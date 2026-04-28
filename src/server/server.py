import socket
from dotenv import load_dotenv
import os
import logging
import threading
import pickle
import sys
import random

def main():
    load_dotenv()
    
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        level=logging.DEBUG,
    )

    ip = os.getenv("SERVER_IP")
    port = int(os.getenv("PORT"))

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((ip, port))

            server.listen(0)
            logging.info(f"Listening at {ip}:{port}")

            while True:
                c_socket, c_addr = server.accept()
                logging.info(f"Accepted connection from {c_addr[0]}:{c_addr[1]}")
                thread = threading.Thread(target=handle_client, args=(c_socket, c_addr,))
                thread.start()

    except Exception as e:
        logging.critical(f"Exception occurred: {e}")

def handle_client(c_socket, c_addr):
    try:
        while True:
            request = c_socket.recv(1024).decode("utf-8")
            if request:
                logging.info(f"Received: {request}")

                if request == "QUERY_ROOMS":
                    c_socket.send(pickle.dumps(["1. Bob", "2. Jim"]))
                if request.split(":")[0] == "JOIN":
                    
                    if random(0, 1) == 0:
                        message = "JOINED:START"
                    else:
                        message = "JOINED:DONT_START"
                    c_socket.send(f"{message}".encode("utf-8"))

    except Exception as e:
        logging.critical(f"Error when handling client: {e}")


if __name__ == "__main__":
    main()