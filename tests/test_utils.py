#!/usr/bin/env python3

import struct
import pytest
from serial_protocol import utils

# --- Enum Tests ---


@pytest.mark.parametrize("enum_class, num_bytes, category, label,"
                         "format_char, max_value, is_uint, is_float", [
    (utils.ValueFormat.UINT8, 1, "uint", "uint8", None, 255, True, False),
    (utils.ValueFormat.UINT16, 2, "uint", "uint16", None, 65535, True, False),
    (utils.ValueFormat.UINT32, 4, "uint", "uint32", None, 4294967295, True, False),
    (utils.ValueFormat.FLOAT32, 4, "float", "float32", 'f', None, False, True),
    (utils.ValueFormat.FLOAT64, 8, "float", "float64", 'd', None, False, True),
])
def test_floatprecision_enum(enum_class, num_bytes, category, label,
                             format_char, max_value,
                             is_uint, is_float):
    assert enum_class.num_bytes == num_bytes
    assert enum_class.category == category
    assert enum_class.label == label
    assert enum_class.format_char == format_char
    assert enum_class.max_value == max_value
    assert enum_class.is_uint() == is_uint
    assert enum_class.is_float() == is_float
    assert str(enum_class) == label


def test_coerce_from_label():
    assert utils.ValueFormat.coerce("uint8") == utils.ValueFormat.UINT8
    assert utils.ValueFormat.coerce("float32") == utils.ValueFormat.FLOAT32


def test_max_value_for_uints():
    for vf in utils.ValueFormat:
        if vf.is_uint():
            assert vf.max_value == (2 ** (vf.num_bytes * 8)) - 1
        else:
            assert vf.max_value is None


# --- Hex/Dec String Conversion ---
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
    assert utils.bytearray_to_decstring(bytearray([0, 17, 255])) == "000 017 255"
    assert utils.bytearray_to_decstring(bytearray([1, 2, 3, 4, 5])) == "001 002 003 004 005"


# --- Integer Conversion ---
@pytest.mark.parametrize("value, format, expected", [
    (0, utils.ValueFormat.UINT8, bytearray([0x00])),
    (8, utils.ValueFormat.UINT8, bytearray([0x08])),
    (255, utils.ValueFormat.UINT8, bytearray([0xFF])),
    (0, utils.ValueFormat.UINT16, bytearray([0x00, 0x00])),
    (8, utils.ValueFormat.UINT16, bytearray([0x08, 0x00])),
    (65535, utils.ValueFormat.UINT16, bytearray([0xFF, 0xFF])),
    (0, utils.ValueFormat.UINT32, bytearray([0x00, 0x00, 0x00, 0x00])),
    (8, utils.ValueFormat.UINT32, bytearray([0x08, 0x00, 0x00, 0x00])),
    (4294967295, utils.ValueFormat.UINT32, bytearray([0xFF, 0xFF, 0xFF, 0xFF]))
])
def test_int_to_bytearray(value, format, expected):
    assert utils.int_to_bytearray(value, format) == expected


@pytest.mark.parametrize("value, max_value", [
    (-1, utils.ValueFormat.UINT8),
    (256, utils.ValueFormat.UINT8),
    (65536, utils.ValueFormat.UINT16),
    (4294967296, utils.ValueFormat.UINT32)
])
def test_int_to_bytearray_invalid(value, max_value):
    with pytest.raises(ValueError):
        utils.int_to_bytearray(value, max_value)


@pytest.mark.parametrize("value, max_value", [
    (8, 999999),
    (8, "UINT8"),
    (8, None)
])
def test_int_to_bytearray_invalid_max_value(value, max_value):
    with pytest.raises(ValueError):
        utils.int_to_bytearray(value, max_value)


# --- Float Conversion ---
@pytest.mark.parametrize("value, precision, expected", [
    (3.14, utils.ValueFormat.FLOAT32, bytearray(struct.pack('f', 3.14))),
    (3.14, utils.ValueFormat.FLOAT64, bytearray(struct.pack('d', 3.14))),
    (-1.5, utils.ValueFormat.FLOAT32, bytearray(struct.pack('f', -1.5))),
    (0.0, utils.ValueFormat.FLOAT64, bytearray(struct.pack('d', 0.0)))
])
def test_float_to_bytearray(value, precision, expected):
    assert utils.float_to_bytearray(value, precision) == expected


@pytest.mark.parametrize("value, precision", [
    (3.14, 2),
    (3.14, 16),
    (3.14, "FLOAT32"),
    (3.14, None),
    (3.14, utils.ValueFormat.UINT8),
    (3.14, utils.ValueFormat.UINT16),
    (3.14, utils.ValueFormat.UINT32),
])
def test_float_to_bytearray_invalid(value, precision):
    with pytest.raises(ValueError):
        utils.float_to_bytearray(value, precision)


@pytest.mark.parametrize("value, precision", [
    (bytearray(struct.pack('f', 3.14)), utils.ValueFormat.FLOAT32),
    (bytearray(struct.pack('d', 3.14)), utils.ValueFormat.FLOAT64)
])
def test_bytearray_to_float(value, precision):
    result = utils.bytearray_to_float(value, precision)
    assert isinstance(result, float)
    assert abs(result - 3.14) < 1e-6
