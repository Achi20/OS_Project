from socket import socket, AF_INET, SOCK_STREAM, timeout, error
from threading import Thread, current_thread, enumerate
import sys
import time

PORT_S = 2021
PORT_R = 2022
IP = "127.0.0.1"
BUFF_SIZE = 1000
send_addr = (IP, PORT_S)
recv_addr = (IP, PORT_R)

active = True

while active:
    command = input("Please, type a command: ").split()

    if command[0] == "quit" and len(command) == 1:
        print("You have quit.")
        break

    elif command[0] == "connect" and len(command) == 3:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect(send_addr)
            try:
                s.sendto("Hi server.".encode(), send_addr)
            except Exception as e:
                print(e)

        while True:
            command = input("Please, type a command: ").split()

            if len(command) == 1:
                if command[0] == "disconnect":
                    print("Disconnect")
                    break

                elif command[0] == "lu":
                    print("LU")

                elif command[0] == "lf":
                    print("LF")

                elif command[0] == "quit":
                    active = False
                    print("You have quit.")
                    break

                else:
                    print("Something went wrong. Check your command.")

            elif len(command) == 2:
                if command[0] == "read":
                    print("Read")

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