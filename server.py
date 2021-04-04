from socket import *
import time
import threading
import sys
import argparse
import logging
"""
USERS = [
    {
        "username",
        "password",
        "login"
    }
]

MESSAGES = {
    date : []
}

"""

FORMAT = "utf-8"
USERS = []
MESSAGES = {}

LOG = open('log.txt', "a+")



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
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


def login(username, password):
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
                u["login"] == True
                return True
            return False
    return False


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr[0]} connected.")

    connected = True
    login_flag = False

    print(f"[Logining In] ...")
    counter = 0
    # TODO: Change max to dynamic input value
    max = 3

    # Login
    while login_flag == False and counter < max:
        login_package = conn.recv(1024).decode(FORMAT)
        items = login_package.split(" ")
        username = items[0]
        password = items[1]
        check_details = login(username, password)
        if check_details:
            # Logged in
            login_flag == True
            # Return success message
            response = "SUCCESS: LOGIN".encode(FORMAT)
            conn.send(response)
            break
        response = "FAILED: LOGIN".encode(FORMAT)
        conn.send(response)
        counter += 1

    # Messaging
    if login_flag == False:
        print(f"[LOGIN SUCCESS] {addr} Logged in...")
        while connected:
            msg = conn.recv(1024).decode(FORMAT)
            print(f"[INCOMING MESSAGE] {msg}")
            if msg == "OUT":
                response = "SUCCESS: LOGOUT".encode(FORMAT)
                connected = False
            elif msg == "OUTX":
                connected = False
                print("OUTX")
            else:
                response = "YEET Back at you".encode(FORMAT)
            conn.send(response)
    conn.close()
    print(f"[CLOSED CONNECTION] {addr} closed.")
    return

def load_users():
    """
    Load all registered users and password
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
            "login"   : False
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
        LOG.close()
        # Close all connection
        server.close()
    print("\n[EXIT]")
    
