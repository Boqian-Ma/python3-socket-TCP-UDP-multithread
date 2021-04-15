from socket import *
import time
import threading
import sys
import argparse
import logging
from datetime import datetime
import datetime as d

"""
USERS = [
    {
        "username",
        "password",
        "login",
        "tcp_port",
        "udp_port",
        "active_since"
        "ip",
        "can_login_after"
        "login_attampts",
    }
]

MESSAGES = [
    {
        "username",
        "last_modified",
        "message",
        "edited",
    }
]

"""

DATE_FORMAT = "%d %b %Y %H:%M:%S"
ZERO_OFFSET = 1
FORMAT = "utf-8"
USERS = []
MESSAGES = []
MAX_LOGIN_ATTAMPTS = 1
CONNECTIONS = []



def update_message_log():

    global MESSAGES
    message_log = open('messagelog.txt', "w+")
    i = 1

    all_messages = []

    for m in MESSAGES:
        entry = str(i) + "; "
        entry += m["last_modified"] + "; "
        entry += m["username"] + "; "
        entry += m["message"] + "; "
        if m["edited"]:
            entry += "yes"
        else:
            entry += "no"
        all_messages.append(entry)
        i += 1
    
    message_log.write("\n".join(all_messages))
    message_log.close()


def update_user_log():
    """
    Update userlog.txt
    """
    global USERS
    user_log = open('userlog.txt', "w+")
    i = 1
    all_users = []
    for u in USERS:
        if u['login'] is True:
            entry = str(i) + "; "
            entry += (u["active_since"] + "; ")
            entry += (u["username"] + "; ")
            entry += (u["ip"] + "; ")
            entry += u["udp_port"]
            all_users.append(entry)
            i += 1
    user_log.write("\n".join(all_users))
    user_log.close()




def take_input():
    """
    Take input from command line
    TODO: Implement UDP
    """
    global MAX_LOGIN_ATTAMPTS
    parser = argparse.ArgumentParser()
    parser.add_argument("server_name", type=str, help="Enter server name.")
    parser.add_argument("tcp_port", type=int,  help="Enter a TCP port number for messaging.")
    parser.add_argument("max_login_attampts", type=int, choices=range(1, 6), help="Invalid number of allowed failed consecutive attempt: number (1,5)")
    # parser.add_argument("udp_port", type=int, help="Enter an UDP port number for P2P video sharing.")   
    args = parser.parse_args()
    MAX_LOGIN_ATTAMPTS = args.max_login_attampts

    dict = {
        "server_name": args.server_name,
        "tcp_port": args.tcp_port,
        "max_login_attampts": MAX_LOGIN_ATTAMPTS
    }
    return dict

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
        # Invalid input
        return False, False
    
    for u in USERS:
        if u["username"] == username:
            # check time and attampt count
            # if time is less then allowed login, return false
            curr_time = datetime.now()
            can_login_after_time = datetime.strptime(u["can_login_after"], DATE_FORMAT)

            # If still within range
            if curr_time < can_login_after_time:
                now = datetime.now()
                seconds_left = datetime.strptime(u["can_login_after"], DATE_FORMAT) - now
                seconds_left_string = str(int(seconds_left.total_seconds()))
                
                return False, seconds_left_string

            if u["password"] == password and u["login"] is False:
                # Reset attamp counter 
                u["login_attampts"] = 0
                u["login"] = True
                u["udp_port"] = udp_port
                u["ip"] = addr[0]
                u["tcp_port"] = addr[1]
                u["active_since"] = datetime.now().strftime(DATE_FORMAT)

                return True, False
            # add an attampt because failed passedword

            u["login_attampts"] =+ 1

            # Max attampts reached
            if u["login_attampts"] >= MAX_LOGIN_ATTAMPTS:
                # Reset attampts
                u["login_attampts"] = 0
                # Set login time
                now = datetime.now()
                u["can_login_after"] = (now + d.timedelta(0,10)).strftime(DATE_FORMAT)

                seconds_left = datetime.strptime(u["can_login_after"], DATE_FORMAT) - now
                seconds_left_string = str(int(seconds_left.total_seconds()))
                return False, seconds_left_string


            return False, False
    # Cant find user
    return False, False

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    login_flag = False

    # print(f"[Logining In] ...")
    login_attampt_counter = 0

    # Login
    while login_flag == False:
        login_package = conn.recv(1024).decode(FORMAT)
        # logout duing checkin 
        if login_package == "OUTX":
            # Log out on keyboard interrupt during login
            connected = False
            break
        
        items = login_package.split(" ")
        username = items[0]
        password = items[1]
        udp_port = items[2]

        check_details, time_left_str = login(username, password, udp_port, addr)

        # check login counter
        if time_left_str is not False:
            response = "LOGIN: REACHED MAXIMUM ATTAMPTS " + time_left_str
            response = response.encode(FORMAT)
            conn.send(response)
            break

        if check_details:
            # Logged in
            login_flag = True
            # Return success message
            response = "LOGIN: SUCCESS".encode(FORMAT)
            conn.send(response)
            break
        
        response = "LOGIN: FAILED".encode(FORMAT)
        conn.send(response)

    # Messaging
    if login_flag == True:
        print(f"[LOGIN SUCCESS] {username}:{addr} Logged in...")
        update_user_log()
        while connected:
            msg = conn.recv(2048).decode(FORMAT)
            print(f"[INCOMING MESSAGE] {msg}")

            response, logout = handle_requests(msg)

            # Normal Respond 
            if response is not None and logout is False:
                response = response.encode(FORMAT)

            # Logout Respond 
            if logout is True:
                if response == "OUT":
                    response = "LOGOUT: SUCCESS".encode(FORMAT)
                connected = False

            conn.send(response)
    conn.close()
    print(f"[CLOSED CONNECTION] {username}:{addr} closed.")
    return

def print_active_users():
    """
    Debug
    """
    for u in USERS:
        if u['login'] is True:
            print(u)

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
        response = handle_dlt(msg, current_user)

    elif command == "EDT":
        response = handle_edt(msg, current_user)
    
    elif command == "RDM":
        response = handle_rdm(msg)
    
    elif command == "ATU":
        response = handle_atu(current_user)
    
    elif command == "OUT" or command == "OUTX":
        handle_out(current_user)
        response = "OUT"
        logout = True
        update_user_log()   # Update user log

    else:
        print("Invalid command, check implementation please")

    update_message_log() # Update message log

    return response, logout

def handle_edt(msg, current_user):
    '''
    Handle an edit message request: a message can only be deleted by the sender
    
    msg: EDT messagenumber timestamp message

    Returns: Messagenumber; timestamp; username; message; edited
    '''
    global MESSAGES

    msg_num = int(msg[1]) - ZERO_OFFSET
    timestamp_str = " ".join(msg[2:6])    
    timestamp = datetime.strptime(timestamp_str, DATE_FORMAT)
    new_message = " ".join(msg[6:])

    edited_message = find_message(msg_num, timestamp, current_user)

    if edited_message is False:
        return "Message Editing Failed: Please Check Details Entered"

    MESSAGES[msg_num]["edited"] = True
    MESSAGES[msg_num]["message"] = new_message
    now = datetime.now().strftime(DATE_FORMAT)
    MESSAGES[msg_num]["last_modified"] = now

    return "#" + str(msg_num) + "; " + now + "; " + current_user + "; " + "edited" 

def find_message(msg_num, timestamp, current_user):
    '''
    Find a message
    Returns True if found, False if not found
    '''
    global MESSAGES
    try:
        m = MESSAGES[msg_num]
        m_timestamp = datetime.strptime(m["last_modified"], DATE_FORMAT)
        if m_timestamp == timestamp and m["username"] == current_user:
            return True
    except IndexError:
        return False
    return False

def handle_dlt(msg, current_user):
    '''
    Handle a delete request: a message can only be deleted by the sender
    '''
    global MESSAGES 

    msg_num = int(msg[1]) - ZERO_OFFSET
    timestamp_str = " ".join(msg[2:])    
    timestamp = datetime.strptime(timestamp_str, DATE_FORMAT)

    deleted_message = find_message(msg_num, timestamp, current_user)

    if deleted_message is False:
        return "Message Removed Failed: Please Check Details Entered"
    
    m = MESSAGES[msg_num]
    MESSAGES.remove(m)

    return "Message Removed Successfully"

def handle_rdm(msg):
    '''
    Handle a read message request
    Input:
        <List> msg: a list of words in incoming request
    Output:
        String response: a string containing response message
    '''
    timestamp_str = " ".join(msg[1:])
    timestamp = datetime.strptime(timestamp_str, DATE_FORMAT)
    retstr = get_messages(timestamp)
    return retstr

def get_messages(timestamp):
    '''
    Retrive messages in this session after a timestamp
    Returns:
        A string of all messages after a timestamp
    '''
    messages = []
    i = 0
    for m in MESSAGES:
        m_timestamp = datetime.strptime(m["last_modified"], DATE_FORMAT)
        if m_timestamp >= timestamp:
            messages.append((m, i))
        i += 1
    
    retstr = message_list_to_string(messages)

    if retstr is None:
        retstr = "No Available Messages"

    return retstr

def message_list_to_string(messages):
    '''
    Change a list of messages to a string
    Messages: a list of tuples (message dict, message number)
    '''
    if len(messages) == 0:
        return None
    strs = []
    for m in messages:
        message = m[0]
        num = m[1]
        s = "#" + str(num + ZERO_OFFSET) + ", "
        s += message["username"] + ": "
        s += message["message"] + ", "
        if (message["edited"]):
            s += "edited at "
        else:
            s += "posted at "
        s += message["last_modified"]
        strs.append(s)
    
    retstr = "\n".join(strs)
    return retstr

def handle_msg(msg, current_user):
    '''
    Handle a MSG request
    '''
    message = " ".join(msg[1:])
    create_message(current_user, message)
    return "Message Sent Successfully"

def create_message(username, message):
    '''
    Create a message and append to messages, update textfile
    '''
    global MESSAGES
    msg = {
        "username": username,
        "message": message,
        "edited": False,
        "last_modified": datetime.now().strftime(DATE_FORMAT)
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
    return retstr

def load_users():
    """
    Load all registered users and password from txt file
    """
    global USERS
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
            "active_since": None,
            "can_login_after": datetime.now().strftime(DATE_FORMAT),
            "login_attampts": 0
        }
        USERS.append(dict)

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

    input_dict = take_input()

    TCP_ADDR = (input_dict["server_name"], input_dict["tcp_port"])
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(TCP_ADDR)

    try:
        start(server, TCP_ADDR)
    except KeyboardInterrupt:

        for c in CONNECTIONS:
            c.close()

        server.close()
    print("\n[EXIT SERVER]")
    
