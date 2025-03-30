#!/usr/bin/env python3

import pytest
import random
import math
from itertools import product
from serial_protocol import tlv, utils
from hypothesis import given, strategies as st


# --- CONSTRUCTOR TESTS --- #


def test_defaults():
    packet = tlv.TLVPacket()
    assert isinstance(packet, tlv.TLVPacket)
    assert packet.max_data_length == utils.ValueFormat.UINT8


@pytest.mark.parametrize("attr, enumval", [
    ("max_data_length", utils.ValueFormat.UINT8),
    ("max_data_length", utils.ValueFormat.UINT16),
    ("max_data_length", utils.ValueFormat.UINT32),
])
def test_valid_constructor_values(attr, enumval):
    packet = tlv.TLVPacket(**{attr: enumval})
    assert getattr(packet, attr) == enumval


@pytest.mark.parametrize("attr, value", [
    ("max_data_length", 999),
    ("max_data_length", "FLOAT32"),
])
def test_invalid_constructor_values(attr, value):
    with pytest.raises(ValueError):
        tlv.TLVPacket(**{attr: value})


# --- PROPERTY TESTS --- #


@pytest.mark.parametrize("attr, values", [
    ("max_data_length", [utils.ValueFormat.UINT8, utils.ValueFormat.UINT16, utils.ValueFormat.UINT32]),
])
def test_valid_setters(attr, values):
    packet = tlv.TLVPacket()
    for val in values:
        setattr(packet, attr, val)
        assert getattr(packet, attr) == val


@pytest.mark.parametrize("attr, invalid_value", [
    ("max_data_length", "FLOAT64"),
])
def test_invalid_setters(attr, invalid_value):
    packet = tlv.TLVPacket()
    with pytest.raises(ValueError):
        setattr(packet, attr, invalid_value)


# --- ENCODE/DECODE TESTS --- #


@pytest.mark.parametrize("max_length, format_", product(
    [utils.ValueFormat.UINT8, utils.ValueFormat.UINT16, utils.ValueFormat.UINT32],
    [utils.ValueFormat.UINT8, utils.ValueFormat.UINT16, utils.ValueFormat.UINT32]
))
def test_encode_decode_int_roundtrip(max_length, format_):
    packet = tlv.TLVPacket(max_data_length=max_length)
    type_ = random.randint(0, 255)
    value_ = random.randint(0, format_.max_value)
    encoded = packet.encode(type_, value_, format_)
    decoded = packet.decode(encoded, value_format=format_)
    assert decoded[0] == type_
    assert decoded[2] == value_


@pytest.mark.parametrize("max_length, format_", product(
    [utils.ValueFormat.UINT8, utils.ValueFormat.UINT16, utils.ValueFormat.UINT32],
    [utils.ValueFormat.FLOAT32, utils.ValueFormat.FLOAT64],
))
def test_encode_decode_float_roundtrip(max_length, format_):
    packet = tlv.TLVPacket(max_data_length=max_length)
    type_ = 42
    value_ = 3.14
    encoded = packet.encode(type_, value_, format_)
    decoded = packet.decode(encoded, value_format=format_)
    assert decoded[0] == type_
    assert round(decoded[2], 2) == round(value_, 2)


def test_raw_bytearray_decode():
    packet = tlv.TLVPacket()
    value_bytes = bytearray([0xAB, 0xCD])
    length = len(value_bytes)
    length_bytes = utils.int_to_bytearray(length, format=utils.ValueFormat.UINT8)
    encoded = bytearray([0x05]) + length_bytes + value_bytes
    decoded = packet.decode(encoded, value_format=None)
    assert decoded == (5, length, value_bytes)


# --- ERROR TESTS --- #


def test_decode_length_mismatch():
    packet = tlv.TLVPacket(max_data_length=utils.ValueFormat.UINT8)
    corrupted = bytearray([0x01, 0x05, 0xAA])  # claims length 5, gives 1 byte
    with pytest.raises(ValueError):
        packet.decode(corrupted, value_format=None)


@pytest.mark.parametrize("invalid_type", [-1, 256, 3.14, "str", None])
def test_invalid_type_input(invalid_type):
    packet = tlv.TLVPacket()
    with pytest.raises((TypeError, ValueError)):
        packet.encode(invalid_type, 1, utils.ValueFormat.UINT8)


@pytest.mark.parametrize("invalid_value", ["abc", {}, [1], (2,), None])
def test_invalid_value_input(invalid_value):
    packet = tlv.TLVPacket()
    with pytest.raises(TypeError):
        packet.encode(1, invalid_value, utils.ValueFormat.UINT8)


def test_encode_float_with_uint_format():
    packet = tlv.TLVPacket()
    with pytest.raises(TypeError):
        packet.encode(1, 3.14, utils.ValueFormat.UINT16)


def test_encode_int_out_of_range():
    packet = tlv.TLVPacket()
    with pytest.raises(ValueError):
        packet.encode(1, 256, utils.ValueFormat.UINT8)


def test_decode_float_size_mismatch():
    packet = tlv.TLVPacket()
    format_ = utils.ValueFormat.FLOAT32
    bad_float = bytearray([0x00, 0x00])  # Too short
    length = utils.int_to_bytearray(len(bad_float), format=utils.ValueFormat.UINT8)
    full = bytearray([0x01]) + length + bad_float
    with pytest.raises(ValueError):
        packet.decode(full, value_format=format_)


def test_decode_empty_packet():
    packet = tlv.TLVPacket()
    with pytest.raises(ValueError):
        packet.decode(bytearray([]))


def test_decode_type_error():
    packet = tlv.TLVPacket()
    with pytest.raises(TypeError):
        packet.decode("not bytes")


# --- UINT FUZZ TESTS --- #

uint_strategies = {
    utils.ValueFormat.UINT8: st.integers(min_value=0, max_value=2**8 - 1),
    utils.ValueFormat.UINT16: st.integers(min_value=0, max_value=2**16 - 1),
    utils.ValueFormat.UINT32: st.integers(min_value=0, max_value=2**32 - 1),
}


@pytest.mark.parametrize("format_", [utils.ValueFormat.UINT8, utils.ValueFormat.UINT16, utils.ValueFormat.UINT32])
@given(type_=st.integers(min_value=0, max_value=255),
       data=st.integers(min_value=0, max_value=2**32 - 1))
def test_fuzz_encode_decode_uints(type_, data, format_):
    if data > format_.max_value:
        pytest.skip("Filtered to avoid over-range value for format")
    packet = tlv.TLVPacket(max_data_length=utils.ValueFormat.UINT8)
    encoded = packet.encode(type_, data, format_)
    decoded = packet.decode(encoded, value_format=format_)
    assert decoded[0] == type_
    assert decoded[2] == data


# --- FLOAT FUZZ TESTS --- #

@given(
    type_=st.integers(min_value=0, max_value=255),
    data=st.floats(
        min_value=-3.4e38,
        max_value=3.4e38,
        allow_nan=False,
        allow_infinity=False,
        width=64
    )
)
def test_fuzz_encode_decode_float32(type_, data):
    format_ = utils.ValueFormat.FLOAT32
    packet = tlv.TLVPacket(max_data_length=utils.ValueFormat.UINT8)
    encoded = packet.encode(type_, data, format_)
    decoded = packet.decode(encoded, value_format=format_)
    assert decoded[0] == type_
    assert math.isclose(decoded[2], data, rel_tol=1e-5, abs_tol=1e-5)


@given(
    type_=st.integers(min_value=0, max_value=255),
    data=st.floats(
        min_value=-1.7e308,
        max_value=1.7e308,
        allow_nan=False,
        allow_infinity=False,
        width=64
    )
)
def test_fuzz_encode_decode_float64(type_, data):
    format_ = utils.ValueFormat.FLOAT64
    packet = tlv.TLVPacket(max_data_length=utils.ValueFormat.UINT8)
    encoded = packet.encode(type_, data, format_)
    decoded = packet.decode(encoded, value_format=format_)
    assert decoded[0] == type_
    assert math.isclose(decoded[2], data, rel_tol=1e-5, abs_tol=1e-5)
