#!/usr/bin/env python3

import pytest
from hypothesis import given, strategies as st
from serial_protocol import cobs


# Basic Encode Bytearray Tests
def test_encode_bytearray_return_type():
    """Encoding returns a byte array."""
    retval = cobs.encode_bytearray(bytearray([0x00]))
    assert isinstance(retval, bytearray) is True


def test_encode_bytearray_invalid_input_types():
    """A type error is raised for invalid types"""
    with pytest.raises(TypeError):
        cobs.encode_bytearray(1)
        cobs.encode_bytearray(3.14)
        cobs.encode_bytearray([0, 0])
        cobs.encode_bytearray({"key": 0})


def test_encode_bytearray_empty_input():
    """Encoding an empty array should raise an exception"""
    with pytest.raises(ValueError):
        assert cobs.encode_bytearray(bytearray([]))


def test_encode_bytearray_single_zero():
    """Encoding a single 0x00 byte array"""
    data = bytearray([0x00])
    expected = bytearray([0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_bytearray_singe_nonzero():
    """Encoding a single non-zero byte array"""
    data = bytearray([0x18])
    expected = bytearray([0x02, 0x18, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_bytearray_no_zeros():
    """Encoding a simple byte array that contains no zeros"""
    data = bytearray([0x01, 0x02, 0x03])
    expected = bytearray([0x04, 0x01, 0x02, 0x03, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_bytearray_non_leading_zeros():
    """Encoding a byte array that doesn't have a leading zeros"""
    data = bytearray([0x01, 0x02, 0x00, 0x03, 0x00])
    expected = bytearray([0x03, 0x01, 0x02, 0x02, 0x03, 0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_bytearray_leading_zero():
    """Encoding a byte array that has a leading zero"""
    data = bytearray([0x00, 0x11, 0x11, 0x00, 0x22, 0x22, 0x00])
    expected = bytearray([0x01, 0x03, 0x11, 0x11, 0x03, 0x22, 0x22, 0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


# Advanced Encoding Bytearray Tests
def test_encode_bytearray_long_array():
    """Tests encoding 256-byte data sequence"""
    data = bytearray(list(range(0, 256)))
    expected = bytearray([0x01, 0xFF] + list(range(1, 255)) +
                         [0x02, 0xFF, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_bytearray_max_nonzero_block():
    """Tests encoding exactly 254 bytes before a zero"""
    data = bytearray(list(range(1, 256)) + [0x00])
    expected = bytearray([0xFF] + list(range(1, 255)) +
                         [0x02, 0xFF, 0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_bytearray_large_data():
    """Test encoding a large dataset (512 bytes)"""
    data = bytearray([i % 256 for i in range(512)])
    encoded = cobs.encode_bytearray(data)
    assert cobs.decode(encoded) == data  # Round-trip test


def test_encode_bytearray_round_trip():
    """Ensure encoding then decoding returns the original data"""
    data = bytearray([0x00, 0x01, 0x02, 0x03, 0x00,
                      0xFF, 0x00, 0x00, 0x10, 0x00])
    assert cobs.decode(cobs.encode_bytearray(data)) == data


def test_encode_bytearray_multiple_zeros_simple():
    """Tests encoding multiple zero bytes in a small dataset (< 10 bytes)"""
    data = bytearray([0x01, 0x02, 0x00, 0x00, 0x03, 0x04, 0x00])
    expected = bytearray([0x03, 0x01, 0x02, 0x01, 0x03,
                          0x03, 0x04, 0x01, 0x00])
    assert cobs.encode_bytearray(data) == expected


def test_encode_bytearray_multiple_zeros_complex():
    """Tests encoding multiple zero bytes occurring over a 255-byte chunk"""
    data = bytearray(list(range(1, 256)) + [0x00, 0x00, 0x00, 0xfe, 0xff])
    expected = bytearray([0xff] + list(range(1, 255)) +
                         [0x02, 0xff, 0x01, 0x01, 0x03] +
                         [0xfe, 0xff, 0x00])
    assert cobs.encode_bytearray(data) == expected


# Encoding Input Tests
def test_encode_input_types():
    """
    Ensure encode() correctly converts input formats before
    calling encode_bytearray()
    """
    data_list = [0x01, 0x02, 0x03]
    data_str = "01 02 03"
    data_bytes = bytearray([0x01, 0x02, 0x03])
    expected = bytearray([0x04, 0x01, 0x02, 0x03, 0x00])

    assert cobs.encode(data_list) == expected
    assert cobs.encode(data_str) == expected
    assert cobs.encode(data_bytes) == expected


def test_encode_invalid_inputs():
    """Ensure encode() raises TypeError for unsupported inputs"""
    with pytest.raises(TypeError):
        cobs.encode(123)
        cobs.encode(3.14)
        cobs.encode({"key": "value"})


# Advanced Encode/Decode Tests
@given(st.binary(min_size=1, max_size=512))
def test_cobs_encode_decode_round_trip_hypothesis(data):
    try:
        data = bytearray(data)
        encoded = cobs.encode_bytearray(data)
        decoded = cobs.decode_bytearray(encoded)
        assert decoded == data
    except Exception as e:
        print(f"Failed for input: {data.hex()} - Error: {str(e)}... "
              f"Encoded: {encoded.hex()}")
        raise
