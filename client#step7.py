from socket import socket, AF_INET, SOCK_STREAM, timeout, error, gethostname, gethostbyname
from threading import Thread, current_thread, Lock
from os.path import isfile, join, getsize
from select import select
from time import sleep
from os import listdir
import sys

PORT_S = 2021
PORT_R = 2022
IP = gethostbyname(gethostname())
# IP = "127.0.0.1"     # required for unix os
recv_addr = (IP, PORT_R)

disc = False            # to check disconnection command output
connection = False
active = True
mes_check = Lock()      # to avoid interfering of the two threads' output


def dataf(s):           # to recover data
    global connection
    data = ""
    while True:
        tmp = s.recv(1)
        tmp = tmp.decode('us-ascii')
        if tmp == "\n": break
        data += tmp
    return data.split()


def mesf(strt, end, command):       # to convert content of append command or message of send command
    mes = ""
    for i in range(strt, end):
        mes += command[i] + ' '
    mes = mes.rstrip()
    if mes[0] == '"':
        mes = mes[1:]
    if mes[-1] == '"':
        mes = mes[:-1]
    return mes


def sizef(s):           # to recover size of files
    size = ""
    while True:
        data = s.recv(1)
        data = data.decode('us-ascii')
        if data == " ":
            break
        size += data
    return size


def readf(s, command, fname, send_addr):                  # to recover read commands
    s.sendto(f"{command.upper()} {fname}\n".encode(), send_addr)
    data = dataf(s)

    if data[0] == "ERROR":
        data.pop(0)
        print(f"{command.capitalize()}ing was rejected.\nCause:", *data)

    if data[0] == "OK":
        size = sizef(s)
        data = s.recv(int(size))
        data = data.decode('us-ascii')

        file = open(fname, 'w')
        file.write(data)
        file.close()


def writef(s, command, fname, send_addr, f, content):               # to send write and append commands
    s.sendto(f"{command.upper()} {fname}\n".encode('us-ascii'), send_addr)
    data = dataf(s)

    if data[0] == "ERROR":
        data.pop(0)
        print(f"{command.capitalize()} command was rejected.\nCause:", *data)

    if data[0] == "OK":
        size = sys.getsizeof(content)
        if f:
            size = getsize(f)
            file = open(f, "r")
            content = file.read(size)
            file.close()

        s.sendto(f"{size} {content}".encode('us-ascii'), send_addr)
        data = dataf(s)

        if data[0] == "ERROR":
            data.pop(0)
            if command != "append":
                print("The server was unable to accept the file.\nCause:", *data)
            else:
                print("The server was unable to accept the content.\nCause:", *data)


def client_s():         # the sending thread
    global active
    global connection
    global disc

    while active:
        command = input("Please, type a command: ").split()
        if not command:         # to avoid errors of wrong outputs
            print("Something went wrong. Check your command.")
            continue

        if command[0] == "quit" and len(command) == 1:
            active = False
            print("\nYou have quit.")
            break

        elif command[0] == "connect" and len(command) == 3:
            s = socket(AF_INET, SOCK_STREAM)
            send_addr = (command[2], PORT_S)

            try:
                s.connect(send_addr)
                s.sendto(f"CONNECT {command[1]}\n".encode('us-ascii'), send_addr)
                data = dataf(s)

            except Exception as e:
                print(e)

            else:
                if data[0] == "ERROR":
                    data.pop(0)
                    print("The connection was rejected.\nCause:", *data)
                elif data[0] == "OK":
                    connection = True

            if connection:
                while True:
                    disc = False
                    mes_check.acquire()
                    command = input("Please, type a command: ").split()
                    mes_check.release()

                    if not connection:
                        break

                    if not command:
                        print("Something went wrong. Check your command.")
                        continue

                    if len(command) == 1:
                        if command[0] == "disconnect":
                            s.sendto("DISCONNECT\n".encode('us-ascii'), send_addr)
                            data = dataf(s)
                            if data[0] == "ERROR":
                                data.pop(0)
                                print("The disconnection was rejected.\nCause:", *data)
                            elif data[0] == "OK":
                                disc = True
                                print("\nYou have been disconnected.\n")
                                break

                        elif command[0] == "lu":
                            s.sendto("LU\n".encode('us-ascii'), send_addr)
                            data = dataf(s)
                            print("Users:", *data)

                        elif command[0] == "lf":
                            s.sendto("LF\n".encode('us-ascii'), send_addr)
                            data = dataf(s)
                            print("Files:", *data)

                        elif command[0] == "quit":
                            disc = True
                            active = False
                            s.sendto("DISCONNECT\n".encode('us-ascii'), send_addr)
                            print("\nYou have quit.")
                            break

                        else:
                            print("Something went wrong. Check your command.")

                    elif len(command) == 2 or command[0] == "appendfile":
                        c = False
                        onlyfiles = [f for f in listdir() if isfile(join(f))]
                        for f in onlyfiles:            # to check if the file exists
                            if f.endswith(command[1]):
                                c = True
                                break

                        if command[0] == "read":
                            if c:
                                print("ERROR: You already have that file.")
                                continue

                            readf(s, command[0], command[1], send_addr)

                        elif command[0] == "write" or command[0] == "overwrite":
                            if c:
                                writef(s, command[0], command[1], send_addr, f, 0)
                                continue

                            print("ERROR The file doesn't exist.")

                        elif command[0] == "overread":
                            readf(s, command[0], command[1], send_addr)

                        elif command[0] == "appendfile" and len(command) == 3:
                            if c:
                                writef(s, command[0], command[2], send_addr, f, 0)
                                continue

                            print("ERROR The local file doesn't exist.")

                        else:
                            print("Something went wrong. Check your command.")

                    elif command[0] == "send" and len(command) >= 3:
                        mes = mesf(2, len(command), command)
                        size = sys.getsizeof(mes)

                        s.sendto(f"{command[0].upper()} {command[1]}\n{size} {mes}".encode('us-ascii'), send_addr)
                        data = dataf(s)

                        if data[0] == "ERROR":
                            data.pop(0)
                            print(f"{command[0].capitalize()}ing was rejected.\nCause:", *data)

                    elif command[0] == "append" and len(command) >= 3:
                        content = mesf(1, len(command)-1, command)
                        writef(s, command[0], command[-1], send_addr, False, content)

                    else:
                        print("Something went wrong. Check your command.")

        elif command[0] != "connect":
            print("Before using this command connect to the server.")

        else:
            print("Something went wrong. Check your command.")


def client_r():         # the receiving thread
    global active
    global connection
    global disc

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
                            data = dataf(conn)

                            if data[0] == "DISCONNECT":
                                # sleep(1)     # required for unix os
                                if not disc:
                                    print("\n\nServer has been graceful terminated.\nPush Enter to continue.")
                                connection = False
                                break

                            elif data[0] == "MESSAGE":
                                size = sizef(conn)
                                data = conn.recv(int(size))
                                data = data.decode()

                                mes_check.acquire()
                                print(f"New message: {data}")
                                mes_check.release()

                            else:
                                print(data)

                    except timeout:
                        continue

                    except Exception:
                        connection = False
                        print("\n\nServer has been ungraceful terminated.\nPush Enter to continue.")
                        break


t1 = Thread(target=client_s)
t1.start()
t2 = Thread(target=client_r)
t2.start()
