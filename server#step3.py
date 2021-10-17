from socket import socket, AF_INET, SOCK_STREAM, timeout
from threading import Thread, current_thread, enumerate
import time

PORT_S = 2022
PORT_R = 2021
IP = "127.0.0.1"
BUFF_SIZE = 1000
send_addr = (IP, PORT_S)
recv_addr = (IP, PORT_R)

def client_handler(conn, addr):
    while True:
        data = conn.recv(BUFF_SIZE)
        if data:
            print(f"Connected {current_thread().name} received from {addr}: {data.decode()}")

with socket(AF_INET, SOCK_STREAM) as r:
    r.bind(recv_addr)
    r.listen()
    r.settimeout(1.0)
    try:
        while True:
            try:
                conn, addr = r.accept()
                data = conn.recv(BUFF_SIZE)
            except timeout:
                continue
            except Exception as e:
                print(e)
                break
            else:
                #conn.send("OK".encode())
                with socket(AF_INET, SOCK_STREAM) as s:
                    s.connect(send_addr)
                    s.sendto("Hi from server.".encode(), send_addr)
                t = Thread(target=client_handler, args=(conn, addr), name=data.decode())
                t.start()
    except KeyboardInterrupt:
        print("User has quit.")
