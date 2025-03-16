#!/usr/bin/env python3

import pytest
from serial_protocol import cobs, utils


# ✅ **Basic Decode Tests**
def test_decode_no_zeros():
    encoded = bytearray([0x04, 0x01, 0x02, 0x03, 0x00])
    expected = bytearray([0x01, 0x02, 0x03])
    assert cobs.decode_bytearray(encoded) == expected


def test_decode_non_leading_zeros():
    encoded = bytearray([0x03, 0x01, 0x02, 0x02, 0x03, 0x01, 0x00])
    expected = bytearray([0x01, 0x02, 0x00, 0x03, 0x00])
    assert cobs.decode_bytearray(encoded) == expected


def test_decode_single_zero():
    """Decoding [0x01, 0x00] should return [0x00]"""
    data = bytearray([0x01, 0x00])
    expected = bytearray([0x00])
    assert cobs.decode_bytearray(data) == expected


# ✅ **Advanced Decode Tests**
def test_decode_bytearray():
    encoded = bytearray([0x01, 0x03, 0x11, 0x11, 0x03, 0x22, 0x22, 0x01, 0x00])
    expected = bytearray([0x00, 0x11, 0x11, 0x00, 0x22, 0x22, 0x00])
    assert cobs.decode_bytearray(encoded) == expected


def test_decode_long_array():
    """Tests decoding 256-byte data sequence"""
    encoded = bytearray([0x01, 0xFF] + list(range(1, 255)) + [0x02, 0xFF, 0x00])
    expected = bytearray(list(range(0, 256)))
    assert cobs.decode_bytearray(encoded) == expected


def test_decode_max_nonzero_block():
    """Tests decoding exactly 254 bytes before a zero"""
    data = bytearray([0xFF] + list(range(1, 255)) + [0x02, 0xFF, 0x01, 0x00])
    expected = bytearray(list(range(1, 256)) + [0x00])
    assert cobs.decode_bytearray(data) == expected


def test_decode_large_data():
    """Test decoding a large dataset (512 bytes)"""
    data = bytearray([i % 256 for i in range(512)])
    encoded = cobs.encode(data)
    assert cobs.decode_bytearray(encoded) == data  # Round-trip test


def test_decode_round_trip():
    """Ensure decoding an encoded value returns the original data"""
    data = bytearray([0x00, 0x01, 0x02, 0x03, 0x00, 0xFF, 0x00, 0x00, 0x10, 0x00])
    assert cobs.decode_bytearray(cobs.encode(data)) == data


def test_decode_round_trip_random():
    """Ensure encoding then decoding a randomized dataset works"""
    import random
    data = bytearray(random.randint(0, 255) for _ in range(1000))
    assert cobs.decode_bytearray(cobs.encode(data)) == data


def test_decode_multiple_zeros_simple():
    """Tests decoding multiple zero bytes in a small dataset (< 10 bytes)"""
    data = bytearray([0x03, 0x01, 0x02, 0x01, 0x03, 0x03, 0x04, 0x01, 0x00])
    expected = bytearray([0x01, 0x02, 0x00, 0x00, 0x03, 0x04, 0x00])
    assert cobs.decode_bytearray(data) == expected


def test_decode_multiple_zeros_complex():
    """Tests decoding multiple zero bytes occurring over a 255-byte frame chunk"""
    data = bytearray([0xff] + list(range(1, 255)) +
                         [0x02, 0xff, 0x01, 0x01, 0x03] +
                         [0xfe, 0xff, 0x00]
                         )
    expected = bytearray(list(range(1, 256)) + [0x00, 0x00, 0x00, 0xfe, 0xff])

    assert cobs.decode_bytearray(data) == expected


def test_decode_input_types():
    """Ensure decode() correctly converts input formats before calling decode_bytearray"""
    encoded_bytes = cobs.encode_bytearray(bytearray([0x01, 0x02, 0x03]))

    expected = cobs.decode_bytearray(encoded_bytes)  # Expected correct decoding

    assert cobs.decode(list(encoded_bytes)) == expected
    assert cobs.decode(bytearray(encoded_bytes)) == expected
    assert cobs.decode(" ".join(f"{b:02x}" for b in encoded_bytes)) == expected


def test_decode_invalid_inputs():
    """Ensure encode() raises TypeError for unsupported inputs"""
    with pytest.raises(TypeError):
        cobs.decode(123)  # Integer is not valid
        cobs.decode_bytearray(123)

    with pytest.raises(TypeError):
        cobs.decode(3.14)  # Float is not valid
        cobs.decode_bytearray(3.14)

    with pytest.raises(TypeError):
        cobs.decode({"key": "value"})  # Dictionary is not valid
        cobs.decode_bytearray({"key": "value"})

    with pytest.raises(TypeError):
        cobs.decode_bytearray([0x01, 0x02, 0x03])

    with pytest.raises(TypeError):
        cobs.decode_bytearray("01 02 03")