#!/usr/bin/env python3

import pytest
from serial_protocol import cobs, utils


# Basic Encode Tests
def test_encode_no_zeros():
    """Encoding a simple byte array that contains no zeros"""
    bytes = bytearray([0x01, 0x02, 0x03])
    expected = bytearray([0x04, 0x01, 0x02, 0x03, 0x00])
    assert cobs.encode_bytearray(bytes) == expected


def test_encode_non_leading_zeros():
    """Encoding a simple byte array that doesn't have a leading zeros"""
    bytes = bytearray([0x01, 0x02, 0x00, 0x03, 0x00])
    expected = bytearray([0x03, 0x01, 0x02, 0x02, 0x03, 0x01, 0x00])
    assert cobs.encode_bytearray(bytes) == expected


def test_encode_leading_zero():
    """Encoding a byte array that has a leading zero"""
    data = bytearray([0x00, 0x11, 0x11, 0x00, 0x22, 0x22, 0x00])
    expected = bytearray([0x01, 0x03, 0x11, 0x11, 0x03, 0x22, 0x22, 0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_empty_bytearray():
    """Encoding an empty bytearray should return just the frame delimiter"""
    assert cobs.encode_bytearray(bytearray([])) == bytearray([0x01, 0x00])


def test_encode_single_zero():
    """Encoding a single zero should return [0x01, 0x00]"""
    data = bytearray([0x00])
    expected = bytearray([0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


# Advanced Encoding Tests
def test_encode_long_array():
    """Tests encoding 256-byte data sequence"""
    data = bytearray(list(range(0, 256)))
    expected = bytearray([0x01, 0xFF] + list(range(1, 255)) + [0x02, 0xFF, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_max_nonzero_block():
    """Tests encoding exactly 254 bytes before a zero"""
    data = bytearray(list(range(1, 256)) + [0x00])
    expected = bytearray([0xFF] + list(range(1, 255)) + [0x02, 0xFF, 0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_large_data():
    """Test encoding a large dataset (512 bytes)"""
    data = bytearray([i % 256 for i in range(512)])
    encoded = cobs.encode_bytearray(data)
    assert cobs.decode(encoded) == data  # Round-trip test


def test_encode_round_trip():
    """Ensure encoding then decoding returns the original data"""
    data = bytearray([0x00, 0x01, 0x02, 0x03, 0x00, 0xFF, 0x00, 0x00, 0x10, 0x00])
    assert cobs.decode(cobs.encode_bytearray(data)) == data


def test_encode_multiple_zeros_simple():
    """Tests encoding multiple zero bytes in a small dataset (< 10 bytes)"""
    data = bytearray([0x01, 0x02, 0x00, 0x00, 0x03, 0x04, 0x00])
    expected = bytearray([0x03, 0x01, 0x02, 0x01, 0x03, 0x03, 0x04, 0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_multiple_zeros_complex():
    """Tests encoding multiple zero bytes occurring over a 255-byte frame chunk"""
    data = bytearray(list(range(1, 256)) + [0x00, 0x00, 0x00, 0xfe, 0xff])
    expected = bytearray([0xff] + list(range(1, 255)) +
                         [0x02, 0xff, 0x01, 0x01, 0x03] +
                         [0xfe, 0xff, 0x00]
                         )

    assert cobs.encode_bytearray(data) == expected


def test_encode_input_types():
    """Ensure encode() correctly converts input formats before calling encode_bytearray"""
    data_list = [0x01, 0x02, 0x03]
    data_str = "01 02 03"
    data_bytes = bytearray([0x01, 0x02, 0x03])

    expected = cobs.encode_bytearray(bytearray([0x01, 0x02, 0x03]))  # Expected correct encoding

    assert cobs.encode(data_list) == expected
    assert cobs.encode(data_str) == expected
    assert cobs.encode(data_bytes) == expected


def test_encode_invalid_inputs():
    """Ensure encode() raises TypeError for unsupported inputs"""
    with pytest.raises(TypeError):
        cobs.encode(123)  # Integer is not valid
        cobs.encode_bytearray(123)

    with pytest.raises(TypeError):
        cobs.encode(3.14)  # Float is not valid
        cobs.encode_bytearray(3.14)

    with pytest.raises(TypeError):
        cobs.encode({"key": "value"})  # Dictionary is not valid
        cobs.encode_bytearray({"key": "value"})

    with pytest.raises(TypeError):
        cobs.encode_bytearray([0x01, 0x02, 0x03])

    with pytest.raises(TypeError):
        cobs.encode_bytearray("01 02 03")
