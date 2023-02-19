import logging
import threading

from node_socket import UdpSocket


class City:

    def __init__(self, my_port: int, number_general: int) -> None:
        self.number_general = number_general
        self.my_port = my_port
        self.node_socket = UdpSocket(my_port)

    def start(self):
        """
        :return: string
        """
        num_of_attacks = 0
        num_of_retreat = 0
        logging.info("Listen to incoming messages...")
        while True:
            message = self.node_socket.listen()
            if message:
                general, action = message[0].split('~')
                action = int(action[-1])
                if action == 0:
                    logging.info(f"{general} RETREAT from us!")
                    num_of_retreat += 1
                else:
                    logging.info(f"{general} ATTACK us!")
                    num_of_attacks += 1
            if (num_of_attacks + num_of_retreat) == self.number_general:
                break
        logging.info("Concluding what happen...")

        if self.number_general < 2:
            logging.info("GENERAL CONSENSUS: ERROR_LESS_THAN_TWO_GENERALS")
            return "ERROR_LESS_THAN_TWO_GENERALS"

        if num_of_attacks > num_of_retreat:
            logging.info("GENERAL CONSENSUS: ATTACK")
            return "ATTACK"
        elif num_of_attacks < num_of_retreat:
            logging.info("GENERAL CONSENSUS: RETREAT")
            return "RETREAT"
        else:
            logging.info("GENERAL CONSENSUS: FAILED")
            return "FAILED"


def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def main(city_port: int, number_general: int):
    threading.excepthook = thread_exception_handler
    try:
        logging.debug(f"city_port: {city_port}")
        logging.info(f"City is running...")
        logging.info(f"Number of loyal general: {number_general}")
        city = City(my_port=city_port, number_general=number_general)
        return city.start()

    except Exception:
        logging.exception("Caught Error")
        raise
