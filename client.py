from socket import *
import time
import random
import argparse
import datetime

STATE = 0 # logout = 0, login = 1
FORMAT = "utf-8"

WELCOME = "Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT):"
DATE_FORMAT = "%d %b %Y %H:%M:%S"
def take_input():
    parser = argparse.ArgumentParser()
    parser.add_argument("server_name", type=str, help="Enter server name.")
    parser.add_argument("tcp_port", type=int,  help="Enter a TCP port number for messaging.")
    # parser.add_argument("udp_port", type=int, help="Enter an UDP port number for P2P video sharing.")   
    args = parser.parse_args()
    server_name = args.server_name
    tcp_port = args.tcp_port
    # udp_port = args.udp_port
    return server_name, tcp_port #, udp_port

def send_message(msg, tcp_client):
    '''
    Encode and send a message

    Output: 
        decoded response message from server
    '''
    message = msg.encode(FORMAT)
    tcp_client.send(message)
    response = tcp_client.recv(2048).decode(FORMAT)
    return response


def connect(tcp_client):
    connected = False
    # Login 
    while not connected:
        # Get login details
        username = input("Enter User Name: ")
        password = input("Enter Password: ")
        package = username + " " + password
        # Send login details
        response = send_message(package, tcp_client)
        if str(response) == "SUCCESS: LOGIN":
            connected = True
            print("Login Succeed...")
        else:
            print("Please Check Login Details...")
    print("Select from the following options to continue...")
    while connected:
        input_msg = str(input(WELCOME))

        # Validate input
        retstr = user_actions(input_msg)
        if retstr is None:
            print("[INVALID COMMAND] Please try again...")
            continue

        # If clients requests to disconnect
        if retstr == "OUT":
            # Log out
            connected = False
            response = send_message(input_msg, tcp_client)
            print(f"[SERVER RESPOND] {response}")
            continue
        
        # Send message 
        response = send_message(input_msg, tcp_client)
        print(f"[SERVER RESPOND] {response}")
    return

def user_actions(user_input):
    """
    Process user actions
    MSG: Post Message
    DLT: Delete Message
    EDT: Edit Message
    RDM: Read Message
    ATU: Display active users
    OUT: Log out and UPD: Upload file
    """
    # user_input = str(input(WELCOME))
    # Remove trailing spaces
    user_input = user_input.rstrip()
    command = user_input[:3]
    retstr = None # Return string
    if command == "MSG":
        # Send message
        if validate_msg(user_input):
            retstr = user_input
    elif command == "DLT":
        # Delete message
        if validate_dlt(user_input):
            retstr = user_input
    elif command == "EDT":
        if validate_edt(user_input):
            retstr = user_input
    elif command == "RDM":
        if validate_rdm(user_input):
            retstr = user_input
    elif command == "ATU":
        if validate_atu(user_input):
            retstr = user_input
    elif command == "OUT":
        retstr = command
    else:
        retstr = None
    return retstr, command


def validate_int(string):
    """
    Given a string
    Returns
        True is its an integer
        None is not
    """
    try: 
        int(string)
    except ValueError:
        return False
    return True

def validate_time(str):
    """
    Validate if a string is in the proper date format

    Returns 
        True if string is in FORMAT
        None if string in not in FORMAT
    """
    try:   
        datetime.datetime.strptime(str, DATE_FORMAT)
    except ValueError:
        return False
    return True

def validate_msg(input):
    """
    Validate Message
    MSG MESSAGE
    """
    words = input.split(" ")
    command = words[0]
    msg = words[1:]
    print(f"msg = {msg}")
    if command != "MSG":
        return False
    if not msg:
        return False
    return True

def validate_dlt(input):
    """
    Validate delete message input
    Date format:
    - %d %b %Y %H:%M:%S
    - 23 Feb 2021 16:01:25
    DLT 1 23 Feb 2021 16:01:25
    """
    words = input.split(" ")
    command = words[0]
    msg_num = words[1]
    date_str = " ".join(words[2:])
    if command != "DLT":
        return False
    if not validate_int(msg_num):
        return False
    if not validate_time(date_str):
        return False
    return True

def validate_edt(input):
    """
    Validate edit message input
    Format: EDT messagenumber timestamp message
    EDT 1 23 Feb 2021 16:01:25 message ajskdch hgsdc e 
    """
    words = input.split(" ")
    # print(words)
    if len(words) < 6:
        return False
    command = words[0]
    msg_num = words[1]
    date_str = " ".join(words[2:6])
    if command != "EDT":
        return False
    if not validate_int(msg_num):
        return False
    if not validate_time(date_str):
        return False
    if not words[6:]:
        return False
    return True

def validate_rdm(input):
    # RDM timestamp
    words = input.split(" ")
    if len(words) != 5:
        return False
    command = words[0]
    date_str = " ".join(words[1:5])
    if command != "RDM":
        return False
    if not validate_time(date_str):
        return False
    return True

def validate_atu(input):
    words = input.split(" ")
    if len(words) != 1:
        return False
    command = words[0]
    if command != "ATU":
        return False
    return True


    

if __name__ == "__main__":

    # tcp_port = generate_port()
    server_name, target_TCP_port = take_input()
    TCP_ADDR = (server_name, target_TCP_port)
    tcp_client = socket(AF_INET, SOCK_STREAM)
    tcp_client.connect(TCP_ADDR)
   
    try:
        connect(tcp_client)
    except KeyboardInterrupt:
        send_message("OUTX", tcp_client)
        



    # TODO: Stage 2
    # udp_client = socket(AF_INET, SOCK_DGRAM)
    # udp_client.bind(UDP_ADDR)
    # UDP_ADDR = (server_name, udp_port)

    
