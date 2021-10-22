from socket import socket, AF_INET, SOCK_STREAM, timeout, error
from threading import Thread, current_thread, enumerate
from os import listdir
from os.path import isfile, join
import sys
import time

PORT_S = 2021
PORT_R = 2022
IP = "127.0.0.1"
BUFF_SIZE = 1000
recv_addr = (IP, PORT_R)

connection = False
active = True

def client_s():
    global active
    global connection

    while active:
        command = input("Please, type a command: ").split()

        if command[0] == "quit" and len(command) == 1:
            active = False
            print("You have quit.")
            break

        elif command[0] == "connect" and len(command) == 3:
            send_addr = (command[2], PORT_S)
            s = socket(AF_INET, SOCK_STREAM)
            s.connect(send_addr)

            try:
                s.sendto(f"{command[1]}".encode(), send_addr)
                data = s.recv(BUFF_SIZE)

            except Exception as e:
                print(e)

            else:
                data = data.decode().split()
                if data[0] == "ERROR":
                    data.pop(0)
                    print("The connection was rejected.\nCause:", *data)

                elif data[0] == "OK":
                    connection = True

            if connection:
                while True:
                    command = input("Please, type a command: ").split()

                    if len(command) == 1:
                        if command[0] == "disconnect":
                            s.sendto("DISCONNECT".encode(), send_addr)
                            data = s.recv(BUFF_SIZE)
                            data = data.decode().split()

                            if data[0] == "ERROR":
                                data.pop(0)
                                print("The disconnection was rejected.\nCause:", *data)

                            elif data[0] == "OK":
                                break

                        elif command[0] == "lu":
                            lu = []
                            s.sendto("LU".encode(), send_addr)

                            while True:
                                data = s.recv(BUFF_SIZE)
                                data = data.decode()
                                if data == "\n": break
                                lu.append(data)

                            print("Users:", *lu)

                        elif command[0] == "lf":
                            lf = []
                            s.sendto("LF".encode(), send_addr)

                            while True:
                                data = s.recv(BUFF_SIZE)
                                data = data.decode()
                                if data == "\n": break
                                lf.append(data)

                            print("Files:", *lf)

                        elif command[0] == "quit":
                            active = False
                            s.sendto("DISCONNECT".encode(), send_addr)
                            print("You have quit.")
                            break

                        else:
                            print("Something went wrong. Check your command.")

                    elif len(command) == 2:
                        if command[0] == "read":
                            c = False
                            err = ""
                            num = 0
                            for i in command[1]:
                                num += 1
                                if num == 1: continue
                                err += i
                            onlyfiles = [f for f in listdir() if isfile(join(f))]
                            for f in onlyfiles:
                                if f.endswith(err):
                                    c = True
                                    print("ERROR: You already have that file.")
                                    break
                            if c: continue
                            file = open(command[1], 'w')
                            s.sendto(f"READ {err}".encode(), send_addr)
                            data = s.recv(BUFF_SIZE)
                            data = data.decode().split()
                            if data[0] == "ERROR":
                                data.pop(0)
                                print("Reading was rejected.\nCause:", *data)
                            elif data[0] == "OK":
                                size = ""
                                while True:
                                    data = s.recv(1)
                                    data = data.decode()
                                    if data == " ":
                                        break
                                    size += data[0]
                                data = s.recv(int(size))
                                data = data.decode()
                                file.write(data)

                        elif command[0] == "write":
                            print("Write")

                        elif command[0] == "overread":
                            print("Overread")

                        elif command[0] == "overwrite":
                            print("Overwrite")

                        else:
                            print("Something went wrong. Check your command.")

                    elif command[0] == "appendfile" and len(command) == 3:
                        print(f"Appendfile")

                    elif command[0] == "send" and len(command) >= 3:
                        mes = ""

                        for i in range(2, len(command)):
                            mes += command[i] + ' '
                        mes = mes.rstrip()
                        if mes[0] == '"':
                            mes = mes[1:]
                        if mes[-1] == '"':
                            mes = mes[:-1]

                        print(f"Message to {command[1]}\n{mes}")

                    elif command[0] == "append" and len(command) >= 3:
                        print("Append")

                    else:
                        print("Something went wrong. Check your command.")

        elif command[0] != "connect":
            print("Before using this command connect to the server.")

        else:
            print("Something went wrong. Check your command.")

def client_r():
    global active
    global connection

    while active:
        if connection:
            with socket(AF_INET, SOCK_STREAM) as r:
                r.bind(recv_addr)
                r.listen()
                r.settimeout(1.0)

                while connection:
                    try:
                        conn, addr = r.accept()
                        while True:
                            data = conn.recv(BUFF_SIZE)
                            data = data.decode()

                            if data == "DISCONNECT":
                                print("\nYou have been disconnected.")
                                connection = False
                                break

                    except timeout:
                        continue

                    except Exception as e:
                        print(e)
                        break

t1 = Thread(target=client_s)
t1.start()
t2 = Thread(target=client_r)
t2.start()