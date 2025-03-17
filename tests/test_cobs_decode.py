#!/usr/bin/env python3

import pytest
from serial_protocol import cobs, utils


# Basic Decode Bytearray Tests
def test_decode_bytearray_return_type():
    """Decoding returns a byte array."""
    retval = cobs.decode_bytearray(bytearray([0x01, 0x00]))
    assert isinstance(retval, bytearray) is True


def test_decode_bytearray_invalid_input_types():
    """A type error is raised for invalid types"""
    with pytest.raises(TypeError):
        cobs.decode_bytearray(1)
        cobs.decode_bytearray(3.14)
        cobs.decode_bytearray([0, 0])
        cobs.decode_bytearray({"key": 0})


def test_decode_bytearray_short_input():
    """Decoding an empty array should raise an exception"""
    with pytest.raises(ValueError):
        assert cobs.decode_bytearray(bytearray([]))
        assert cobs.decode_bytearray(bytearray([0x00]))


def test_decode_bytearray_single_zero():
    """Decoding an array that unencoded has a single zero"""
    data = bytearray([0x01, 0x00])
    expected = bytearray([0x00])
    assert cobs.decode_bytearray(data) == expected

    with pytest.raises(ValueError):
        cobs.decode_bytearray(bytearray([0x01, 0x01]))


def test_decode_bytearray_no_zeros():
    """Decoding an array that unencoded has no leading zero"""
    data = bytearray([0x04, 0x01, 0x02, 0x03, 0x00])
    expected = bytearray([0x01, 0x02, 0x03])
    assert cobs.decode_bytearray(data) == expected


def test_decode_bytearray_non_leading_zeros():
    """Decoding an array that unencoded zero but aren't leading"""
    data = bytearray([0x03, 0x01, 0x02, 0x02, 0x03, 0x01, 0x00])
    expected = bytearray([0x01, 0x02, 0x00, 0x03, 0x00])
    assert cobs.decode_bytearray(data) == expected


def test_decode_bytearray_leading_zero():
    """Decoding an array that unencoded has a leading zero plus other zeros"""
    data = bytearray([0x01, 0x03, 0x11, 0x11, 0x03, 0x22, 0x22, 0x01, 0x00])
    expected = bytearray([0x00, 0x11, 0x11, 0x00, 0x22, 0x22, 0x00])
    assert cobs.decode_bytearray(data) == expected


# Advanced Decode Bytearray Test
def test_decode_bytearray_long_array():
    """Tests decoding 256-byte data sequence"""
    data = bytearray([0x01, 0xFF] + list(range(1, 255)) + [0x02, 0xFF, 0x00])
    expected = bytearray(list(range(0, 256)))
    assert cobs.decode_bytearray(data) == expected


def test_decode_bytearray_max_nonzero_block():
    """Tests decoding exactly 254 bytes before a zero"""
    data = bytearray([0xFF] + list(range(1, 255)) + [0x02, 0xFF, 0x01, 0x00])
    expected = bytearray(list(range(1, 256)) + [0x00])
    assert cobs.decode_bytearray(data) == expected


def test_decode_bytearray_large_data():
    """Test decoding a large dataset (512 bytes)"""
    data = bytearray([i % 256 for i in range(512)])
    encoded = cobs.encode(data)
    assert cobs.decode_bytearray(encoded) == data  # Round-trip test


def test_decode_bytearray_round_trip():
    """Ensure decoding an encoded value returns the original data"""
    data = bytearray([0x00, 0x01, 0x02, 0x03, 0x00, 0xFF, 0x00,
                      0x00, 0x10, 0x00])
    assert cobs.decode_bytearray(cobs.encode(data)) == data


def test_decode_bytearray_round_trip_random():
    """Ensure encoding then decoding a randomized dataset works"""
    import random
    data = bytearray(random.randint(0, 255) for _ in range(1000))
    assert cobs.decode_bytearray(cobs.encode(data)) == data


def test_decode_bytearray_multiple_zeros_simple():
    """Tests decoding multiple zero bytes in a small dataset (< 10 bytes)"""
    data = bytearray([0x03, 0x01, 0x02, 0x01, 0x03, 0x03, 0x04, 0x01, 0x00])
    expected = bytearray([0x01, 0x02, 0x00, 0x00, 0x03, 0x04, 0x00])
    assert cobs.decode_bytearray(data) == expected


def test_decode_bytearray_multiple_zeros_complex():
    """Tests decoding multiple zero bytes occurring over a 255-byte chunk"""
    data = bytearray([0xff] + list(range(1, 255)) +
                     [0x02, 0xff, 0x01, 0x01, 0x03] +
                     [0xfe, 0xff, 0x00])
    expected = bytearray(list(range(1, 256)) + [0x00, 0x00, 0x00, 0xfe, 0xff])
    assert cobs.decode_bytearray(data) == expected


# Invalid COBS Encoding Array Tests
def test_decode_bytearray_missing_frame_delimiter():
    """Frame delimiter must be present at end of data"""
    with pytest.raises(ValueError):
        cobs.decode_bytearray(bytearray([0x03, 0x01, 0x02]))


def test_decode_bytearray_more_than_one_delimiter():
    """Test invalid encoding if more than one delimiter present"""
    with pytest.raises(ValueError):
        cobs.decode_bytearray(bytearray([0x03, 0x00, 0x00]))


def test_decode_bytearray_invalid_zero_marker():
    """Test invalid zero marker encodings"""
    data1 = bytearray([0x03, 0x01, 0x00])
    data2 = bytearray([0x02, 0x01, 0x02, 0x00])
    with pytest.raises(ValueError):
        cobs.decode_bytearray(data1)
        cobs.decode_bytearray(data2)


# Decoding Input Tests
def test_decode_input_types():
    """
    Ensure decode() correctly converts input formats before
    calling decode_bytearray
    """
    data = bytearray([0x04, 0x01, 0x02, 0x03, 0x00])
    expected = bytearray([0x01, 0x02, 0x03])

    assert cobs.decode(list(data)) == expected
    assert cobs.decode(bytearray(data)) == expected
    assert cobs.decode(utils.bytearray_to_hexstring(data)) == expected


def test_decode_invalid_inputs():
    """Ensure decode() raises TypeError for unsupported inputs"""
    with pytest.raises(TypeError):
        cobs.decode(123)  # Integer is not valid
        cobs.decode(3.14)  # Float is not valid
        cobs.decode({"key": "value"})  # Dictionary is not valid

