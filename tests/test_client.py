import pytest

import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/Users/adamma/Documents/GitHub/websocket')

from client import *

def test_user_actions():
    
    # Invalide input 
    res, _ = user_actions("")
    assert(res == None)

    # MSG
    res, command = user_actions("MSG yeet")
    assert(command == "MSG")
    assert(res == "MSG yeet")

    # Correct MSG command No message body
    res, command = user_actions("MSG")
    assert(command == "MSG")
    assert(res == None)

    res, command = user_actions("MSG ")
    assert(command == "MSG")
    assert(res == None)


    # DLT
    # res, command = user_actions("DLT 1 23 Feb 2021 16:01:25")
    # assert(command == "DLT")
    # assert(res == "DLT 1 23 Feb 2021 16:01:25")



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

    res = validate_edt("EDT 1 23 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == True)

    res = validate_edt("EDT l 23 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == False)

    res = validate_edt("EDT 1 99 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == False)

    res = validate_edt("EDT 1 23 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == False)

    res = validate_edt("EDT 1 23 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == True)

    res = validate_edt("EDT 1 23 Feb 2021 16:01:25 asdcjh uiacdg ")
    assert(res == True)