from socket import *
import threading

sock = socket(AF_INET, SOCK_DGRAM)
sock.settimeout(1)
sock.bind(("127.0.0.1", 4504))

# Addr for client contact
#clients = []

clientIDs = []

# Vector3s
clientspos = []

idcounter = 0



# Vector3 represented in strings. I never need the numbers on the server so it doesn't matter if I convert them
class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def serialize(self):
        return f"{self.x}:{self.y}:{self.z}"



import traceback

def incoming_thread():
    #global clients
    global clientIDs
    global idcounter
    global clientspos


    while True:
        try:
            message, client_address = sock.recvfrom(256)
        except:
            continue

        message = message.decode()
        msp = message.split(":")

        if msp[0] == "POSUPDT":
            # Server command code: POSUPDT:X:Y:Z:ID
            print("Got position update")
            print(message)

            if msp[4] == "NA":
                print("Got new client")
                #clients += [client_address[0]]
                clientIDs += [idcounter]
                msp[4] = str(idcounter)
                idcounter += 1
                sock.sendto(f"CLIENTID;{msp[4]}".encode(), client_address)
            else:
                sock.sendto("FILLER".encode(), client_address)

            #sock.sendto(f"CLIENTID;{msp[4]}".encode(), client_address)
            if not int(msp[4]) < len(clientspos):
                clientspos += [Vector3(msp[1], msp[2], msp[3])]
            else:
                clientspos[int(msp[4])] = Vector3(msp[1], msp[2], msp[3])
        elif msp[0] == "POSREQ":
            print(clientspos)
            # Client command code: POSUPDTCL;ID:X:Y:Z;(repeat as many times as needed)
            clmessage = "POSUPDTCL"
            for client in clientIDs:
                #try:
                clmessage += ";" + str(client) + ":" + clientspos[client].serialize()
                #except:
                #    pass
            print(clmessage)
            sock.sendto(clmessage.encode(), client_address)
            

incoming_thread()

sock.close()
runThread = False