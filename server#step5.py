from socket import socket, AF_INET, SOCK_STREAM, timeout
from threading import Thread, current_thread, enumerate
from os import listdir
from os.path import isfile, join, getsize
import time
import sys

PORT_S = 2022
PORT_R = 2021
IP = "127.0.0.1"
BUFF_SIZE = 1000
recv_addr = (IP, PORT_R)
threads = []

def client_handler(conn, addr, s):
    while True:
        data = conn.recv(BUFF_SIZE)
        data = data.decode().split()

        if data:
            if data[0] == "DISCONNECT":
                try:
                    conn.send("OK".encode())

                except Exception as e:
                    conn.send(f"ERROR {str(e)}".encode())
                    print(e)

                else:
                    s.sendto("DISCONNECT".encode(), send_addr)
                    threads.remove(current_thread().name)
                    print(f"Connected {current_thread().name} received from {addr}: {data}\n{enumerate()}")
                    break

            elif data[0] == "LF":
                onlyfiles = [f for f in listdir() if isfile(join(f))]
                onlyfiles.append("\n")

                for i in onlyfiles:
                    conn.send(i.encode())
                    time.sleep(0.01)

                print("List of files has been sent.")

            elif data[0] == "LU":
                lthreads = [i for i in threads]
                lthreads.append("\n")

                for i in lthreads:
                    conn.send(i.encode())
                    time.sleep(0.01)

                print("List of users has been sent.")

            elif data[0] == "READ":
                onlyfiles = [f for f in listdir() if isfile(join(f))]
                c = False

                for f in onlyfiles:
                    if f.endswith(data[1]):
                        c = True

                        try:
                            conn.send("OK".encode())

                        except Exception as e:
                            conn.send(f"ERROR {str(e)}".encode())
                            print(e)

                        else:
                            size = getsize(f)
                            file = open(f, "r")
                            l = file.read(size)
                            print(size)
                            conn.send(f"{size} {l}".encode())
                            break

                if c: continue

                else:
                    conn.send("ERROR The file doesn't exist.".encode())

with socket(AF_INET, SOCK_STREAM) as r:
    r.bind(recv_addr)
    r.listen()
    r.settimeout(1.0)

    try:
        while True:
            try:
                conn, addr = r.accept()
                data = conn.recv(BUFF_SIZE)
                data = data.decode()

            except timeout:
                continue

            except Exception as e:
                conn.send(f"ERROR {str(e)}".encode())
                print(e)
                break

            else:
                if data in threads:
                    conn.send("ERROR The User already exists.".encode())
                    break

                conn.send("OK".encode())
                threads.append(data)

                send_addr = (addr[0], PORT_S)
                s = socket(AF_INET, SOCK_STREAM)
                s.connect(send_addr)

                t = Thread(target=client_handler, args=(conn, addr, s), name=data)
                t.start()
    except KeyboardInterrupt:
        print("User has quit.")