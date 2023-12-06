import socket
import _thread
import sys
import hashlib
import math
import os.path
import time


controller = []
ports = []
servers = []

def sender(data, s, filename):
    numberchunks = math.ceil(len(data) / 65503) + 1
    print("Total chunks:", numberchunks)
    for x in range(numberchunks):
        s.send(f'newfile {filename}'.encode())
        time.sleep(0.05)
        s.send(str(x).encode())
        string = s.recv(1024)
        storep = []
        temp = ""
        for z in range(len(string)):
            if string[z] != '/':
                temp = temp + chr(string[z])
            else:
                storep.append(int(temp))
                temp = ""
        for y in storep:
            v = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            v.connect(('127.0.0.1', y))
            time.sleep(0.03)
            v.send(f"receive: {filename}_chunk{x}".encode())
            time.sleep(0.03)
            v.send(data[x * 65503:(x + 1) * 65503])
            time.sleep(0.03)
            v.send("///end///".encode())
            v.close()

def Main():
    ip = '127.0.0.1'
    port = 8000

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    s.send("client".encode())

    controller.append(s)

    while True:
        query = input("Enter 1 to enter a file, 2 to read a pre-existing file, 3 to write to a pre-existing file, and -1 to exit: ")
        if query == "-1":
            break
        if query == "1":
            data = input("Enter the data: ")
            filename = input("Enter file name: ")
            sender(data, s, filename)
        if query == "2":
            files = []
            s.send("filereq".encode())
            string = s.recv(1024)
            temp = ""
            for x in range(len(string)):
                if string[x] != '/':
                    temp = temp + chr(string[x])
                else:
                    files.append(temp)
                    temp = ""
            print("The files available are: ")
            for x in files:
                print(x)
            while True:
                filename = input("Which file do you want to read? ")
                if filename in files:
                    break
                if filename not in files:
                    raise Exception("No such file")
            s.send(filename.encode())
            chunks = int(s.recv(1024))
            qt = f"There are {chunks} chunks [0-{chunks - 1}]. Which one do you want to read? (Enter -1 for all): "
            q3 = input(qt)
            requests = []
            if q3 == "-1":
                requests = [str(x) for x in range(chunks)]
            else:
                requests.append(q3)
            for x in requests:
                s.send(x.encode())
                portstr = s.recv(1024)
                portsread = [int(temp) for temp in portstr.split('/') if temp]
                for con in range(len(portsread)):
                    v = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    v.connect((ip, portsread[con]))
                    time.sleep(0.02)
                    v.send('read'.encode())
                    chunkname = f"{filename}_chunk{x}"
                    v.send(chunkname.encode())
                    dataread = ""
                    err = 0
                    errstat = v.recv(1024)
                    if errstat == "err":
                        print("Some error.")
                        err = err + 1
                    if err == 0:
                        while True:
                            nstring = v.recv(1024)
                            dataread = dataread + nstring
                            if len(nstring) >= 9:
                                if nstring[len(nstring) - 9:len(nstring)] == "///end///":
                                    dataread = dataread[:len(dataread) - 9]
                                    break
                        print("Chunk", x, "is:", dataread)
                    v.close()
                    if err == 0:
                        break
                    else:
                        print("File was tampered, looking up at another copy.")
                        if err == len(portsread):
                            print("No untampered copy available, sorry.")
            s.send("done".encode())
        if query == "3":
            files = []
            s.send("filereq2".encode())
            string = s.recv(1024)
            temp = ""
            for x in range(len(string)):
                if string[x] != '/':
                    temp = temp + string[x]
                else:
                    files.append(temp)
                    temp = ""
            print("The files available are: ")
            for x in files:
                print(x)
            while True:
                filename = input("Which file do you want to write to? ")
                if filename in files:
                    break
            s.send(filename.encode())
            chunks = int(s.recv(1024))
            qt = f"There are {chunks} chunks [0-{chunks - 1}]. Which one do you want to write to? "
            q3 = input(qt)
            requests = []
            if q3 == "-1":
                requests = [str(x) for x in range(chunks)]
            else:
                requests.append(q3)
            for x in requests:
                chunkname = f"{filename}_chunk{x}"
                s.send('buffer'.encode())
                s.send(chunkname.encode())
                s.recv(1024)
                s.send(x.encode())
                portstr = s.recv(1024)
                portsread = [int(temp) for temp in portstr.split('/') if temp]
                for con in range(len(portsread)):
                    v = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    v.connect((ip, portsread[con]))
                    time.sleep(0.02)
                    v.send('write'.encode())
                    v.send(chunkname.encode())
                    dataread = ""
                    err = 0
                    errstat = v.recv(1024)
                    if errstat == "err":
                        print("Some error.")
                        err = err + 1
                    if err == 0:
                        while True:
                            nstring = v.recv(1024)
                            dataread = dataread + nstring
                            if len(nstring) >= 9:
                                if nstring[len(nstring) - 9:len(nstring)] == "///end///":
                                    dataread = dataread[:len(dataread) - 9]
                                    break
                        print("Chunk", x, "is:", dataread)
                        offset = input("What is the offset that you want to write to? (0-65502 or 0-(max chars-1)): ")
                        txt = input("What do you want to write here? ")
                        v.send(offset.encode())
                        time.sleep(0.05)
                        v.send(txt.encode())
                        time.sleep(0.02)
                        v.send("///end///".encode())
                        nstring = ''
                        while True:
                            nnstring = v.recv(1024)
                            nstring = nstring + nnstring
                            if nnstring[len(nnstring) - 9:len(nnstring)] == "///end///":
                                nstring = nstring[:len(nstring) - 9]
                                break
                    s.send('done'.encode())
                    v.close()
                    if err == 0:
                        print("Edited file is:", nstring)
                        break
                    else:
                        print("File was tampered, looking up at another copy.")
                        if err == len(portsread):
                            print("No untampered copy available, sorry.")

if __name__ == "__main__":
    Main()
