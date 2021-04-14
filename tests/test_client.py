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

