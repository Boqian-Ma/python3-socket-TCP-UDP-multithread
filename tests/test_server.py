import pytest

import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/Users/adamma/Documents/GitHub/websocket')

from server import *


USERS = [
    {
        "username": "boqian",
        "password": "123",
        "login": True,
        "tcp_port": "0",
        "udp_port": "1",
        "active_since": None,
        "ip": "1.1.1.1"
    },
    {
            "username": "adam",
            "password": "123",
            "login": True,
            "tcp_port": "0",
            "udp_port": "1",
            "active_since": None,
            "ip": "1.1.1.1"
    }
]

# def test_handle_aut():
#     response = handle_aut(USERS)
#     assert(response == "boqian 1.1.1.1 udp/1\nadam 1.1.1.1 udp/1")

#     response = handle_aut([])
#     assert(response == "No Active Users")
