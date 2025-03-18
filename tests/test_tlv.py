#!/usr/bin/env python3

import pytest
import struct
from serial_protocol import tlv, utils


# Test Basic TLV Constructor
def test_tlv_packet_constructor_without_args():
    packet = tlv.tlv_packet()
    assert isinstance(packet, tlv.tlv_packet) is True
    assert packet.max_data_length.value == 255
    assert packet.max_data_value.value == 255
    assert packet.float_byte_size.value == 4


# Test Valid Constructor Arguments
@pytest.mark.parametrize("attr, enumval, intval", [
    ("max_data_length", utils.MaxUintValues.UINT8_MAX, 255),
    ("max_data_length", utils.MaxUintValues.UINT16_MAX, 65535),
    ("max_data_length", utils.MaxUintValues.UINT32_MAX, 4294967295),
    ("max_data_value", utils.MaxUintValues.UINT8_MAX, 255),
    ("max_data_value", utils.MaxUintValues.UINT16_MAX, 65535),
    ("max_data_value", utils.MaxUintValues.UINT32_MAX, 4294967295),
    ("float_byte_size", utils.FloatByteSize.FLOAT32, 4),
    ("float_byte_size", utils.FloatByteSize.FLOAT64, 8),
])
def test_tlv_packet_constructor_valid(attr, enumval, intval):
    """Ensure TLV packet constructor accepts valid values."""
    packet = tlv.tlv_packet(**{attr: enumval})
    assert getattr(packet, attr) == enumval
    assert getattr(getattr(packet, attr), "value") == intval


# Test Invalid Constructor Arguments
@pytest.mark.parametrize("attr, value", [
    ("max_data_length", 0),
    ("max_data_length", 256),
    ("max_data_length", 65534),
    ("max_data_value", 0),
    ("max_data_value", 256),
    ("max_data_value", 65534),
    ("float_byte_size", 0),
    ("float_byte_size", 5),
    ("float_byte_size", 9)
])
def test_tlv_packet_constructor_invalid(attr, value):
    """Ensure TLV packet constructor raises ValueError for invalid values."""
    with pytest.raises(ValueError):
        tlv.tlv_packet(**{attr: value})


# Test Property Getters & Setters
@pytest.mark.parametrize("attr, values", [
    ("max_data_length", [[utils.MaxUintValues.UINT8_MAX, 255],
                         [utils.MaxUintValues.UINT16_MAX, 65535],
                         [utils.MaxUintValues.UINT32_MAX, 4294967295]]),
    ("max_data_value", [[utils.MaxUintValues.UINT8_MAX, 255],
                        [utils.MaxUintValues.UINT16_MAX, 65535],
                        [utils.MaxUintValues.UINT32_MAX, 4294967295]]),
    ("float_byte_size", [[utils.FloatByteSize.FLOAT32, 4],
                         [utils.FloatByteSize.FLOAT64, 8]]),
])
def test_tlv_packet_setters(attr, values):
    """Ensure valid values can be set via property setters."""
    packet = tlv.tlv_packet()
    for (enumval, intval) in values:
        setattr(packet, attr, enumval)
        assert getattr(packet, attr) == enumval
        assert getattr(getattr(packet, attr), "value") == intval


# Test Invalid Property Setters
@pytest.mark.parametrize("attr, invalid_value", [
    ("max_data_length", 256), ("max_data_length", 65534),
    ("max_data_value", 256), ("max_data_value", 65534),
    ("float_byte_size", 5), ("float_byte_size", 9)
])
def test_tlv_packet_setters_invalid(attr, invalid_value):
    """Ensure property setters raise ValueError for invalid values."""
    packet = tlv.tlv_packet()
    with pytest.raises(ValueError):
        setattr(packet, attr, invalid_value)


# 🟢 Test Encode - Valid Cases
@pytest.mark.parametrize("type_, value_, float_size, max_value, max_length, expected", [
    # Integer Type, Integer Value
    (5, 100, utils.FloatByteSize.FLOAT32, utils.MaxUintValues.UINT8_MAX, utils.MaxUintValues.UINT8_MAX,
     bytearray([5, 1, 100])),
    (255, 255, utils.FloatByteSize.FLOAT32, utils.MaxUintValues.UINT8_MAX, utils.MaxUintValues.UINT8_MAX,
     bytearray([255, 1, 255])),

    # Integer Type, Float Value (4-byte IEEE 754)
    (10, 3.14, utils.FloatByteSize.FLOAT32, utils.MaxUintValues.UINT8_MAX, utils.MaxUintValues.UINT8_MAX,
     bytearray([10, 4]) + struct.pack("f", 3.14)),

    # Integer Type, Float Value (8-byte IEEE 754)
    (20, 3.14, utils.FloatByteSize.FLOAT64, utils.MaxUintValues.UINT8_MAX, utils.MaxUintValues.UINT8_MAX,
     bytearray([20, 8]) + struct.pack("d", 3.14)),

    # Integer Type, Bytearray Value
    (42, bytearray([0x01, 0x02, 0x03]), utils.FloatByteSize.FLOAT32, utils.MaxUintValues.UINT8_MAX,
     utils.MaxUintValues.UINT8_MAX, bytearray([42, 3, 1, 2, 3])),

    # Bytearray Type, Integer Value
    (bytearray([99]), 50, utils.FloatByteSize.FLOAT32, utils.MaxUintValues.UINT8_MAX, utils.MaxUintValues.UINT8_MAX,
     bytearray([99, 1, 50])),

    # Bytearray Type, Float Value
    (bytearray([1]), 2.71, utils.FloatByteSize.FLOAT32, utils.MaxUintValues.UINT8_MAX, utils.MaxUintValues.UINT8_MAX,
     bytearray([1, 4]) + struct.pack("f", 2.71)),

    # Bytearray Type, Bytearray Value
    (bytearray([100]), bytearray([0xFF, 0x00]), utils.FloatByteSize.FLOAT32, utils.MaxUintValues.UINT8_MAX,
     utils.MaxUintValues.UINT8_MAX, bytearray([100, 2, 0xFF, 0x00])),
])
def test_encode_valid(type_, value_, float_size, max_value, max_length, expected):
    """Ensure encode correctly formats TLV packets with valid inputs."""
    packet = tlv.tlv_packet(float_byte_size=float_size, max_data_value=max_value, max_data_length=max_length)
    result = packet.encode(type_, value_)
    assert result == expected


# 🔴 Test Encode - Invalid Type (Not int or bytearray)
@pytest.mark.parametrize("invalid_type", [
    None, "string", 3.14, [10], (1,)
])
def test_encode_invalid_type(invalid_type):
    """Ensure encode raises TypeError when type_ is not an int or bytearray."""
    packet = tlv.tlv_packet()
    with pytest.raises(TypeError):
        packet.encode(invalid_type, 10)


# 🔴 Test Encode - Invalid Type Bytearray (Must be 1 byte)
@pytest.mark.parametrize("invalid_bytearray", [
    bytearray([]), bytearray([1, 2]), bytearray([0, 1, 2, 3]),
])
def test_encode_invalid_bytearray_type(invalid_bytearray):
    """Ensure encode raises ValueError if type_ bytearray is not exactly 1 byte."""
    packet = tlv.tlv_packet()
    with pytest.raises(ValueError):
        packet.encode(invalid_bytearray, 10)


# 🔴 Test Encode - Invalid Type Integer (Out of Range)
@pytest.mark.parametrize("invalid_type", [-1, 256])
def test_encode_invalid_int_type(invalid_type):
    """Ensure encode raises ValueError for out-of-range integer type_."""
    packet = tlv.tlv_packet()
    with pytest.raises(ValueError):
        packet.encode(invalid_type, 10)


# 🔴 Test Encode - Invalid Value Type
@pytest.mark.parametrize("invalid_value", [
    None, "string", [1, 2, 3], (1, 2, 3), {"key": "value"},
])
def test_encode_invalid_value_type(invalid_value):
    """Ensure encode raises TypeError when value_ is not int, float, or bytearray."""
    packet = tlv.tlv_packet()
    with pytest.raises(TypeError):
        packet.encode(1, invalid_value)


# 🔴 Test Encode - Value Out of Range
@pytest.mark.parametrize("invalid_value, max_value", [
    (-1, utils.MaxUintValues.UINT8_MAX), (4294967296, utils.MaxUintValues.UINT32_MAX)
])
def test_encode_value_out_of_range(invalid_value, max_value):
    """Ensure encode raises ValueError when value_ is out of range."""
    packet = tlv.tlv_packet(max_data_value=max_value)
    with pytest.raises(ValueError):
        packet.encode(1, invalid_value)