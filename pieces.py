import subprocess
import sys
import threading
import json
import socket
import select
import random


DISC_PORT = 12345
MSG_PORT = 12346
CHESS_PIECE_PORTS = {"S-S-1": 10005, "S-V-1": 10004, "S-K-1": 10001, "S-A-1": 10002, "S-F-1": 10003,
                     "S-K-2": 10008, "S-A-2": 10007, "S-F-2": 10006, "S-P-1": 10011, "S-P-2": 10012,
                     "S-P-3": 10013, "S-P-4": 10014, "S-P-5": 10015, "S-P-6": 10016, "S-P-7": 10017,
                     "S-P-8": 10018, "B-S-1": 20005, "B-V-1": 20004, "B-K-1": 20001, "B-A-1": 20002,
                     "B-F-1": 20003, "B-K-2": 20008, "B-A-2": 20007, "B-F-2": 20006, "B-P-1": 20011,
                     "B-P-2": 20012, "B-P-3": 20013, "B-P-4": 20014, "B-P-5": 20015, "B-P-6": 20016,
                     "B-P-7": 20017, "B-P-8": 20018}
UI_COLORS = {"CGREEN": '\33[32m', "BLUE": '\x1b[1;37;44m', "LIGHT": '\x1b[7;37;40m', "RED": '\x1b[1;37;41m',
             "GREEN": '\x1b[5;30;42m', "YELLOW": '\x1b[2;30;43m', "PINK": '\x1b[2;30;45m', "END": '\x1b[0m'}
NAME = sys.argv[1].upper() +"-"+sys.argv[2].upper()
MY_IP = str(subprocess.check_output("hostname -I", shell=True), 'utf-8').split(' ')[0] 
TARGET_IPS = MY_IP+"/24"
ONLINES = {}
BUFFER_SIZE = 10240


def printColor(msg, color):
    print("LOG... {}: ".format(NAME),UI_COLORS[color] + msg+UI_COLORS["END"])

def sendDiscover():
    """
    Broadcasts a discover message
    """
    ID = random.randint(0, 10e7)
    for _ in range(10):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            # sock.bind(("",0))
            sock.settimeout(0.2)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = b'{"type":1, "name":"'+bytearray(NAME.encode())+b'"'+b', "IP":"'+bytearray(
                MY_IP.encode())+b'", "ID":'+str(ID).encode()+b'}'
            sock.sendto(message, ("<broadcast>", DISC_PORT))


def sendDiscoverResponse(target_ip):
    """
    Sends a response to a discover message
    """
    message = b'{"type":2, "name":"' + \
        bytearray(NAME.encode())+b'"'+b', "IP":"' + \
        bytearray(MY_IP.encode())+b'"}'
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_ip, MSG_PORT))
            s.sendall(message)
    except Exception as e:
        ...
        #print("LOG... {}: ".format(NAME),e)


def initializeTcpDiscoverResponseServer():
    """
    listens and answers discover response messages
    """
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                s.bind((MY_IP, MSG_PORT))
                s.listen()  # listen
                conn, addr = s.accept()
                with conn:
                    msg = ""
                    while True:
                        part_of_data = str(conn.recv(BUFFER_SIZE), 'utf-8')
                        msg += part_of_data
                        if not part_of_data:
                            break
                    if msg == "":
                        break

            incoming_message_in_json = json.loads(msg)
            if incoming_message_in_json["type"] == 2:
                if incoming_message_in_json["name"] == NAME:
                    continue
                if(ONLINES.get(incoming_message_in_json["name"]) is None):
                    ONLINES[incoming_message_in_json["name"]
                            ] = incoming_message_in_json["IP"]
        except Exception as e:
            ...
            #print("LOG... {}: ".format(NAME),e)


def broadcastYourMove(prev_location,new_location):
    """
    Broadcast your move to every other client, send 10 UDP messages with same ID    
    """
    
    ID = random.randint(0, 10e7)
    for _ in range(10):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            # sock.bind(("",0))
            sock.settimeout(0.2)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = b'{"type":4, "name":"'+bytearray(NAME.encode())+b'"'+b', "IP":"'+bytearray(
                MY_IP.encode())+b'", "ID":'+str(ID).encode()+b', "new_loc":"'+bytearray(new_location.encode())+b'", "prev_loc":"'+bytearray(prev_location.encode())+b'"}'
            sock.sendto(message, ("<broadcast>", DISC_PORT))


def initializeTcpChatServer():
    """
    listens movement message from player and calls broadcast fucntion
    """
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                s.bind((MY_IP, CHESS_PIECE_PORTS[NAME]))
                s.listen()  # listen
                conn, addr = s.accept()
                with conn:
                    msg = ""
                    while True:
                        part_of_data = str(conn.recv(BUFFER_SIZE), 'utf-8')
                        msg += part_of_data
                        if not part_of_data:
                            break
                    if msg == "":
                        break

            incoming_message_in_json = json.loads(msg)
            if incoming_message_in_json["type"] == 3:  # message came
                if incoming_message_in_json["name"] == NAME:
                    continue
                if (ONLINES.get(incoming_message_in_json["name"]) is None):
                    ONLINES[incoming_message_in_json["name"]] = addr[0]
                broadcastYourMove(incoming_message_in_json["prev_loc"],incoming_message_in_json["new_loc"])
        except Exception as e:
            print(e)
            pass


def initializeUdpServer():
    """
    listens discover messages
    """
    incoming_message_ids = set()
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.bind(("", DISC_PORT))
            # s.setblocking(1)
            result = select.select([s], [], [])
            msg = result[0][0].recv(BUFFER_SIZE)
        # now we got the message
        try:  # check whether message format is valid
            incoming_message_in_json = json.loads(msg)
            #    raise Exception
        except:  # if not raise exception and listen next message
            #print("LOG... {}: ".format(NAME),"***Incoming message was not in good format!***")
            continue
        # do not listen to myself
        if incoming_message_in_json["name"] == NAME:
            continue
        # only take one udp message from each burst
        if incoming_message_in_json["ID"] not in incoming_message_ids:
            incoming_message_ids.add(incoming_message_in_json["ID"])
        else:
            continue

        # return discover response
        if incoming_message_in_json["type"] == 1:
            # if incoming_message_in_json["name"] not in ONLINES:
            discover_response_thread = threading.Thread(
                target=sendDiscoverResponse, args=(incoming_message_in_json["IP"],))
            discover_response_thread.start()

        # we would not want to run out of memory
        if len(incoming_message_ids) > 10000:
            incoming_message_ids.clear()


if __name__ == "__main__":
    tcp_server_for_discover_response_thread = threading.Thread(target=initializeTcpDiscoverResponseServer)
    tcp_server_for_chat_thread = threading.Thread(target=initializeTcpChatServer)
    udp_server_for_discover_thread = threading.Thread(target=initializeUdpServer)
    discover_thread = threading.Thread(target=sendDiscover)
    tcp_server_for_discover_response_thread.start()
    udp_server_for_discover_thread.start()
    discover_thread.start()
    tcp_server_for_chat_thread.start()
