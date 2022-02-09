import subprocess
import sys
import os
import threading
import json
import socket
import select
import random
from time import sleep

CHARS = ["A", "B", "C", "D", "E", "F", "G", "H"]
NUMBERS = ["1", "2", "3", "4", "5", "6", "7", "8"]

BOARD_CONFIG = {"1": {"A": "B-K-1", "B": "B-A-1", "C": "B-F-1",
                      "D": "B-S-1", "E": "B-V-1", "F": "B-F-2",
                      "G": "B-A-2", "H": "B-K-2"},
                "2": {"A": "B-P-1", "B": "B-P-2", "C": "B-P-3",
                      "D": "B-P-4", "E": "B-P-5", "F": "B-P-6",
                      "G": "B-P-7", "H": "B-P-8"},
                "3": {"A": "", "B": "", "C": "",
                      "D": "", "E": "", "F": "",
                      "G": "", "H": ""},
                "4": {"A": "", "B": "", "C": "",
                      "D": "", "E": "", "F": "",
                      "G": "", "H": ""},
                "5": {"A": "", "B": "", "C": "",
                      "D": "", "E": "", "F": "",
                      "G": "", "H": ""},
                "6": {"A": "", "B": "", "C": "",
                      "D": "", "E": "", "F": "",
                      "G": "", "H": ""},
                "7": {"A": "S-P-1", "B": "S-P-2", "C": "S-P-3",
                      "D": "S-P-4", "E": "S-P-5", "F": "S-P-6",
                      "G": "S-P-7", "H": "S-P-8"},
                "8": {"A": "S-K-1", "B": "S-A-1", "C": "S-F-1",
                      "D": "S-V-1", "E": "S-S-1", "F": "S-F-2",
                      "G": "S-A-2", "H": "S-K-2"}
                }

DISC_PORT = 12345
MSG_PORT = 12346
COLOR = sys.argv[1]

CHESS_PIECE_PORTS = {"S-S-1": 10005, "S-V-1": 10004, "S-K-1": 10001, "S-A-1": 10002, "S-F-1": 10003,
                     "S-K-2": 10008, "S-A-2": 10007, "S-F-2": 10006, "S-P-1": 10011, "S-P-2": 10012,
                     "S-P-3": 10013, "S-P-4": 10014, "S-P-5": 10015, "S-P-6": 10016, "S-P-7": 10017,
                     "S-P-8": 10018, "B-S-1": 20005, "B-V-1": 20004, "B-K-1": 20001, "B-A-1": 20002,
                     "B-F-1": 20003, "B-K-2": 20008, "B-A-2": 20007, "B-F-2": 20006, "B-P-1": 20011,
                     "B-P-2": 20012, "B-P-3": 20013, "B-P-4": 20014, "B-P-5": 20015, "B-P-6": 20016,
                     "B-P-7": 20017, "B-P-8": 20018}
UI_COLORS = {"CGREEN": '\33[32m', "BLUE": '\x1b[1;37;44m', "LIGHT": '\x1b[7;37;40m', "RED": '\x1b[1;37;41m',
             "GREEN": '\x1b[5;30;42m', "YELLOW": '\x1b[2;30;43m', "PINK": '\x1b[2;30;45m', "END": '\x1b[0m'}
NAME = "player "+COLOR
TURN = 0 if COLOR == "S" else 1
PLAYER_PORT = 10000 if COLOR == "S" else 20000
MY_IP = str(subprocess.check_output("hostname -I", shell=True), 'utf-8').split(' ')[0]
TARGET_IPS = MY_IP+"/24"
ONLINES = {}
BUFFER_SIZE = 10240


def isGameFinished():
    """
    calculate whether game is finished by looking at whether "şah" exists
    """
    isWhiteSahAlive = False
    isBlackSahAlive = False
    for row_id in NUMBERS:
        for col_id in CHARS:
            piece = BOARD_CONFIG[row_id][col_id]
            if piece == "S-S-1":
                isBlackSahAlive = True
            if piece == "B-S-1":
                isWhiteSahAlive = True
    if not isWhiteSahAlive:
        return True, "S"
    elif not isBlackSahAlive:
        return True, "B"
    else:
        return False, " "


def printColor(msg, color):
    print(UI_COLORS[color] + msg+UI_COLORS["END"])


def promptInput():
    """
    take user input if it's user's turn
    """
    listOfGlobals = globals()
    if listOfGlobals["TURN"] == 1:
        send_chat_message_thread = threading.Thread(target=sendMoveMessage)
        send_chat_message_thread.start()


def pieceMoved(name, new_loc, prev_loc):
    """
    After a piece broadcasted its movement, update the board, calcualte the status of the game, take user input or terminate the program
    """
    listOfGlobals = globals()

    if name[0] != COLOR:
        printColor(msg="Opponent made a move!\t from: {}, to: {}".format(
            prev_loc, new_loc), color="GREEN")
        listOfGlobals["TURN"] = 1
    else:
        listOfGlobals["TURN"] = 0
    BOARD_CONFIG[new_loc[0]][new_loc[1]], BOARD_CONFIG[prev_loc[0]][prev_loc[1]] = BOARD_CONFIG[prev_loc[0]][prev_loc[1]], ""
    printChessBoard()
    is_game_finished, who_won = isGameFinished()
    if is_game_finished:
        if who_won[0] == COLOR:
            printColor("You won!", "GREEN")
        elif who_won[0] != " ":
            printColor("Opponent won!", "RED")
        os._exit(1)
    promptInput()


def sendDiscover():
    """
    Broadcasts a discover message
    """
    while True:
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
        sleep(3)


def sendDiscoverResponse(target_ip):
    """
    Sends a response to a discover message
    """
    message = b'{"type":2, "name":"' + bytearray(NAME.encode())+b'"'+b', "IP":"' + bytearray(MY_IP.encode())+b'"}'
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_ip, MSG_PORT))
            s.sendall(message)
    except Exception as e:
        ...
        # print(e)


def possibleNewLocations(color, piece_type, current_loc):
    """
    Calculates the possible locations that a piece can be moved
    """
    possible_locs = []
    if piece_type == "A":  # at
        for i in [-2, 2]:
            for j in [-1, 1]:
                if CHARS.index(current_loc[1])+j > 7 or 0 > CHARS.index(current_loc[1])+j:
                    continue
                if int(current_loc[0])+i > 8 or 1 > int(current_loc[0])+i:
                    continue
                possible_locs.append(
                    str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])+j])

                if CHARS.index(current_loc[1])+i > 7 or 0 > CHARS.index(current_loc[1])+i:
                    continue
                if int(current_loc[0])+j > 8 or 1 > int(current_loc[0])+j:
                    continue
                possible_locs.append(
                    str(int(current_loc[0])+j)+CHARS[CHARS.index(current_loc[1])+i])
    if piece_type == "K" or piece_type == "V":  # kale ya da vezir
        for i in range(-1, -8, -1):
            if int(current_loc[0])+i > 8 or 1 > int(current_loc[0])+i:
                break
            if BOARD_CONFIG[str(int(current_loc[0])+i)][current_loc[1]] != "":
                if BOARD_CONFIG[str(int(current_loc[0])+i)][current_loc[1]][0] != COLOR:
                    possible_locs.append(
                        str(int(current_loc[0])+i)+current_loc[1])
                break
            possible_locs.append(str(int(current_loc[0])+i)+current_loc[1])
        for i in range(-1, -8, -1):
            if CHARS.index(current_loc[1])+i > 7 or 0 > CHARS.index(current_loc[1])+i:
                break
            if BOARD_CONFIG[str(int(current_loc[0]))][CHARS[CHARS.index(current_loc[1])+i]] != "":
                if BOARD_CONFIG[str(int(current_loc[0]))][CHARS[CHARS.index(current_loc[1])+i]][0] != COLOR:
                    possible_locs.append(
                        str(int(current_loc[0]))+CHARS[CHARS.index(current_loc[1])+i])
                break
            possible_locs.append(
                str(int(current_loc[0]))+CHARS[CHARS.index(current_loc[1])+i])
        for i in range(1, 8):
            if int(current_loc[0])+i > 8 or 1 > int(current_loc[0])+i:
                break
            if BOARD_CONFIG[str(int(current_loc[0])+i)][current_loc[1]] != "":
                if BOARD_CONFIG[str(int(current_loc[0])+i)][current_loc[1]][0] != COLOR:
                    possible_locs.append(
                        str(int(current_loc[0])+i)+current_loc[1])
                break
            possible_locs.append(str(int(current_loc[0])+i)+current_loc[1])
        for i in range(1, 8):
            if CHARS.index(current_loc[1])+i > 7 or 0 > CHARS.index(current_loc[1])+i:
                break
            if BOARD_CONFIG[str(int(current_loc[0]))][CHARS[CHARS.index(current_loc[1])+i]] != "":
                if BOARD_CONFIG[str(int(current_loc[0]))][CHARS[CHARS.index(current_loc[1])+i]][0] != COLOR:
                    possible_locs.append(
                        str(int(current_loc[0]))+CHARS[CHARS.index(current_loc[1])+i])
                break
            possible_locs.append(
                str(int(current_loc[0]))+CHARS[CHARS.index(current_loc[1])+i])
    if piece_type == "P":  # piyon
        i = -1 if color == "S" else 1
        if CHARS.index(current_loc[1])+i > 0 and 8 > CHARS.index(current_loc[1])+i and BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])+i]] != "" and BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])+i]][0] != COLOR:
            possible_locs.append(
                str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])+i])
        if CHARS.index(current_loc[1])-i > 0 and 8 > CHARS.index(current_loc[1])-i and BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])-i]] != "" and BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])-i]][0] != COLOR:
            possible_locs.append(
                str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])-i])
        if BOARD_CONFIG[str(int(current_loc[0])+i)][current_loc[1]] == "":
            possible_locs.append(str(int(current_loc[0])+i)+current_loc[1])
    if piece_type == "S":  # şah
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if i == 0 and j == 0:
                    continue
                if CHARS.index(current_loc[1])+j > 7 or 0 > CHARS.index(current_loc[1])+j:
                    continue
                if int(current_loc[0])+i > 8 or 1 > int(current_loc[0])+i:
                    continue
                possible_locs.append(
                    str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])+j])

                if CHARS.index(current_loc[1])+i > 7 or 0 > CHARS.index(current_loc[1])+i:
                    continue
                if int(current_loc[0])+j > 8 or 1 > int(current_loc[0])+j:
                    continue
                possible_locs.append(
                    str(int(current_loc[0])+j)+CHARS[CHARS.index(current_loc[1])+i])
    if piece_type == "F" or piece_type == "V":  # fil ya da vezir     
        for i in range(-1, -8, -1):
            if int(current_loc[0])+i > 8 or 1 > int(current_loc[0])+i or CHARS.index(current_loc[1])+i > 7 or 0 > CHARS.index(current_loc[1])+i:
                break
            if BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])+i]] != "":
                if BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])+i]][0] != COLOR:
                    possible_locs.append(str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])+i])
                break
            possible_locs.append(str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])+i])
        for i in range(-1, -8, -1):
            if CHARS.index(current_loc[1])-i > 7 or 0 > CHARS.index(current_loc[1])-i or int(current_loc[0])+i > 8 or 1 > int(current_loc[0])+i:
                break
            if BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])-i]] != "":
                if BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])-i]][0] != COLOR:
                    possible_locs.append(str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])-i])
                break
            possible_locs.append(str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])-i])
        for i in range(1, 8):
            if int(current_loc[0])+i > 8 or 1 > int(current_loc[0])+i or CHARS.index(current_loc[1])-i > 7 or 0 > CHARS.index(current_loc[1])-i:
                break
            if BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])-i]] != "":
                if BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])-i]][0] != COLOR:
                    possible_locs.append(str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])-i])
                break
            possible_locs.append(str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])-i])
        for i in range(1, 8):
            if CHARS.index(current_loc[1])+i > 7 or 0 > CHARS.index(current_loc[1])+i or int(current_loc[0])+i > 8 or 1 > int(current_loc[0])+i:
                break
            if BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])+i]] != "":
                if BOARD_CONFIG[str(int(current_loc[0])+i)][CHARS[CHARS.index(current_loc[1])+i]][0] != COLOR:
                    possible_locs.append(str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])+i])
                break
            possible_locs.append(str(int(current_loc[0])+i)+CHARS[CHARS.index(current_loc[1])+i])

    for possible_loc in possible_locs:
        if BOARD_CONFIG[possible_loc[0]][possible_loc[1]] != "" and BOARD_CONFIG[possible_loc[0]][possible_loc[1]][0] == COLOR:
            possible_locs.remove(possible_loc)
    return possible_locs


def isInputValid(piece_name, prev_loc, new_loc):
    """
    return whether user input is valid
    """
    if new_loc[0] not in NUMBERS or new_loc[1] not in CHARS:
        return False, "That location is out of bounds! Example input: 1a or 8h"
    possible_locs = possibleNewLocations(
        piece_name[0], piece_name[2], prev_loc)
    if new_loc not in possible_locs:
        return False, "That piece can't make that move. These are the possible positions to move it: {}".format(" ".join(set(possible_locs)))
    else:
        return True, ""


def sendMoveMessage():
    """
    Takes user input and sends it to the piece client with TCP.
    """
    is_input_capture_completed = False
    while not is_input_capture_completed:
        while True: # take input from user about the piece to be moved
            piece_location = input(UI_COLORS["LIGHT"] + "WHICH PIECE DO YOU WANT TO MOVE?"+UI_COLORS["END"]+"\t").upper()
            if 2 > len(piece_location):
                printColor("*** WRONG INPUT ***","RED")
                continue
            if piece_location[0] not in NUMBERS or piece_location[1] not in CHARS:
                printColor(
                    msg="That location is out of bounds! Example input: 1a or 8h", color="RED")
                continue
            piece_name = BOARD_CONFIG[piece_location[0]][piece_location[1]]
            if piece_name == "":
                printColor(msg="That location is empty!", color="RED")
            elif piece_name[0] != COLOR:
                printColor(msg="You can only move your pieces!", color="RED")
            else:
                break
        target_ip = ONLINES.get(piece_name)
        if(target_ip is None):
            printColor("*** WRONG INPUT ***","RED")
        while True: # take input from user about the new location of the piece to be moved
            input_message = input(UI_COLORS["LIGHT"]+"WHERE DO YOU WANT TO MOVE IT:\t" + UI_COLORS["END"]).upper()
            if 2 > len(input_message):
                printColor("*** WRONG INPUT ***","RED")
                continue
            isValid, msg = isInputValid(piece_name, piece_location, input_message)
            if not isValid:
                printColor(msg, "RED")
                if 79 > len(msg):
                    printColor("This piece cant be moved!", "RED")
                    break
            else:
                is_input_capture_completed = True
                break
    # prepare message to be sent to peice client
    message = b'{"type":3, "name":"'+bytearray(NAME.encode())+b'"'+b', "new_loc":"'+bytearray(
        input_message.encode())+b'", "prev_loc":"'+bytearray(piece_location.encode())+b'"}'
    try:# try to send the message to piece client with TCP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_ip, CHESS_PIECE_PORTS[piece_name]))
            s.sendall(message)

    except Exception as ex:
        print(ex)
        print(UI_COLORS["PINK"]+"IT SEEMS THAT USER YOU ARE TRYING TO REACH IS OFFLINE"+UI_COLORS["END"])
        ONLINES.pop(piece_name)


def initializeTcpDiscoverResponseServer():
    """
    listens and answers discover response messages
    """
    while True: 
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP) as s:
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
            # add them to onlines list
            if incoming_message_in_json["type"] == 2:
                if incoming_message_in_json["name"] == NAME:
                    continue
                if(ONLINES.get(incoming_message_in_json["name"]) is None):
                    ONLINES[incoming_message_in_json["name"]
                            ] = incoming_message_in_json["IP"]
        except Exception as e:
            print(e)


def initializeUdpServer():
    """
    listens incoming UDP messages
    possible messages are type 1: discover and type 4:broadcast from a piece
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
            # if set(["type","name","ID","IP"]) != incoming_message_in_json.keys():
            #    raise Exception
        except:  # if not raise exception and listen next message
            print("***Incoming message was not in good format!***")
            continue
        # do not listen to myself
        if incoming_message_in_json["name"] == NAME:
            continue
        # if incoming_message_in_json["IP"] == MY_IP:
        #    continue
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
            if incoming_message_in_json["name"] == NAME:
                continue
            if(ONLINES.get(incoming_message_in_json["name"]) is None):
                ONLINES[incoming_message_in_json["name"]
                        ] = incoming_message_in_json["IP"]

        # a piece broadcasted its movement, take necessary actions
        if incoming_message_in_json["type"] == 4:
            # a piece is moved, update the board.
            pieceMoved(
                incoming_message_in_json["name"], incoming_message_in_json["new_loc"], incoming_message_in_json["prev_loc"])
        # we would not want to run out of memory
        if len(incoming_message_ids) > 10000:
            incoming_message_ids.clear()


def printChessBoard():
    """
    prints current config of the chess board
    """
    print("\n  A B C D E F G H")
    for row_id in NUMBERS[::-1]:
        print(row_id, end="")
        for col_id in CHARS:
            piece = BOARD_CONFIG[row_id][col_id]
            if piece != "":
                color = "YELLOW" if piece[0] == "S" else "BLUE"
                print("|", UI_COLORS[color] + str("\033[4m{}\033[0m").format(
                    piece[2])+UI_COLORS["END"], end="", sep="")
            else:
                print("|", "_", end="", sep="")
        print("|{}".format(row_id))
    print("  A B C D E F G H")


if __name__ == "__main__":
    tcp_server_for_discover_response_thread = threading.Thread(target=initializeTcpDiscoverResponseServer)
    udp_server_for_discover_thread = threading.Thread(target=initializeUdpServer)
    discover_thread = threading.Thread(target=sendDiscover)
    tcp_server_for_discover_response_thread.start()
    udp_server_for_discover_thread.start()
    discover_thread.start()

    """
    Runs piece client scripts one by one
    """
    for i in range(1, 9):
        subprocess.Popen(
            ["python3", "pieces.py", COLOR[0], "P-{}".format(i), "&"])
        sleep(0.3)
    for i in range(1, 3):
        subprocess.Popen(
            ["python3", "pieces.py", COLOR[0], "A-{}".format(i), "&"])
        sleep(0.3)
        subprocess.Popen(
            ["python3", "pieces.py", COLOR[0], "K-{}".format(i), "&"])
        sleep(0.3)
        subprocess.Popen(
            ["python3", "pieces.py", COLOR[0], "F-{}".format(i), "&"])
        sleep(0.3)
    subprocess.Popen(["python3", "pieces.py", COLOR[0], "V-1", "&"])
    sleep(0.3)
    subprocess.Popen(["python3", "pieces.py", COLOR[0], "S-1", "&"])
    
    while(31 > len(ONLINES)):
    # waits until all the pieces are discovered
        printColor("Setting up the game...", "PINK")
        sleep(3)
    input("Press enter to begin!")
    printChessBoard()
    promptInput()
