#!/usr/bin/env python3

import pytest
import struct
import random
from itertools import product
from serial_protocol import tlv, utils


# --- Constructor Tests ---

def test_tlv_packet_constructor_defaults():
    packet = tlv.TLVPacket()
    assert isinstance(packet, tlv.TLVPacket)
    assert packet.max_data_length == utils.MaxUInt.UINT8
    assert packet.max_data_value == utils.MaxUInt.UINT8
    assert packet.float_byte_size == utils.FloatPrecision.FLOAT32


@pytest.mark.parametrize("attr, enumval", [
    ("max_data_length", utils.MaxUInt.UINT16),
    ("max_data_length", utils.MaxUInt.UINT32),
    ("max_data_value", utils.MaxUInt.UINT16),
    ("max_data_value", utils.MaxUInt.UINT32),
    ("float_byte_size", utils.FloatPrecision.FLOAT64),
])
def test_tlv_packet_constructor_valid(attr, enumval):
    packet = tlv.TLVPacket(**{attr: enumval})
    assert getattr(packet, attr) == enumval


@pytest.mark.parametrize("attr, value", [
    ("max_data_length", 999),
    ("max_data_value", "UINT16"),
    ("float_byte_size", 5),
])
def test_tlv_packet_constructor_invalid(attr, value):
    with pytest.raises(ValueError):
        tlv.TLVPacket(**{attr: value})


# --- Property Setters ---

@pytest.mark.parametrize("attr, values", [
    ("max_data_length", [utils.MaxUInt.UINT8, utils.MaxUInt.UINT16, utils.MaxUInt.UINT32]),
    ("max_data_value", [utils.MaxUInt.UINT8, utils.MaxUInt.UINT16, utils.MaxUInt.UINT32]),
    ("float_byte_size", [utils.FloatPrecision.FLOAT32, utils.FloatPrecision.FLOAT64]),
])
def test_tlv_packet_property_setters(attr, values):
    packet = tlv.TLVPacket()
    for val in values:
        setattr(packet, attr, val)
        assert getattr(packet, attr) == val


@pytest.mark.parametrize("attr, invalid_value", [
    ("max_data_length", 0),
    ("max_data_value", None),
    ("float_byte_size", "bad"),
])
def test_tlv_packet_property_setters_invalid(attr, invalid_value):
    packet = tlv.TLVPacket()
    with pytest.raises(ValueError):
        setattr(packet, attr, invalid_value)


# --- Encode/Decode INT ---

@pytest.mark.parametrize("max_length, max_value", product(utils.MaxUInt, utils.MaxUInt))
def test_encode_decode_int_roundtrip(max_length, max_value):
    packet = tlv.TLVPacket(max_data_length=max_length, max_data_value=max_value)
    type_ = random.randint(0, 255)
    value_ = random.randint(0, max_value.max_value)
    encoded = packet.encode(type_, value_)
    decoded = packet.decode(encoded, return_value_as=tlv.TLVValueReturnType.INT)
    assert decoded[0] == type_
    assert decoded[2] == value_


@pytest.mark.parametrize("max_value, input_val, expected_bytes", [
    (utils.MaxUInt.UINT8, 42, bytearray([0x01, 0x01, 0x2A])),
    (utils.MaxUInt.UINT16, 513, bytearray([0x01, 0x02, 0x01, 0x02])),
])
def test_encode_int_structure(max_value, input_val, expected_bytes):
    packet = tlv.TLVPacket(max_data_value=max_value)
    result = packet.encode(1, input_val)
    assert result == expected_bytes


@pytest.mark.parametrize("packet_bytes, expected_value", [
    (bytearray([0x01, 0x01, 0x2A]), 42),
    (bytearray([0x01, 0x02, 0x01, 0x02]), 513),
])
def test_decode_int_structure(packet_bytes, expected_value):
    packet = tlv.TLVPacket()
    result = packet.decode(packet_bytes, return_value_as=tlv.TLVValueReturnType.INT)
    assert result == (1, len(packet_bytes) - 2, expected_value)



# --- Encode/Decode FLOAT ---

@pytest.mark.parametrize("max_length, float_prec", product(utils.MaxUInt, utils.FloatPrecision))
def test_encode_decode_float_roundtrip(max_length, float_prec):
    packet = tlv.TLVPacket(max_data_length=max_length, float_byte_size=float_prec)
    type_ = 42
    value_ = 3.14
    encoded = packet.encode(type_, value_)
    decoded = packet.decode(encoded, return_value_as=tlv.TLVValueReturnType.FLOAT)
    assert decoded[0] == type_
    assert round(decoded[2], 2) == round(value_, 2)


def test_encode_float32_structure():
    packet = tlv.TLVPacket(float_byte_size=utils.FloatPrecision.FLOAT32)
    result = packet.encode(1, 3.14)
    expected = bytearray([0x01, 0x04]) + struct.pack('f', 3.14)
    assert result == expected


def test_decode_float32_structure():
    bytes_ = bytearray([0x01, 0x04]) + struct.pack('f', 3.14)
    packet = tlv.TLVPacket(float_byte_size=utils.FloatPrecision.FLOAT32)
    result = packet.decode(bytes_, return_value_as=tlv.TLVValueReturnType.FLOAT)
    assert round(result[2], 2) == 3.14


# --- Type/Value Error Handling ---

@pytest.mark.parametrize("invalid_type", [-1, 256, 3.14, "str", None])
def test_encode_invalid_type(invalid_type):
    packet = tlv.TLVPacket()
    with pytest.raises((TypeError, ValueError)):
        packet.encode(invalid_type, 1)


@pytest.mark.parametrize("invalid_value", ["abc", {}, [1], (2,), None])
def test_encode_invalid_value(invalid_value):
    packet = tlv.TLVPacket()
    with pytest.raises(TypeError):
        packet.encode(1, invalid_value)


@pytest.mark.parametrize("invalid_float", [
    bytearray([0x00, 0x00]),          # too short
    bytearray([0x00] * 10),           # too long
])
def test_decode_float_size_mismatch(invalid_float):
    packet = tlv.TLVPacket(float_byte_size=utils.FloatPrecision.FLOAT32)
    length_bytes = utils.int_to_bytearray(len(invalid_float), packet.max_data_length)
    full_packet = bytearray([0x01]) + length_bytes + invalid_float
    with pytest.raises(ValueError):
        packet.decode(full_packet, return_value_as=tlv.TLVValueReturnType.FLOAT)


def test_decode_empty_packet_raises():
    packet = tlv.TLVPacket()
    with pytest.raises(ValueError):
        packet.decode(bytearray([]))


def test_decode_type_error_inputs():
    packet = tlv.TLVPacket()
    with pytest.raises(TypeError):
        packet.decode("not a bytearray")

    with pytest.raises(TypeError):
        packet.decode(bytearray([0x01, 0x00]), return_value_as="string")
