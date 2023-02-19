import logging
import threading
from pprint import pformat
import time

from node_socket import UdpSocket


class Order:
    RETREAT = 0
    ATTACK = 1


class General:

    def __init__(self, my_id: int, is_traitor: bool, my_port: int,
                 ports: list, node_socket: UdpSocket, city_port: int):
        self.ports = ports
        self.my_id = my_id
        self.city_port = city_port
        self.node_socket = node_socket
        self.my_port = my_port
        self.is_traitor = is_traitor

    def start(self):
        """
        :return: None
        """
        orders = []
        logging.info("Start listening for incoming messages...")
        message = self.listen_procedure()
        sender = message[0]
        order = int(message[1][-1])
        logging.info(f"Got incoming message from {sender}: {message}")

        orders.append(order)
        logging.info(f"Append message to a list: {orders}")

        if self.is_traitor:
            if orders[0] == Order.ATTACK:
                self.sending_procedure(sender, Order.RETREAT)
            else:
                self.sending_procedure(sender, Order.ATTACK)
        else:
            self.sending_procedure(sender, orders[0])
        
        message = self.listen_procedure()
        logging.info(f"Got incoming message from {message[0]}: {message}")
        orders.append(int(message[1][-1]))
        self.sending_procedure(message[0], int(message[1][-1]))
        logging.info(f"Append message to a list: {orders}")
        message = self.listen_procedure()
        logging.info(f"Got incoming message from {message[0]}: {message}")
        orders.append(int(message[1][-1]))
        self.sending_procedure(message[0], int(message[1][-1]))
        logging.info(f"Append message to a list: {orders}")

        self.conclude_action(orders)

    def listen_procedure(self):
        """
        :return: list
        """
        while True:
            message = self.node_socket.listen()
            if message:
                return message[0].split('~')

    def sending_procedure(self, sender, order):
        """
        :param sender: sender id
        :param order: order
        :return: str or None
        """
        if sender == "supreme_general":
            logging.info("Send supreme general order to other generals with threading...")  
            logging.info(f"message: general_{self.my_id}~order={order}")
            
            generals = self.ports[1:]
            for i in range(len(generals)):
                if generals[i] != self.my_port:
                    logging.info("Initiate threading to send the message...")
                    thread = threading.Thread(
                        target=self.node_socket.send,
                        args=(f"general_{self.my_id}~order={order}", generals[i])
                    )
                    logging.info("Start threading...")
                    thread.start()
                    logging.info(f"Done sending message to general {i+1}...")
            return f"general_{self.my_id}~order={order}"

    def conclude_action(self, orders):
        """
        :param orders: list
        :return: str or None
        """
        logging.info("Concluding action...")
        if self.is_traitor:
            logging.info("I am a traitor...")
            return None
        
        num_of_attack = 0
        num_of_retreat = 0
        for order in orders:
            if order == Order.ATTACK:
                num_of_attack += 1
            else:
                num_of_retreat += 1
        
        if num_of_attack > num_of_retreat:
            self.node_socket.send(
                f"general_{self.my_id}~action={Order.ATTACK}",
                self.city_port
            )
            logging.info("action: ATTACK")
            logging.info("Done doing my action...")
            return f"general_{self.my_id}~action={Order.ATTACK}"
        else:
            self.node_socket.send(
                f"general_{self.my_id}~action={Order.RETREAT}",
                self.city_port
            )
            logging.info("action: RETREAT")
            logging.info("Done doing my action...")
            return f"general_{self.my_id}~action={Order.RETREAT}"


class SupremeGeneral(General):

    def __init__(self, my_id: int, is_traitor: bool, my_port: int, ports: list, node_socket: UdpSocket, city_port: int,
                 order: Order):
        super().__init__(my_id, is_traitor, my_port, ports, node_socket, city_port)
        self.order = order

    def sending_procedure(self, sender, order):
        """
        :param sender: sender id
        :param order: order
        :return: list
        """
        orders = []
        general_no = 1

        for port in self.ports[1:]:
            if self.is_traitor:
                if general_no % 2 == 1:
                    self.node_socket.send(f"{sender}~order={Order.ATTACK}", port)
                    orders.append(Order.ATTACK)
                else:
                    self.node_socket.send(f"{sender}~order={Order.RETREAT}", port)
                    orders.append(Order.RETREAT)
            else:
                self.node_socket.send(f"{sender}~order={order}", port)
                orders.append(order)
            logging.info(f"Send message to general {general_no} with port {port}")
            general_no += 1
        logging.info("Finish sending message to other generals...")
        return orders

    def start(self):
        """
        :return: None
        """
        logging.info("Supreme general is starting...")
        logging.info("Wait until all generals are running...")
        time.sleep(1)

        orders = self.sending_procedure("supreme_general", self.order)
        self.conclude_action(orders)

    def conclude_action(self, orders):
        """
        :param orders: list
        :return: str or None
        """
        logging.info("Concluding action...")
        if self.is_traitor:
            logging.info("I am a traitor...")
            return None
        if self.order == Order.ATTACK:
            logging.info("ATTACK the city...")
        else:
            logging.info("RETREAT from the city...")
        logging.info("Send information to city...")
        self.node_socket.send(
            f"supreme_general~order={self.order}",
            self.city_port
        )
        logging.info("Done sending information...")
        return f"supreme_general~action={self.order}"


def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def main(is_traitor: bool, node_id: int, ports: list,
         my_port: int = 0, order: Order = Order.RETREAT,
         is_supreme_general: bool = False, city_port: int = 0):
    threading.excepthook = thread_exception_handler
    try:
        if node_id > 0:
            logging.info(f"General {node_id} is running...")
        else:
            logging.info("Supreme general is running...")
        logging.debug(f"is_traitor: {is_traitor}")
        logging.debug(f"ports: {pformat(ports)}")
        logging.debug(f"my_port: {my_port}")
        logging.debug(f"order: {order}")
        logging.debug(f"is_supreme_general: {is_supreme_general}")
        logging.debug(f"city_port: {city_port}")

        if node_id == 0:
            obj = SupremeGeneral(my_id=node_id,
                                 city_port=city_port,
                                 is_traitor=is_traitor,
                                 node_socket=UdpSocket(my_port),
                                 my_port=my_port,
                                 ports=ports, order=order)
        else:
            obj = General(my_id=node_id,
                          city_port=city_port,
                          is_traitor=is_traitor,
                          node_socket=UdpSocket(my_port),
                          my_port=my_port,
                          ports=ports, )
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise
