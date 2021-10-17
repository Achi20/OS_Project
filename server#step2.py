from socket import socket, AF_INET, SOCK_STREAM, timeout
from threading import Thread, current_thread, enumerate
import time

PORT_S = 2022
PORT_R = 2021
IP = "127.0.0.1"
BUFF_SIZE = 1000
full_addr = (IP, PORT_R)

def client_handler(conn, addr):
    while True:
        data = conn.recv(BUFF_SIZE)
        if data:
            print(f"Connected {current_thread().name} received from {addr}: {data.decode()}")

with socket(AF_INET, SOCK_STREAM) as s:
    s.bind(full_addr)
    s.listen()
    s.settimeout(1.0)
    try:
        while True:
            try:
                conn, addr = s.accept()
            except timeout:
                continue
            except Exception as e:
                print(e)
                break
            else:
                t = Thread(target=client_handler, args=(conn, addr))
                t.start()
    except KeyboardInterrupt:
        print("User has quit.")
