from socket import socket, AF_INET, SOCK_STREAM, timeout, gethostname, gethostbyname
from threading import Thread, current_thread, Lock
from os.path import isfile, join, getsize
from signal import signal, SIGINT
from select import select
from time import sleep
from os import listdir
import sys

PORT_S = 2022
PORT_R = 2021
IP = gethostbyname(gethostname())
# IP = "127.0.0.1"      # required for unix os
recv_addr = (IP, PORT_R)
threads = []            # to collect threads' names
files = []              # to collect changing files' names
gnrl_file_check = Lock()          # to avoid race condition during commands
mes_check = Lock()           # to avoid race condition during send command
spcfc_file_check = Lock()          # to avoid race condition during specific write commands

def sigint_handler(sig, frame):
    global count
    print(f"The server intercepted the SIGINT signal.\n"
          f"All existing connections are being terminated gracefully "
          f"and the server will be terminated after them.")
    count = 0
    sys.exit(0)


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


def dataf(conn, s):      # to recover data and to check sigint and send commands' flag
    global mes
    global new_mes
    data = ""

    while True:
        ready = select([conn], [], [], 0.1)
        if ready[0]:
            tmp = conn.recv(1)
            tmp = tmp.decode('us-ascii')
            if tmp == "\n": break
            data += tmp

        if count == 0:
            s.send("DISCONNECT\n".encode('us-ascii'))
            s.close()
            break

        mes_check.acquire()
        if new_mes:
            if mes.split()[0] == current_thread().name:
                tmp = mes.split()
                size = tmp[1]
                data = mesf(2, len(tmp), tmp)
                s.send(f"MESSAGE\n{size} {data}".encode('us-ascii'))

                data = ""
                mes = ""
                new_mes = False
        mes_check.release()

    return data.split()


def sizef(conn):        # to recover size of files
    size = ""
    while True:
        data = conn.recv(1)
        data = data.decode('us-ascii')
        if data == " ":
            break
        size += data
    return size


def writef(conn, fname, app):       # to recover write and append commands
    conn.send("OK\n".encode('us-ascii'))

    size = sizef(conn)
    data = conn.recv(int(size))

    mode = 'wb'
    if app == 1:
        mode = 'ab'
        data = data.encode()
        data = mesf(0, len(data.split()), data.split())
        data = "\n" + data
        data = data.decode()
    if app == 2:
        mode = 'ab'

    gnrl_file_check.acquire()
    if fname in files:
        gnrl_file_check.release()
        spcfc_file_check.acquire()
        while fname in files:
            continue
        files.append(fname)
        spcfc_file_check.release()
    else:
        files.append(fname)
        gnrl_file_check.release()

    file = open(fname, mode)
    file.write(data)
    file.close()

    files.remove(fname)

    conn.send("OK\n".encode('us-ascii'))


def readf(conn, fname):         # to send read commands
    conn.send("OK\n".encode('us-ascii'))
    size = getsize(fname)

    gnrl_file_check.acquire()

    file = open(fname, "rb")
    data = file.read(size)
    file.close()

    gnrl_file_check.release()
    
    conn.send(f"{size} ".encode('us-ascii', 'replace'))
    conn.send(data)


def client_handler(conn, s):         # the thread for each client
    global count
    global mes
    global new_mes
    while True:
        try:
            data = dataf(conn, s)

        except Exception as e:
            print(f"{current_thread().name}: {e}")
            count -= 1
            s.close()
            threads.remove(current_thread().name)
            break

        else:
            if data:
                c = False
                onlyfiles = [f for f in listdir() if isfile(join(f))]
                if len(data) > 1:
                    for f in onlyfiles:           # to check if the file exists
                        if f.endswith(data[1]):
                            c = True
                            break

                if data[0] == "DISCONNECT":
                    try:
                        conn.send("OK\n".encode('us-ascii'))

                    except Exception as e:
                        conn.send(f"ERROR\n".encode('us-ascii'))
                        print(e)

                    else:
                        s.send("DISCONNECT\n".encode('us-ascii'))
                        s.close()
                        print(f"{current_thread().name} has disconnected.")
                        threads.remove(current_thread().name)
                        count -= 1
                        break

                elif data[0] == "LF":
                    conn.send(f"{onlyfiles}\n".encode('us-ascii'))
                    print("List of files has been sent.")

                elif data[0] == "LU":
                    lthreads = [i for i in threads]
                    conn.send(f"{lthreads}\n".encode('us-ascii'))
                    print("List of users has been sent.")

                elif data[0] == "READ" or data[0] == "OVERREAD":
                    if c:
                        readf(conn, f)
                        continue

                    conn.send("ERROR\n".encode('us-ascii'))
                    print("The file doesn't exist.")

                elif data[0] == "WRITE":
                    if c:
                        conn.send("ERROR\n".encode('us-ascii'))
                        print("The file already exists.")
                        continue

                    writef(conn, data[1], False)

                elif data[0] == "OVERWRITE":
                    writef(conn, data[1], False)

                elif data[0] == "APPENDFILE":
                    if c:
                        writef(conn, data[1], 2)
                        continue

                    conn.send("ERROR\n".encode('us-ascii'))
                    print("The file doesn't exist.")

                elif data[0] == "MESSAGE":
                    if data[1] not in threads:
                        conn.send("ERROR\n".encode('us-ascii'))
                        size = sizef(conn)
                        data = conn.recv(int(size))         # to clean up the recover
                        print("The User doesn't exist.")
                        continue
                    conn.send("OK\n".encode('us-ascii'))
                    tmp = data[1]

                    size = sizef(conn)
                    data = conn.recv(int(size))
                    data = data.decode()

                    mes = f"{tmp} {size} {data}"
                    new_mes = True

                elif data[0] == "APPEND":
                    if c:
                        writef(conn, data[1], 1)
                        continue

                    conn.send("ERROR\n".encode('us-ascii'))
                    print("The file doesn't exist.")

                else: print(f"Something went wrong.\nFrom client: {data}")
            else:
                break


signal(SIGINT, sigint_handler)
with socket(AF_INET, SOCK_STREAM) as r:
    r.bind(recv_addr)
    r.listen()
    r.settimeout(1.0)
    count = 0        # to check sigint flag
    mes = ""         # to send a message between threads
    new_mes = False  # to check send command flag

    while True:
        try:
            conn, addr = r.accept()
            count += 1
            data = dataf(conn, False, False)

        except timeout:
            continue

        except Exception as e:
            conn.send(f"ERROR\n".encode('us-ascii'))
            count -= 1
            print(e)
            break

        else:
            if data[0] != "CONNECT":
                conn.send("ERROR\n".encode('us-ascii'))
                print("CONNECT command should be the first one of the connection.")
                continue
            if data[1] in threads:
                conn.send("ERROR\n".encode('us-ascii'))
                count -= 1
                print("The User already exists.")
                continue

            conn.send("OK\n".encode('us-ascii'))
            threads.append(data[1])

            send_addr = (addr[0], PORT_S)
            # sleep(3)    # required for unix os
            s = socket(AF_INET, SOCK_STREAM)
            s.connect(send_addr)

            t = Thread(target=client_handler, args=(conn, s), name=data[1])
            t.start()
