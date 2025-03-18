#!/usr/bin/env python3

import struct
import pytest
from serial_protocol import utils

# Test Enumerations
@pytest.mark.parametrize("enum_class, value, expected", [
    (utils.MaxUintValues, 255, utils.MaxUintValues.UINT8_MAX),
    (utils.MaxUintValues, 65535, utils.MaxUintValues.UINT16_MAX),
    (utils.MaxUintValues, 4294967295, utils.MaxUintValues.UINT32_MAX),
    (utils.FloatByteSize, 4, utils.FloatByteSize.FLOAT32),
    (utils.FloatByteSize, 8, utils.FloatByteSize.FLOAT64)
])
def test_enum_values(enum_class, value, expected):
    assert enum_class(value) == expected
    assert expected.value == value


# Test Utility Functions
def test_hexstring_to_bytearray():
    data = bytearray([0x00, 0x11, 0x22])
    assert utils.hexstring_to_bytearray("00 11 22") == data
    assert utils.hexstring_to_bytearray("0x00 0x11 0x22") == data


def test_bytearray_to_hexstring():
    data = bytearray([0x00, 0x11, 0x22])
    assert utils.bytearray_to_hexstring(data) == "0x00 0x11 0x22"
    assert utils.bytearray_to_hexstring(data, False) == "00 11 22"


def test_is_0x_format():
    assert utils.is_0x_format("0x00 0x11 0x22") is True
    assert utils.is_0x_format("00 11 22") is False
    with pytest.raises(ValueError):
        utils.is_0x_format("00 0x11 22")


def test_bytearray_to_decstring():
    data1 = bytearray([0, 17, 255])
    data2 = bytearray([1, 2, 3, 4, 5])
    assert utils.bytearray_to_decstring(data1) == "000 017 255"
    assert utils.bytearray_to_decstring(data2) == "001 002 003 004 005"


# Test Integer to Bytearray Conversion (Valid Cases)
@pytest.mark.parametrize("value, max_value, expected", [
    (8, utils.MaxUintValues.UINT8_MAX, bytearray([0x08])),
    (255, utils.MaxUintValues.UINT8_MAX, bytearray([0xFF])),
    (8, utils.MaxUintValues.UINT16_MAX, bytearray([0x08, 0x00])),
    (65535, utils.MaxUintValues.UINT16_MAX, bytearray([0xFF, 0xFF])),
    (8, utils.MaxUintValues.UINT32_MAX, bytearray([0x08, 0x00, 0x00, 0x00])),
    (4294967295, utils.MaxUintValues.UINT32_MAX, bytearray([0xFF, 0xFF, 0xFF, 0xFF]))
])
def test_int_to_bytearray(value, max_value, expected):
    """Ensure integer-to-bytearray conversion works for various max values."""
    assert utils.int_to_bytearray(value, max_value) == expected


# Test Invalid Integer Values (Out of Range)
@pytest.mark.parametrize("value, max_value", [
    (-1, utils.MaxUintValues.UINT8_MAX),  # Below 0 (negative)
    (256, utils.MaxUintValues.UINT8_MAX),  # Exceeds UINT8 max
    (65536, utils.MaxUintValues.UINT16_MAX),  # Exceeds UINT16 max
    (4294967296, utils.MaxUintValues.UINT32_MAX)  # Exceeds UINT32 max
])
def test_int_to_bytearray_invalid(value, max_value):
    """Ensure invalid integer values raise ValueError."""
    with pytest.raises(ValueError):
        utils.int_to_bytearray(value, max_value)


# Test Invalid MaxUintValues (Invalid Enum or Value)
@pytest.mark.parametrize("value, max_value", [
    (8, 999999),  # Invalid max value
    (8, "UINT8_MAX"),  # Wrong type
    (8, None),  # NoneType
])
def test_int_to_bytearray_invalid_max_value(value, max_value):
    """Ensure invalid max_value raises ValueError."""
    with pytest.raises(ValueError):
        utils.int_to_bytearray(value, max_value)


# Test Float to Bytearray Conversion (Valid Cases)
@pytest.mark.parametrize("value, num_bytes, expected", [
    (3.14, utils.FloatByteSize.FLOAT32, bytearray(struct.pack('f', 3.14))),
    (3.14, utils.FloatByteSize.FLOAT64, bytearray(struct.pack('d', 3.14))),
    (-1.5, utils.FloatByteSize.FLOAT32, bytearray(struct.pack('f', -1.5))),
    (0.0, utils.FloatByteSize.FLOAT64, bytearray(struct.pack('d', 0.0)))
])
def test_float_to_bytearray(value, num_bytes, expected):
    """Ensure float-to-bytearray conversion works for 4 and 8 byte formats."""
    assert utils.float_to_bytearray(value, num_bytes) == expected


# Test Invalid Float Byte Sizes
@pytest.mark.parametrize("value, num_bytes", [
    (3.14, 2),  # Not 4 or 8
    (3.14, 16),  # Not 4 or 8
    (3.14, "FLOAT32"),  # Wrong type
    (3.14, None),  # NoneType
])
def test_float_to_bytearray_invalid(value, num_bytes):
    """Ensure invalid float sizes raise ValueError."""
    with pytest.raises(ValueError):
        utils.float_to_bytearray(value, num_bytes)