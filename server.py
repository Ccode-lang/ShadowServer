from socket import *
import threading


# UDP socket info
sockudp = socket(AF_INET, SOCK_DGRAM)
sockudp.settimeout(1)
sockudp.bind(("0.0.0.0", 4504))

# TCP sock info
socktcp = socket(AF_INET, SOCK_STREAM)
socktcp.settimeout(1)
socktcp.bind(("0.0.0.0", 4504))

clientIDs = []

# Transforms
clientspos = {}

# is said client connected?
client_connected = {}

# Connected TCP clients tuples. (socket, id)
TCP_clients = []

idcounter = 0



# Transform represented in strings. I never need the numbers on the server so it doesn't matter if I convert them
class Transform(object):
    def __init__(self, x, y, z, rx, ry, rz):
        self.x = x
        self.y = y
        self.z = z

        self.rx = rx
        self.ry = ry
        self.rz = rz
    def serialize(self):
        return f"{self.x}:{self.y}:{self.z}:{self.rx}:{self.ry}:{self.rz}"



import traceback

def incoming_udp_thread():
    global clientIDs
    global clientspos


    while True:
        try:
            message, client_address = sockudp.recvfrom(256)
        except:
            continue

        message = message.decode()
        print(message)
        msp = message.split(":")

        if msp[0] == "POSUPDT":
            # Server command code: POSUPDT:X:Y:Z:RX:RY:RZ:ID
            print("Got position update")
            clientspos[int(msp[7])] = Transform(msp[1], msp[2], msp[3], msp[4], msp[5], msp[6])
        elif msp[0] == "POSREQ":
            print(clientspos)
            # Client command code: POSUPDTCL;ID:X:Y:Z:RX:RY:RZ;(repeat as many times as needed)
            clmessage = "POSUPDTCL"
            for client in clientIDs:
                if client_connected[client]:
                    clmessage += ";" + str(client) + ":" + clientspos[client].serialize()
            print(clmessage)
            sockudp.sendto(clmessage.encode(), client_address)

def incoming_tcp_thread():
    global idcounter
    global TCP_clients
    global clientIDs
    socktcp.listen()
    while True:
        try:
            connection, client_address = socktcp.accept()
        except:
            #traceback.print_exc()
            continue

        print("Got new client")
    
     
        client_connected[idcounter] = True
        clientspos[idcounter] = Transform(0, 0, 0, 0, 0, 0)

        thread = threading.Thread(target=user_tcp_thread, args=[connection, idcounter])
        thread.daemon = True
        thread.start()
        clientIDs += [idcounter]

        TCP_clients += [(connection, idcounter)]

        idcounter += 1

def user_tcp_thread(conn: socket, id: int):
    # TCP Client Command code: CLIENTID;ID
    conn.sendall(f"CLIENTID;{id}".encode())

    while True:
        data = conn.recv(1024).decode()

        spldata = data.split(":")

        if data == "DISCONN":
            print("Got client disconnect")
            client_connected[id] = False
            conn.close()
            for client in TCP_clients:
                if client[1] == id:
                    TCP_clients.remove(client)
                    break
            for id1 in clientIDs:
                if id1 == id:
                    clientIDs.remove(id)
                    break
            for id1 in clientspos.keys():
                if id1 == id:
                    del clientspos[id]
                    break
            send_disconnect(id)
            break
        elif spldata[0] == "CHAT":
            send_chat(data.split(":", 1)[1])


dislock = threading.Lock()
def send_disconnect(id: int):
    with dislock:
        for client in TCP_clients:
            client[0].sendall(f"DISCONNCL;{id}".encode())

chatlock = threading.Lock()
def send_chat(chmessage: str):
    with chatlock:
        for client in TCP_clients:
            client[0].sendall(f"CHATCL;{chmessage}".encode())





tcpThread = threading.Thread(target=incoming_tcp_thread)
tcpThread.daemon = True
tcpThread.start()

try:
    incoming_udp_thread()
except KeyboardInterrupt:
    # Quit gracefully
    pass

sockudp.close()
socktcp.close()
runThread = False