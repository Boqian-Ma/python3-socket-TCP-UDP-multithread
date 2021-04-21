import pytest

import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/Users/adamma/Documents/GitHub/websocket')

from client import *

def test_validate_msg():
    res = validate_msg("MSG abc")
    assert(res == True)
    res = validate_msg("MSG abc achi")
    assert(res == True)
    res = validate_msg("MSG")
    assert(res == False)
    res = validate_msg("MSG ".rstrip())
    assert(res == False)

def test_validate_upd():
    res = validate_upd("UPD acdh ahdcia")
    assert(res == True)
    res = validate_msg("UPD abc")
    assert(res == False)

def test_validate_dlt():
    res = validate_dlt("DLT 1 23 Feb 2021 16:01:25")
    assert(res == True)
    # Invalide command
    res = validate_dlt("ABC 1 23 Feb 2021 16:01:25")
    assert(res == False)
    # Invalid message number
    res = validate_dlt("ABC  23 Feb 2021 16:01:25")
    assert(res == False)
    res = validate_dlt("ABC 23 Feb 2021 16:01:25")
    assert(res == False)
    # Invalid date
    res = validate_dlt("DLT 1 -1 Feb 2021 16:01:25")
    assert(res == False)
    # Invalid no date
    res = validate_dlt("DLT 1 Feb 2021 16:01:25")
    assert(res == False)
    # Invalid month
    res = validate_dlt("DLT 1 1 Fee 2021 16:01:25")
    assert(res == False)
    # Invalid year
    res = validate_dlt("DLT 1 1 Feb 20201 16:01:25")
    assert(res == False)
    # Invalid time format
    res = validate_dlt("DLT 1 1 Feb 2021 16-01:25")
    assert(res == False)

def test_validate_edt():
    # Format: EDT messagenumber timestamp message
    # correct input
    res = validate_edt("EDT 1 23 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == True)
    # incorrect message number
    res = validate_edt("EDT l 23 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == False)
    # incorrect date
    res = validate_edt("EDT 1 99 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == False)
    # incorrect month
    res = validate_edt("EDT 1 23 Fe 2021 16:01:25 asdcjh uiacdg ")
    assert(res == False)
    # incorrect year
    res = validate_edt("EDT 1 23 Feb 20200 16:01:25 asdcjh uiacdg ")
    assert(res == False)
    # incorrect time
    res = validate_edt("EDT 1 23 Feb 2021 :01:25 asdcjh uiacdg ")
    assert(res == False)


def test_validate_rdm():
    # Correct format
    res = validate_rdm("RDM 23 Feb 2021 16:01:25")
    assert(res == True)
    # incorrect date
    res = validate_edt("RDM -23 Feb 2021 16:01:25")
    assert(res == False)
    # incorrect month
    res = validate_edt("RDM 23 Meb 2021 16:01:25")
    assert(res == False)
    # incorrect year
    res = validate_edt("RDM 23 Feb 221 16:01:25")
    assert(res == False)
    # incorrect time
    res = validate_edt("RDM 23 Feb 200 16:-:25")
    assert(res == False)
    
def test_validate_atu():
    res = validate_atu("ATU")
    assert(res == True)
    res = validate_atu("ATU asdc")
    assert(res == False)

def test_parse_atu():
    response = "adam 127.0.0.1 udp/10000"
    list = parse_atu(response)
    assert(list == [{
        "username": "adam",
        "ip": "127.0.0.1",
        "udp_port": 10000
    }])

    response = "adam 127.0.0.1 udp/10000\nadam1 127.0.0.2 udp/10001"
    list = parse_atu(response)
    assert(list == [{
        "username": "adam",
        "ip": "127.0.0.1",
        "udp_port": 10000
    },
    {
        "username": "adam1",
        "ip": "127.0.0.2",
        "udp_port": 10001
    }])

def test_get_udp_dest():
    retstr = "UPD adam file.exe adam1"
    user_list = [{
        "username": "adam",
        "ip": "127.0.0.1",
        "udp_port": 10000
    },
    {
        "username": "adam1",
        "ip": "127.0.0.2",
        "udp_port": 10001
    }]
    ret = get_udp_dest(user_list, retstr)
    assert(ret == {
        "dest_ip": "127.0.0.1",
        "dest_port": 10000,
        "file_path": "file.exe"
    })

    retstr = "UPD jake file.exe adam1"
    ret = get_udp_dest(user_list, retstr)
    assert(ret == None)