#!/usr/bin/env python3

import pytest
import struct
import random
from itertools import product
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


# Test Encode - Valid Cases
@pytest.mark.parametrize("max_length, type_, value_, expected", [
    (utils.MaxUintValues.UINT8_MAX, 0, 0, bytearray([0x00, 0x01, 0x00])),
    (utils.MaxUintValues.UINT8_MAX, 128, 122, bytearray([0x80, 0x01, 0x7a])),
    (utils.MaxUintValues.UINT8_MAX, 255, 255, bytearray([0xff, 0x01, 0xff])),
    (utils.MaxUintValues.UINT16_MAX, 0, 0, bytearray([0x00, 0x01, 0x00, 0x00])),
    (utils.MaxUintValues.UINT16_MAX, 128, 122, bytearray([0x80, 0x01, 0x00, 0x7a])),
    (utils.MaxUintValues.UINT16_MAX, 255, 255, bytearray([0xff, 0x01, 0x00, 0xff])),
    (utils.MaxUintValues.UINT32_MAX, 0, 0, bytearray([0x00, 0x01, 0x00, 0x00, 0x00, 0x00])),
    (utils.MaxUintValues.UINT32_MAX, 128, 122, bytearray([0x80, 0x01, 0x00, 0x00, 0x00, 0x7a])),
    (utils.MaxUintValues.UINT32_MAX, 255, 255, bytearray([0xff, 0x01, 0x00, 0x00, 0x00, 0xff]))
])
def test_encode_valid_max_length(max_length, type_, value_, expected):
    packet = tlv.tlv_packet(max_data_length=max_length)
    result = packet.encode(type_, value_)
    assert result == expected


@pytest.mark.parametrize("max_value, type_, value_, expected", [
    (utils.MaxUintValues.UINT8_MAX, 0, 0, bytearray([0x00, 0x01, 0x00])),
    (utils.MaxUintValues.UINT8_MAX, 128, 122, bytearray([0x80, 0x01, 0x7a])),
    (utils.MaxUintValues.UINT8_MAX, 255, 255, bytearray([0xff, 0x01, 0xff])),
    (utils.MaxUintValues.UINT16_MAX, 0, 0, bytearray([0x00, 0x02, 0x00, 0x00])),
    (utils.MaxUintValues.UINT16_MAX, 128, 122, bytearray([0x80, 0x02, 0x7a, 0x00])),
    (utils.MaxUintValues.UINT16_MAX, 255, 65535, bytearray([0xff, 0x02, 0xff, 0xff])),
    (utils.MaxUintValues.UINT32_MAX, 0, 0, bytearray([0x00, 0x04, 0x00, 0x00, 0x00, 0x00])),
    (utils.MaxUintValues.UINT32_MAX, 128, 122, bytearray([0x80, 0x04, 0x7a, 0x00, 0x00, 0x00])),
    (utils.MaxUintValues.UINT32_MAX, 255, 4294967295, bytearray([0xff, 0x04, 0xff, 0xff, 0xff, 0xff]))
])
def test_encode_valid_max_value(max_value, type_, value_, expected):
    packet = tlv.tlv_packet(max_data_value=max_value)
    result = packet.encode(type_, value_)
    assert result == expected


@pytest.mark.parametrize("float_size, type_, value_, expected", [
    (utils.FloatByteSize.FLOAT32, 0, 3.14, bytearray([0x00, 0x04]) + struct.pack('f', 3.14)),
    (utils.FloatByteSize.FLOAT64, 0, 3.14, bytearray([0x00, 0x08]) + struct.pack('d', 3.14))
])
def test_encode_valid_float_size(float_size, type_, value_, expected):
    packet = tlv.tlv_packet(float_byte_size=float_size)
    result = packet.encode(type_, value_)
    assert result == expected


# Test Encode - Invalid Type (Not int or bytearray)
@pytest.mark.parametrize("invalid_type", [
    None, "string", 3.14, [10], (1,)
])
def test_encode_invalid_type(invalid_type):
    """Ensure encode raises TypeError when type_ is not an int or bytearray."""
    packet = tlv.tlv_packet()
    with pytest.raises(TypeError):
        packet.encode(invalid_type, 10)


# Test Encode - Invalid Type Bytearray (Must be 1 byte)
@pytest.mark.parametrize("invalid_bytearray", [
    bytearray([]), bytearray([1, 2]), bytearray([0, 1, 2, 3]),
])
def test_encode_invalid_bytearray_type(invalid_bytearray):
    """Ensure encode raises ValueError if type_ bytearray is not exactly 1 byte."""
    packet = tlv.tlv_packet()
    with pytest.raises(ValueError):
        packet.encode(invalid_bytearray, 10)


# Test Encode - Invalid Type Integer (Out of Range)
@pytest.mark.parametrize("invalid_type", [-1, 256])
def test_encode_invalid_int_type(invalid_type):
    """Ensure encode raises ValueError for out-of-range integer type_."""
    packet = tlv.tlv_packet()
    with pytest.raises(ValueError):
        packet.encode(invalid_type, 10)


# Test Encode - Invalid Value Type
@pytest.mark.parametrize("invalid_value", [
    None, "string", [1, 2, 3], (1, 2, 3), {"key": "value"},
])
def test_encode_invalid_value_type(invalid_value):
    """Ensure encode raises TypeError when value_ is not int, float, or bytearray."""
    packet = tlv.tlv_packet()
    with pytest.raises(TypeError):
        packet.encode(1, invalid_value)


# Test Encode - Value Out of Range
@pytest.mark.parametrize("invalid_value, max_value", [
    (-1, utils.MaxUintValues.UINT8_MAX), (4294967296, utils.MaxUintValues.UINT32_MAX)
])
def test_encode_value_out_of_range(invalid_value, max_value):
    """Ensure encode raises ValueError when value_ is out of range."""
    packet = tlv.tlv_packet(max_data_value=max_value)
    with pytest.raises(ValueError):
        packet.encode(1, invalid_value)


# Test Decode
@pytest.mark.parametrize("max_length, min_packet_size", [
    (utils.MaxUintValues.UINT8_MAX, 2),
    (utils.MaxUintValues.UINT16_MAX, 3),
    (utils.MaxUintValues.UINT32_MAX, 5)
])
def test_decode_packet_length_exception(max_length, min_packet_size):
    tlv_ = tlv.tlv_packet(max_data_length=max_length)
    with pytest.raises(ValueError):
        tlv_.decode(bytearray([0x00]*(min_packet_size-1)))
    tlv_.decode(bytearray([0x00]*(min_packet_size)))


def test_decode_empty_packet():
    packet = tlv.tlv_packet()
    with pytest.raises(ValueError):
        packet.decode(bytearray([]))


@pytest.mark.parametrize("max_length_enum", [
    utils.MaxUintValues.UINT8_MAX,
    utils.MaxUintValues.UINT16_MAX,
    utils.MaxUintValues.UINT32_MAX,
])
def test_decode_packet_length_mismatch(max_length_enum):
    packet = tlv.tlv_packet(max_data_length=max_length_enum,
                            max_data_value=utils.MaxUintValues.UINT8_MAX)
    type_ = 0x01
    value = bytearray([0x10, 0x20])  # actual value is 2 bytes
    declared_len = len(value) + 2    # intentionally incorrect length
    length_field = utils.int_to_bytearray(declared_len, max_length_enum)
    corrupted_packet = bytearray([type_]) + length_field + value  # too short for declared length

    with pytest.raises(ValueError):
        packet.decode(corrupted_packet)


@pytest.mark.parametrize(
    "max_length, max_value",
    list(product(list(utils.MaxUintValues), list(utils.MaxUintValues)))
)
def test_decode_value_as_bytearray(max_length, max_value):
    tlv_ = tlv.tlv_packet(max_data_length=max_length, max_data_value=max_value)
    type_ = random.randint(0, 255)
    value_ = random.randint(0, max_value.value)
    value_bytes = utils.int_to_bytearray(value_, max_value)
    length_bytes = utils.int_to_bytearray(len(value_bytes), max_length)
    packet = bytearray([type_]) + length_bytes + value_bytes

    decoded = tlv_.decode(packet, return_value_as=tlv.TLVValueReturnType.BYTEARRAY)
    assert decoded[0] == type_
    assert decoded[1] == len(value_bytes)
    assert isinstance(decoded[2], bytearray)
    assert decoded[2] == value_bytes


@pytest.mark.parametrize(
    "max_length, max_value",
    list(product(list(utils.MaxUintValues), list(utils.MaxUintValues)))
)
def test_decode_value_as_int(max_length, max_value):
    tlv_ = tlv.tlv_packet(max_data_length=max_length, max_data_value=max_value)
    type_ = random.randint(0, 255)
    value_ = random.randint(0, max_value.value)
    value_bytes = utils.int_to_bytearray(value_, max_value)
    length_bytes = utils.int_to_bytearray(len(value_bytes), max_length)
    packet = bytearray([type_]) + length_bytes + value_bytes

    decoded = tlv_.decode(packet, return_value_as=tlv.TLVValueReturnType.INT)
    assert decoded[0] == type_
    assert decoded[1] == len(value_bytes)
    assert isinstance(decoded[2], int)
    assert decoded[2] == value_


@pytest.mark.parametrize(
    "max_length, float_size",
    list(product(list(utils.MaxUintValues), list(utils.FloatByteSize)))
)
def test_decode_value_as_float_product(max_length, float_size):
    tlv_ = tlv.tlv_packet(max_data_length=max_length, float_byte_size=float_size)

    type_ = random.randint(0, 255)
    float_val = 3.14
    value_bytes = utils.float_to_bytearray(float_val, float_size)
    length_bytes = utils.int_to_bytearray(len(value_bytes), max_length)
    packet = bytearray([type_]) + length_bytes + value_bytes

    decoded = tlv_.decode(packet, return_value_as=tlv.TLVValueReturnType.FLOAT)
    assert decoded[0] == type_
    assert decoded[1] == float_size.value
    assert isinstance(decoded[2], float)
    assert 3.14 == 3.14

