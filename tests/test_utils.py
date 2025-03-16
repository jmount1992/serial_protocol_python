#!/usr/bin/env python3

import pytest
from serial_protocol import utils


def test_hexstring_to_bytearray():
    assert utils.hexstring_to_bytearray("00 11 22") == bytearray([0x00, 0x11, 0x22])
    assert utils.hexstring_to_bytearray("0x00 0x11 0x22") == bytearray([0x00, 0x11, 0x22])


def test_bytearray_to_hexstring():
    assert utils.bytearray_to_hexstring(bytearray([0x00, 0x11, 0x22])) == "0x00 0x11 0x22"
    assert utils.bytearray_to_hexstring(bytearray([0x00, 0x11, 0x22]), False) == "00 11 22"


def test_is_0x_format():
    assert utils.is_0x_format("0x00 0x11 0x22") is True
    assert utils.is_0x_format("00 11 22") is False
    with pytest.raises(ValueError):
        utils.is_0x_format("00 0x11 22")


def test_bytearray_to_decstring():
    assert utils.bytearray_to_decstring(bytearray([0, 17, 255])) == "000 017 255"
    assert utils.bytearray_to_decstring(bytearray([1, 2, 3, 4, 5])) == "001 002 003 004 005"
