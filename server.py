import socket
import _thread
import sys
import hashlib
import math
import os.path
import uu
import time
import threading

clientslist = []
serverslist = []
controller = []
files = []
filesdict = {}
string = ""
port = 0
system = 0

def requester(reqport, filename):
    sn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sn.connect(('127.0.0.1', reqport))
    with open(filename, 'r') as f:
        data = f.read()
    time.sleep(0.05)
    sn.send(f"receive: {filename}".encode())
    time.sleep(0.1)
    sn.send(data)
    time.sleep(0.1)
    sn.send('///end///'.encode())
    sn.close()

def changehamsai(data, filename):
    sn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sn.connect(('127.0.0.1', 8000))
    sn.send("haha".encode())
    time.sleep(0.2)
    msg = f"hamsai: {filename}"
    sn.send(msg.encode())
    time.sleep(0.07)
    msg = str(port)
    time.sleep(0.07)
    sn.send(msg.encode())
    portstr = sn.recv(1024)
    temp = ""
    portarr = []
    for i in range(len(portstr)):
        if portstr[i] == "/":
            portarr.append(int(temp))
            temp = ""
        else:
            temp = temp + portstr[i]
    for i in portarr:
        v = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        v.connect(('127.0.0.1', i))
        v.send(f"receive: {filename}".encode())
        time.sleep(0.1)
        v.send(data.encode())
        time.sleep(0.1)
        v.send('///end///'.encode())
        v.close()
    sn.close()

def initwriter(filename, init):
    if not os.path.isfile(filename):
        with open(filename, 'w') as f:
            f.write(" ")
    with open(filename, 'r') as f:
        data = f.read()
    data = init + data
    if len(data) > 65503:
        extra = data[65503:]
        data = data[:65503]
        initfile = filename[:filename.rfind('_')]
        chunkid = filename[filename.rfind('k') + 1:]
        controller[0].send("cascade".encode())
        time.sleep(0.15)
        controller[0].send(initfile)
        time.sleep(0.15)
        controller[0].send(chunkid)
        nport = int(controller[0].recv(1024))
        v = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        v.connect(('127.0.0.1', nport))
        time.sleep(0.15)
        newfname = f"{initfile}_chunk{int(chunkid)+1}"
        newmsg = f"initwrite: {newfname}"
        v.send(newmsg)
        time.sleep(0.15)
        v.send(extra)
        time.sleep(0.15)
        v.send('///end///')
        v.close()
    with open(filename, 'w') as f:
        f.write(data)
    filesdict[filename] = hasher(data)
    changehamsai(data, filename)

def writer(filename, client):
    with open(filename, 'r') as f:
        data = f.read()
    if hasher(data) == filesdict[filename]:
        client.send('ok')
        time.sleep(0.05)
        client.send(data)
        time.sleep(0.05)
        client.send('///end///')
        offset = int(client.recv(1024))
        txt = ""
        while True:
            nstring = client.recv(1024)
            txt = txt + nstring
            if len(nstring) >= 9:
                if nstring[len(nstring) - 9:len(nstring)] == "///end///" or nstring == "///end///":
                    txt = txt[:len(txt) - 9]
                    break
        data = data[:offset] + txt + data[offset:]
        if len(data) > 65503:
            extra = data[65503:]
            data = data[:65503]
            initfile = filename[:filename.rfind('_')]
            chunkid = filename[filename.rfind('k') + 1:]
            controller[0].send("cascade")
            time.sleep(0.15)
            controller[0].send(initfile)
            time.sleep(0.15)
            controller[0].send(chunkid)
            nport = int(controller[0].recv(1024))
            v = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            v.connect(('127.0.0.1', nport))
            time.sleep(0.02)
            newfname = f"{initfile}_chunk{int(chunkid)+1}"
            newmsg = f"initwrite: {newfname}"
            v.send(newmsg)
            time.sleep(0.02)
            v.send(extra)
            time.sleep(0.02)
            v.send('///end///')
        with open(filename, 'w') as f:
            f.write(data)
        filesdict[filename] = hasher(data)
        changehamsai(data, filename)
        client.send(data)
        time.sleep(0.02)
        client.send('///end///')
    else:
        client.send('err')

def integritychecker():
    global files
    global filesdict
    global system
    while True:
        checker = 0
        time.sleep(15)
        if sys == 1:
            continue
        for q in files:
            with open(q, 'r') as f:
                data = f.read()
            x = 0
            hashint = 0
            while True:
                if (x - 1) * 8192 > len(data):
                    break
                sha1 = hashlib.sha1()
                s = data[x * 8192:(x + 1) * 8192]
                sha1.update(s)
                hashint = hashint + int(sha1.hexdigest(), 16)
                x = x + 1
            if sys == 1:
                continue
            if hashint == filesdict[q]:
                checker = checker
            else:
                print(f"CORRUPTION: Checksum failed for {q}")
                checker = 1
        if checker == 0:
            print("Checksum done")

def hasher(data):
    x = 0
    hashstr = 0
    while True:
        if (x - 1) * 8192 > len(data):
            break
        sha1 = hashlib.sha1()
        s = data[x * 8192:(x + 1) * 8192]
        sha1.update(s)
        hashstr = hashstr + int(sha1.hexdigest(), 16)
        x = x + 1
    return hashstr

def sender(filename, s):
    with open(filename, 'r') as f:
        data = f.read()
    hashstr = hasher(data)
    if hashstr == filesdict[filename]:
        s.send("ok")
        time.sleep(0.02)
        s.send(data)
        time.sleep(0.02)
        s.send('///end///')
    else:
        s.send("err")
        msg = f"writereq: {filename}/{port}"
        controller[0].send(msg)

def getchunk(filename, cont):
    sys = 1
    global string
    data = ""
    while True:
        string = cont.recv(1024)
        if len(string) >= 9:
            if string[len(string) - 9:len(string)] == "///end///":
                data = data + string[:len(string) - 9]
                break
        data = data + string
    with open(filename, 'w') as file:
        file.write(data)
    print(f"{filename} written")
    x = 0
    hashstr = 0
    while True:
        if (x - 1) * 8192 > len(data):
            break
        sha1 = hashlib.sha1()
        s = data[x * 8192:(x + 1) * 8192]
        sha1.update(s)
        hashstr = hashstr + int(sha1.hexdigest(), 16)
        x = x + 1
    if filename not in files:
        files.append(filename)
    filesdict[filename] = hashstr
    sys = 0

def listenerthread(client):
    while True:
        string = client.recv(1024)
        print(f"Client said: {string}")
        if string[:10] == "initwrite:":
            filename = string[11:]
            data = ""
            while True:
                string = client.recv(1024)
                if len(string) >= 9:
                    if string[len(string) - 9:len(string)] == "///end///":
                        data = data + string[:len(string) - 9]
                        break
                data = data + string
            initwriter(filename, data)
        if string == '':
            client.close()
            break
        if string == 'write':
            nstring = client.recv(1024)
            writer(nstring, client)
        if string == 'read':
            nstring = client.recv(1024)
            sender(nstring, client)
        if string[:8] == "receive:":
            getchunk(string[9:], client)
        if string[:9] == "writereq:":
            for x in range(len(string) - 1, 0, -1):
                if string[x] == '/':
                    reqport = int(string[x + 1:])
                    filename = string[10:x]
            requester(reqport, filename)

def clienter(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen(10)
    while True:
        client, addr = s.accept()
        threading.Thread(target=listenerthread, args=(client,)).start()

def listener(cont):
    global port
    while True:
        try:
            string = cont.recv(1024)
            print(f"Controller said: {string}")
            if string[:5] == "port:":
                port = int(string[6:])
                print(f"port: {port}")
                threading.Thread(target=clienter, args=('127.0.0.1', port)).start()
                break
        except socket.error as msg:
            print("Controller disconnected.")
            break

def Main():
    ip = '127.0.0.1'
    port = 8000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    s.send("server".encode())
    controller.append(s)
    threading.Thread(target=integritychecker).start()
    threading.Thread(target=listener, args=(s,)).start()
    while True:
        y = 0

if __name__ == "__main__":
    Main()
