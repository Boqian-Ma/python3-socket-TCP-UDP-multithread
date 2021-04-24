from socket import *
import time
import random
import argparse
import datetime
import threading
import os.path
import errno

FORMAT = "utf-8"    
WELCOME = "Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT):"
DATE_FORMAT = "%d %b %Y %H:%M:%S"
CURRENT_USER = ""
LOGIN = False

# UDP variables
UDP_PACKET_SIZE = 4096  # Define packet size for P2P transfer
T_LOCK=threading.Condition()
UDP_SERVER = None
# one for total size, one for file name, one to notify new file
UDP_MESSAGE_OFFSET = 2

def take_input():
    '''
    Parse command line input
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("server_name", type=str, help="Enter server name.")
    parser.add_argument("tcp_port", type=int,  help="Enter a TCP port number for messaging.")
    parser.add_argument("udp_port", type=int, help="Enter an UDP port number for P2P video sharing.")   
    args = parser.parse_args()
    server_name = args.server_name
    tcp_port = args.tcp_port
    udp_port = args.udp_port
    return server_name, tcp_port, udp_port

def send_message(msg, tcp_client):
    '''
    Encode and send a message to server via TCP

    arg1: msg <string> the message string we wish to send to server
    arg2: tcp_client <socket> the socket we are sending the message from

    Returns: 
        response: <string> decoded response message from server
    '''
    message = msg.encode(FORMAT)
    tcp_client.send(message)
    response = tcp_client.recv(2048).decode(FORMAT)
    return response

def connect(tcp_client, UDP_ADDR):
    """
    Main loop:
        Client login
        Create P-2-P UDP server
        Send Requests to Server
    """
    global CURRENT_USER
    global LOGIN

    connected = False
    udp_server_on = False
    udp_server = None
    # Login 
    while not connected:
        # Get login details
        print("[WELCOME] Please Login...")
        valid_user_info = False

        while valid_user_info == False:
            username = input("Enter User Name: ").strip()
            password = input("Enter Password: ").strip()
            if len(username.split(" ")) == 1 and len(password.split(" ")) == 1:
                valid_user_info = True
            else: 
                print("[ERROR] No space in username and password.")
        
        package = username + " " + password + " " + str(UDP_ADDR[1])
        # Send login details
        response = send_message(package, tcp_client)
        if str(response) == "LOGIN: SUCCESS":
            connected = True
            print("Login Succeed...")
            CURRENT_USER = username
        elif str(response) == "LOGIN: FAILED": # Failed attampt
            print("[ERROR] Please Check Login Details...")
        else: # Reached maximum attampt
            words = str(response).split(" ")
            sec_left = words[-1]
            print("[ERROR] Reached Maximum Attampts, Please Try Again in " + sec_left + " Seconds\nShutting Down...")
            break
    
    # Start P2P server
    while connected and not udp_server_on:
        # start udp server thread
        udp_server_setup(UDP_ADDR)
        udp_server_on = True

    # Main Loop
    while connected and udp_server_on: 
        LOGIN = True
        input_msg = str(input(WELCOME))
        # Validate user input 
        retstr, command = user_actions(input_msg)
        if retstr is None:
            print("[ERROR] Invalid Command, Please Try Again...")
            continue
        if command == "OUT":
            # Log out
            connected = False
            _ = send_message(retstr + " " + CURRENT_USER, tcp_client)
            print(f"Logging Out...")
            continue
        
        retstr += " " + CURRENT_USER
        if command == "UPD":
            # Send ATU
            retstr = "ATU " + CURRENT_USER
            response = send_message(retstr, tcp_client)
            # parse userlist
            handled_connection = handle_upd(response, input_msg)
            continue
            # create threadings

        response = send_message(retstr, tcp_client)
        print(f"[SERVER RESPONSE] {response}")
    return

def udp_server_setup(UDP_ADDR):
    """
    Set up udp client server thread

    arg1: UDP_ADDR <tuple> A tuple of (ip, udp port)
    """
    global UDP_SERVER

    print("[SETTING UP UDP SERVER]")
    print(".")
    print("..")
    print("...")
    UDP_SERVER = socket(AF_INET, SOCK_DGRAM)
    UDP_SERVER.bind(UDP_ADDR)
    print(f"[UDP SERVER LISTENING] Server is listening on {UDP_ADDR[0]}:{UDP_ADDR[1]}")
    recv_thread = threading.Thread(name="RecvHandler", target=upd_recv_handler)
    recv_thread.daemon = True
    recv_thread.start()

def upd_recv_handler():
    '''
    Handle P2P file receive 
    '''
    global T_LOCK
    global UDP_SERVER
    global CURRENT_USER
    
    while True:
        UDP_SERVER.settimeout(None)

        # server first get file_name and user_name of who transfered
        file_name_user_name, clientAddress = UDP_SERVER.recvfrom(UDP_PACKET_SIZE)
        file_name_user_name = file_name_user_name.decode(FORMAT)
        
        file_name = file_name_user_name.split(" ")[0]
        from_user_name = file_name_user_name.split(" ")[1]

        cur_user_dir = CURRENT_USER + "/" + file_name
        # Open file
        if not os.path.exists(os.path.dirname(cur_user_dir)):
            try:
                os.makedirs(os.path.dirname(cur_user_dir))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    print("[ERROR] Failed to create directory to save files")
                    return

        file = open(cur_user_dir, "wb+")
        
        with T_LOCK:
            UDP_SERVER.settimeout(5)
            # receiving a file
            try:
                # number of paclets
                num_packets, clientAddress = UDP_SERVER.recvfrom(UDP_PACKET_SIZE)
            except ConnectionResetError:
                print(
                    "[ERROR] Port numbers not matching. Exiting. Next time enter same port numbers.")
                return
            except:
                print("[ERROR] Timeout or some other error")
                return
            num_packets = int(num_packets.decode(FORMAT))
            d = 0
            while num_packets != 0:
                data, clientbAddr = UDP_SERVER.recvfrom(UDP_PACKET_SIZE)
                dataS = file.write(data)
                d += 1
                num_packets = num_packets - 1            
            file.close()
            print(f"[FILE RECEIVED] Received {file_name} from {from_user_name}\n")
            print(WELCOME,end='')
            T_LOCK.notify()


def handle_upd(response, retstr):
    '''
    message format: "adam 127.0.0.1 udp/10000\n"
    Send 
    Returns
        True if file sent successfully
        False if file sent unsuccessfully
    '''
    if (response == "No Other Active Users"):
        return False

    user_list = parse_atu(response)
    dest_dict = get_udp_dest(user_list, retstr)
    if dest_dict is None:
        print ("[ERROR] No User Found")
        return False
    # check if file exists

    if not os.path.isfile(dest_dict["file_path"]):
        print ("[ERROR] File does not exist")
        return False
    # start a send thread
    send_thread = threading.Thread(name="UDPSendHandler",target=upd_send_handler, args=(dest_dict, ))
    send_thread.daemon = True
    send_thread.start()

def upd_send_handler(dest_dict):
    '''
    Handle UPD and transfers a file to another host

    arg1: dest_dict <dict> a dictionary containing destination ip and port

    Pre-cond: file already exists
    '''
    global T_LOCK
    global UDP_SERVER

    UDP_CLIENT = socket(AF_INET, SOCK_DGRAM)
    
    with T_LOCK:
        file_stat = os.stat(dest_dict["file_path"])
        file_size = file_stat.st_size  # number of packets

        num_packets = int(file_size / UDP_PACKET_SIZE)
        num_packets = num_packets + UDP_MESSAGE_OFFSET
        num_packets_str = str(num_packets)
        num_packets_str_encode = num_packets_str.encode(FORMAT)
        clientAddr = (dest_dict["dest_ip"], dest_dict["dest_port"])

        # Send file name
        UDP_CLIENT.sendto((dest_dict["file_path"] + " " + CURRENT_USER).encode(FORMAT), clientAddr)
        # Send number of packets
        UDP_CLIENT.sendto(num_packets_str_encode, clientAddr)

        # Create file
        file = open(dest_dict["file_path"], "rb")
        check = int(num_packets)

        # Send file body
        while check != 0:
            RunS = file.read(UDP_PACKET_SIZE)
            UDP_CLIENT.sendto(RunS, clientAddr)
            check -= 1
        
        path = dest_dict["file_path"]
        username = dest_dict["username"]
        print(f"[FILE SENT SUCCESSFULLY] { path } has been sent to { username }...")
        UDP_CLIENT.close()
        T_LOCK.notify()
        

def get_udp_dest(user_list, input_msg):
    """
    Get destination IP and Port

    arg1: user_list <list<dict>>>: List of active users
    arg2: input_msg <string>: UPD Obi-wan lecture1.mp4 "server username"

    Returns:
        None if user is not active
        dict <dict>: Destination machins ip and port
    """
    words = input_msg.split(" ")

    dest_username = words[1]
    file_path = words[2]

    dest_ip = None
    dest_port = None
    for u in user_list:
        if u["username"] == dest_username:
            dest_ip = u["ip"]
            dest_port = u["udp_port"]

    if (dest_ip is None or dest_port is None):
        return None
    dict = {
        "dest_ip": dest_ip,
        "dest_port": dest_port,
        "file_path": file_path,
        "username": dest_username
    }
    return dict


def parse_atu(response):
    '''
    Parse ATU response message
    ATU message format: "adam 127.0.0.1 udp/10000\n"

    arg1: responses <string>: a string containing ATU response

    Returns
        users: <dict> Dictionary containing all active users

    Pre-cond: 
        response contains at least one entry
    '''

    if ("\n" in response):
        entries = response.split("\n")
    else: 
        entries = [response]
    
    user_list = []
    print(entries)
    for e in entries:
        entry = e.split(" ")
        user_list.append({
            "username": entry[0],
            "ip": entry[1],
            "udp_port": int(entry[2][4:])
        })
    return user_list

def user_actions(user_input):
    """
    Process user actions

    arg1: user_input <string> Raw user input from command line

    MSG: Post Message
    DLT: Delete Message
    EDT: Edit Message
    RDM: Read Message
    ATU: Display active users
    OUT: Log out and UPD: Upload file

    Returns:
        ret1: Processed request string <string>
        ret2: Command <string>
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
    elif command == "UPD":
        if validate_upd(user_input):
            retstr = user_input 
    elif command == "OUT":
        retstr = command
    else:
        retstr = None

    return retstr, command


def validate_int(str):
    """
    Given a string, validate if its an integer or not

    arg1: string <string> A string we wish to check

    Returns
        True is its an integer
        None is not
    """
    try: 
        int(str)
    except ValueError:
        return False
    return True

def validate_time(str):
    """
    Validate if a string is in the proper date format

    arg1: str <string> A string we wish to check

    Returns:
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
    Format: MSG MESSAGE

    arg1: str <string> A string we wish to check

    Returns:
        True if string is in correct MSG format
        None if string in not
    """
    words = input.split(" ")
    command = words[0]
    msg = words[1:]
    # print(f"msg = {msg}")
    if command != "MSG":
        return False
    if not msg:
        return False
    return True

def validate_dlt(input):
    """
    Validate delete message input
    
    Format example: DLT 1 23 Feb 2021 16:01:25

    arg1: str <string> A string we wish to check

    Returns:
        True if string is in correct DLT format
        None if string in not
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
    Example: EDT 1 23 Feb 2021 16:01:25 message

    arg1: str <string> A string we wish to check

    Returns:
        True if string is in correct DLT format
        None if string in not
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
    """
    Validate RDM message input

    arg1: str <string> A string we wish to check

    Returns:
        True if string is in correct RDM format
        None if string in not
    """
    
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
    """
    Validate ATU message input

    arg1: str <string> A string we wish to check

    Returns:
        True if string is in correct ATU format
        None if string in not
    """
    words = input.split(" ")
    if len(words) != 1:
        return False
    command = words[0]
    if command != "ATU":
        return False
    return True

def validate_upd(input):
    """
    Validate UPD message input

    arg1: str <string> A string we wish to check

    Returns:
        True if string is in correct UPD format
        None if string in not
    """

    words = input.split(" ")
    if len(words) != 3:
        return False
    
    command = words[0]

    if command != "UPD":
        return False
    return True


if __name__ == "__main__":

    # Take command line input
    server_name, target_TCP_port, local_UDP_port = take_input()

    UDP_ADDR = (server_name, local_UDP_port)
    TCP_ADDR = (server_name, target_TCP_port)

    tcp_client = socket(AF_INET, SOCK_STREAM)
    tcp_client.connect(TCP_ADDR)
    
    try:
        connect(tcp_client, UDP_ADDR)
    except KeyboardInterrupt:
        # Close connection
        send_message("OUTX" + " " + CURRENT_USER, tcp_client)

    
