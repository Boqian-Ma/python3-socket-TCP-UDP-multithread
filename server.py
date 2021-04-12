from socket import *
import time
import threading
import sys
import argparse
import logging
from datetime import datetime

DATE_FORMAT = "%d %b %Y %H:%M:%S"

"""
USERS = [
    {
        "username",
        "password",
        "login"
        "tcp_port"
        "udp_port"
        "active_since"
        "ip",
    }
]

MESSAGES = [
    {
        "username",
        "timestamp",
        "message",
        "edited",
    }

]

ACTIVE_USERS = [
    {
        "username",
        "active_since",
        "ip",
        "tcp_port",
        "udp_port",
        "active_since"
    }
]

Tracking active users
refresh doc
"""



FORMAT = "utf-8"
USERS = []
MESSAGES = []
ACTIVE_USERS = []
CONNECTIONS = []
# LOG = open('log.txt', "a+")
# class active_user:
#     def __init__(username, ip, port_num):
#         self.username = username
# LOG = logging.getLogger("log")

def take_input():
    """
    Take input from command line
    TODO: Implement UDP
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("server_name", type=str, help="Enter server name.")
    parser.add_argument("tcp_port", type=int,  help="Enter a TCP port number for messaging.")
    # parser.add_argument("udp_port", type=int, help="Enter an UDP port number for P2P video sharing.")   
    args = parser.parse_args()
    server_name = args.server_name
    tcp_port = args.tcp_port
    # udp_port = args.udp_port
    return server_name, tcp_port

def start(server, ADDR):
    """
    Start a server
    """
    server.listen()
    print(f"[LISTENING] Server is listening on {ADDR[0]}:{ADDR[1]}")
    while True:
        # Handle multithreding
        conn, addr = server.accept()
        CONNECTIONS.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

def login(username, password, udp_port, addr):
    """
    Check user credentials 
    Returns:
        True if logged in
        False if unable to login
    """
    if username == None or password == None:
        return False
    for u in USERS:
        if u["username"] == username:
            if u["password"] == password and u["login"] is False:
                u["login"] = True
                u["udp_port"] = udp_port
                u["ip"] = addr[0]
                u["tcp_port"] = addr[1]
                u["active_since"] = datetime.now().strftime(DATE_FORMAT)
                return True
            return False
    return False


# def add_login_user(username, ip, portnumber) {
#     new_user = {
#         "username": username,
#         "ip": ip,
#         "port_num":
#     }
#     ACTIVE_USERS.append
# }

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    login_flag = False

    print(f"[Logining In] ...")
    counter = 0
    # TODO: Change max to dynamic input value
    max = 3
    # Login
    while login_flag == False and counter < max:
        login_package = conn.recv(1024).decode(FORMAT)
        # logout duing checkin 
        if login_package == "OUTX":
            # Log out on keyboard interrupt
            connected = False
            break
        
        items = login_package.split(" ")
        username = items[0]
        password = items[1]
        udp_port = items[2]

        check_details = login(username, password, udp_port, addr)
        if check_details:
            # Logged in
            login_flag = True
            # Return success message
            response = "SUCCESS: LOGIN".encode(FORMAT)
            conn.send(response)
            break
        response = "FAILED: LOGIN".encode(FORMAT)
        conn.send(response)
        counter += 1

    # Messaging
    if login_flag == True:
        print(f"[LOGIN SUCCESS] {addr} Logged in...")
        while connected:
            msg = conn.recv(2048).decode(FORMAT)
            print(f"[INCOMING MESSAGE] {msg}")

            response, logout = handle_requests(msg)

            if response is not None:
                response = response.encode(FORMAT)
            
            if logout is True:
                if response == "OUT":
                    response = "SUCCESS: LOGOUT".encode(FORMAT)
                connected = False
            
            conn.send(response)
            print(MESSAGES)
    conn.close()
    print(f"[CLOSED CONNECTION] {addr} closed.")
    return

def handle_out(current_user):
    global USERS
    """
    Logout an user
    """
    for user in USERS:
        if user["username"] == current_user:
            user["login"] = False
    
def handle_requests(msg):
    words = msg.split(" ")
    print(f"message = {msg}")
    command = words[0]
    # User name
    current_user = words[-1]
    # Message
    msg = words[:-1] # excluding username
    response = None 
    logout = False
    if command == "MSG":
        response = handle_msg(msg, current_user)
    
    elif command == "DLT":
        print("DLT command received but havent implemented")
    
    elif command == "EDM":
        print("EDM command received but havent implemented")
    
    elif command == "RDM":
        print("RDM command received but havent implemented")
    
    elif command == "ATU":
        # print("ATU command received but havent implemented")
        response = handle_atu(current_user)
        
    elif command == "OUT" or command == "OUTX":
        handle_out(current_user)    # logout current user
        response = "OUT"
        logout = True
    else:
        print("Invalid command, check implementation please")
    return response, logout


def handle_msg(msg, current_user):
    # msg[0] is command
    message = " ".join(msg[1:])
    create_message(current_user, message)
    return "Message Sent Successfully"

def create_message(username, message):
    global MESSAGES
    '''
    Create a message and append to messages, update textfile
    '''
    msg = {
        "username": username,
        "message": message,
        "edited": False,
        "timestamp": datetime.now().strftime(DATE_FORMAT)
    }
    MESSAGES.append(msg)

def handle_atu(current_user):
    '''
    Handles an AUT request
    Returns 
        a string of active users and their IP and UDP port if there is any

    Else returns "No Active Users"
    '''

    global USERS

    if current_user is None:
        return "No Other Active Users"
    
    active_users = []

    for user in USERS:
        if user["login"] is True and user["username"] != current_user:
            s = ""
            s += user["username"]
            s += " "
            s += user["ip"] 
            s += " udp/"
            s += user["udp_port"]
            active_users.append(s)
    
    if len(active_users) == 0:
        return "No Other Active Users"
    
    retstr = "\n".join(active_users)

    # print(f"actuve users = {active_users} retstr = {retstr}")
    return retstr
    


def load_users():
    global USERS
    """
    Load all registered users and password from txt file
    """
    credentials = open("credentials.txt", "r")
    users = [user[:-1] if user[-1] == "\n" else user for user in credentials]
    for u in users:
        user = u.split(" ")
        # print(user)
        username = user[0]
        password = user[1]
        dict = {
            "username" : username,
            "password" : password,
            "login"   : False,
            "udp_port": None,
            "tcp_port": None,
            "ip": None,
            "last_active": None
        }
        USERS.append(dict)
    # print(USERS)

def log(message):
    """
    Log message into a log file
    """
    pass


if __name__ == "__main__":
    # serverName = 'localhost' #Server would be running on the same host as Client
    # tcpPort = int(sys.argv[2])
    # TODO: Check return values
    load_users()
    server_name, tcp_port = take_input()
    TCP_ADDR = (server_name, tcp_port)
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(TCP_ADDR)

    try:
        start(server, TCP_ADDR)
    except KeyboardInterrupt:
        # LOG.close()
        # Close all connection
        for thread in threading.enumerate(): 
            print(thread)
        server.close()
    print("\n[EXIT]")
    
