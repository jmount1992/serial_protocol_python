#!/usr/bin/env python3

import pytest
from serial_protocol import packet, utils


# --- Constructor Tests --- #

def test_serial_packet_constructor():
    """Ensure SerialPacket initializes correctly with default parameters."""
    sp = packet.SerialPacket()
    assert isinstance(sp, packet.SerialPacket)


@pytest.mark.parametrize("max_data_length, expected", [
    (utils.ValueFormat.UINT8, utils.ValueFormat.UINT8),
    (utils.ValueFormat.UINT16, utils.ValueFormat.UINT16),
    (utils.ValueFormat.UINT32, utils.ValueFormat.UINT32),
    ("uint8", utils.ValueFormat.UINT8),
    ("uint16", utils.ValueFormat.UINT16),
    ("uint32", utils.ValueFormat.UINT32),
])
def test_serial_packet_constructor_valid_values(max_data_length, expected):
    """Test valid max_data_length input is coerced correctly."""
    sp = packet.SerialPacket(max_data_length=max_data_length)
    assert sp._tlv_packet.max_data_length == expected


@pytest.mark.parametrize("invalid_length", [
    utils.ValueFormat.FLOAT32,
    utils.ValueFormat.FLOAT64,
    255,
    3.14,
    None,
])
def test_serial_packet_constructor_invalid_values(invalid_length):
    """Test constructor raises for invalid max_data_length."""
    with pytest.raises(ValueError):
        packet.SerialPacket(max_data_length=invalid_length)


# --- Encode Tests --- #

@pytest.mark.parametrize("maxlen, type_, value_, fmt, expected", [
    (utils.ValueFormat.UINT8, 1, 123, utils.ValueFormat.UINT8, bytearray([0x01, 0x01, 0x7b, 0xfd, 0xcb])),
    (utils.ValueFormat.UINT16, 1, 123, utils.ValueFormat.UINT8, bytearray([0x01, 0x01, 0x00, 0x7b, 0x78, 0x8e])),
    (utils.ValueFormat.UINT32, 1, 123, utils.ValueFormat.UINT8, bytearray([0x01, 0x01, 0x00, 0x00, 0x00, 0x7b, 0x0d, 0x20])),
])
def test_encode_basic_payload(maxlen, type_, value_, fmt, expected):
    """Test standard encode functionality for different max_data_length formats."""
    sp = packet.SerialPacket(max_data_length=maxlen)
    assert sp.encode(type_, value_, fmt) == expected
    struct = packet.SerialPacketStruct(type_=type_, value_=value_, format_=fmt)
    assert sp.encode(struct) == expected


@pytest.mark.parametrize("maxlen, dev_id, type_, value_, fmt, expected", [
    (utils.ValueFormat.UINT8, 20, 1, 123, utils.ValueFormat.UINT8, bytearray([0x14, 0x01, 0x01, 0x7b, 0xab, 0x1a])),
])
def test_encode_with_device_id(maxlen, dev_id, type_, value_, fmt, expected):
    """Test encode with device ID prepended."""
    sp = packet.SerialPacket(max_data_length=maxlen)
    assert sp.encode(type_, value_, fmt, device_id=dev_id) == expected
    struct = packet.SerialPacketStruct(device_id=dev_id, type_=type_, value_=value_, format_=fmt)
    assert sp.encode(struct) == expected


@pytest.mark.parametrize("maxlen, dev_id, type_, value_, fmt, expected", [
    (utils.ValueFormat.UINT8, 20, 1, 123, utils.ValueFormat.UINT8, bytearray([0x07, 0x14, 0x01, 0x01, 0x7b, 0xab, 0x1a, 0x00])),
])
def test_encode_with_cobs_encoding(maxlen, dev_id, type_, value_, fmt, expected):
    """Test encode with COBS wrapping and device ID."""
    sp = packet.SerialPacket(max_data_length=maxlen)
    struct = packet.SerialPacketStruct(device_id=dev_id, type_=type_, value_=value_, format_=fmt)
    assert sp.encode(type_, value_, fmt, device_id=dev_id, cobs_encode=True) == expected
    assert sp.encode(struct, cobs_encode=True) == expected


# --- Decode Tests --- #

def test_decode_return_type():
    """Decode should return a SerialPacketStruct."""
    sp = packet.SerialPacket()
    result = sp.decode(bytearray([0x01, 0x01, 0x7b, 0xfd, 0xcb]), utils.ValueFormat.UINT8)
    assert isinstance(result, packet.SerialPacketStruct)


@pytest.mark.parametrize("maxlen, data_, type_, value_, fmt", [
    (utils.ValueFormat.UINT8, bytearray([0x01, 0x01, 0x7b, 0xfd, 0xcb]), 1, 123, utils.ValueFormat.UINT8),
])
def test_decode_basic(maxlen, data_, type_, value_, fmt):
    """Decode correctly from raw TLV + CRC packet."""
    sp = packet.SerialPacket(max_data_length=maxlen)
    result = sp.decode(data_, fmt)
    assert result.device_id is None
    assert result.type_ == type_
    assert result.value_ == value_
    assert result.format_ == fmt


@pytest.mark.parametrize("maxlen, data_, dev_id, type_, value_, fmt", [
    (utils.ValueFormat.UINT8, bytearray([0x14, 0x01, 0x01, 0x7b, 0xab, 0x1a]), 20, 1, 123, utils.ValueFormat.UINT8),
])
def test_decode_with_device_id(maxlen, data_, dev_id, type_, value_, fmt):
    """Decode correctly with a device ID prefix."""
    sp = packet.SerialPacket(max_data_length=maxlen)
    result = sp.decode(data_, fmt, device_id=True)
    assert result.device_id == dev_id
    assert result.type_ == type_
    assert result.value_ == value_
    assert result.format_ == fmt


@pytest.mark.parametrize("maxlen, data_, dev_id, type_, value_, fmt", [
    (utils.ValueFormat.UINT8, bytearray([0x07, 0x14, 0x01, 0x01, 0x7b, 0xab, 0x1a, 0x00]), 20, 1, 123, utils.ValueFormat.UINT8),
])
def test_decode_cobs_encoded(maxlen, data_, dev_id, type_, value_, fmt):
    """Decode with COBS wrapping and device ID."""
    sp = packet.SerialPacket(max_data_length=maxlen)
    result = sp.decode(data_, fmt, device_id=True, cobs_encoded=True)
    assert result.device_id == dev_id
    assert result.type_ == type_
    assert result.value_ == value_
    assert result.format_ == fmt


# --- Failure Tests --- #

def corrupt_checksum(data: bytearray) -> bytearray:
    corrupted = bytearray(data)
    corrupted[-1] ^= 0xFF
    return corrupted


def test_decode_checksum_failure():
    """Corrupted checksum should raise ValueError."""
    sp = packet.SerialPacket()
    encoded = sp.encode(1, 123, utils.ValueFormat.UINT8)
    corrupted = corrupt_checksum(encoded)
    with pytest.raises(ValueError):
        sp.decode(corrupted, utils.ValueFormat.UINT8)


def test_decode_invalid_length_field():
    """Packet with invalid TLV length should raise ValueError."""
    sp = packet.SerialPacket()
    # Construct: type=1, length=5 (only 1 byte payload), plus checksum
    bad_payload = bytearray([0x01, 0x05, 0x7b])
    checksum = utils.int_to_bytearray(sp._crc_calc.checksum(bad_payload), utils.ValueFormat.UINT16)
    broken_packet = bad_payload + checksum
    with pytest.raises(ValueError):
        sp.decode(broken_packet, utils.ValueFormat.UINT8)


def test_decode_invalid_cobs_data():
    """Malformed COBS input should raise ValueError."""
    sp = packet.SerialPacket()
    bad_cobs = bytearray([0x03, 0x01, 0x00, 0x7b, 0xfd, 0xcb])  # includes forbidden 0x00
    with pytest.raises(ValueError):
        sp.decode(bad_cobs, utils.ValueFormat.UINT8, cobs_encoded=True)
