#!/usr/bin/env python3

import pytest

from serial_protocol import cobs


class HexData():
    def __init__(self):
        self.hexstr_0x = "0x00 0x11 0x11 0x00 0x22 0x22 0x00"
        self.hexstr_plain = "00 11 11 00 22 22 00"
        self.hexstr_invalid = "00 11 11 00 0x22 0x22 0x00"
        self.int_list = [0, 17, 17, 0, 34, 34, 0]
        self.bytearr = bytearray([0x00, 0x11, 0x11, 0x00, 0x22, 0x22, 0x00])
        self.encoded = bytearray([0x01, 0x03, 0x11, 0x11, 0x03, 0x22, 0x22, 0x01, 0x00])


@pytest.fixture
def hex_data():
    return HexData()


def test_is_0x_format_true(hex_data):
    assert cobs.is_0x_format(hex_data.hexstr_0x) is True


def test_is_0x_format_false(hex_data):
    assert cobs.is_0x_format(hex_data.hexstr_plain) is False


def test_is_0x_format_invalid(hex_data):
    with pytest.raises(ValueError):
        cobs.is_0x_format(hex_data.hexstr_invalid)


def test_bytearray_to_hexstring_0x_format(hex_data):
    assert cobs.bytearray_to_hexstring(hex_data.bytearr) == hex_data.hexstr_0x


def test_bytearray_to_hexstring_plain_format(hex_data):
    assert cobs.bytearray_to_hexstring(hex_data.bytearr, False) == hex_data.hexstr_plain


def test_hexstring_to_bytearray_0x_format(hex_data):
    assert cobs.hexstring_to_bytearray(hex_data.hexstr_0x) == hex_data.bytearr


def test_hexstring_to_bytearray_plain_format(hex_data):
    assert cobs.hexstring_to_bytearray(hex_data.hexstr_plain) == hex_data.bytearr


def test_hexstring_to_bytearray_invalid_format(hex_data):
    with pytest.raises(ValueError):
        cobs.hexstring_to_bytearray(hex_data.hexstr_invalid)


def test_encode_no_zeros():
    bytes = bytearray([0x01, 0x02, 0x03])
    encoded = bytearray([0x04, 0x01, 0x02, 0x03, 0x00])
    assert cobs.encode(bytes) == encoded


def test_encode_non_leading_zeros():
    bytes = bytearray([0x01, 0x02, 0x00, 0x03, 0x00])
    encoded = bytearray([0x03, 0x01, 0x02, 0x02, 0x03, 0x01, 0x00])
    assert cobs.encode(bytes) == encoded


def test_encode_bytearray(hex_data):
    assert cobs.encode(hex_data.bytearr) == hex_data.encoded


def test_encode_hexstring_0x(hex_data):
    assert cobs.encode(hex_data.hexstr_0x) == hex_data.encoded


def test_encode_hexstring_plain(hex_data):
    assert cobs.encode(hex_data.hexstr_plain) == hex_data.encoded


def test_encode_hexstring_invalid(hex_data):
    with pytest.raises(ValueError):
        assert cobs.encode(hex_data.hexstr_invalid)


def test_encode_int_list(hex_data):
    assert cobs.encode(hex_data.int_list) == hex_data.encoded


def test_encode_long_array():
    # decoded [00 02 03 ... FE FF]
    data = bytearray(list(range(0, 256)))
    # print("\nData [%d]:" % len(data), cobs.bytearray_to_string(data))

    # expected cobs encoding [01 FF 01 02 03 ... FE 02 FF]
    encoded = bytearray([0x01, 0xff] + list(range(1, 255)) + [0x02, 0xff, 0x00])
    # print("\nEncoded [%d]:" % len(encoded), cobs.bytearray_to_string(encoded))

    # test encode function
    retval = cobs.encode(data)
    # print("\nReturn [%d]:" % len(retval), cobs.bytearray_to_string(retval))
    assert encoded == retval


def test_decode_no_zeros():
    bytes = bytearray([0x01, 0x02, 0x03])
    encoded = bytearray([0x04, 0x01, 0x02, 0x03, 0x00])
    assert cobs.decode(encoded) == bytes


def test_decode_non_leading_zeros():
    bytes = bytearray([0x01, 0x02, 0x00, 0x03, 0x00])
    encoded = bytearray([0x03, 0x01, 0x02, 0x02, 0x03, 0x01, 0x00])
    assert cobs.decode(encoded) == bytes


def test_decode_bytearray(hex_data):
    bytes = bytearray([0x00, 0x11, 0x11, 0x00, 0x22, 0x22, 0x00])
    encoded = bytearray([0x01, 0x03, 0x11, 0x11, 0x03, 0x22, 0x22, 0x01, 0x00])
    assert cobs.decode(encoded) == bytes


def test_decode_long_array():
    # cobs encoded [01 FF 01 02 03 ... FE 02 FF]
    data = bytearray([0x01, 0xff] + list(range(1, 255)) + [0x02, 0xff, 0x00])
    print("\nData [%d]:" % len(data), cobs.bytearray_to_string(data))

    # expected cobs decoding [00 02 03 ... FE FF]
    decoded = bytearray(list(range(0, 256)))
    print("\nDecoded [%d]:" % len(decoded), cobs.bytearray_to_string(decoded))

    # test encode function
    retval = cobs.decode(data)
    print("\nReturn [%d]:" % len(retval), cobs.bytearray_to_string(retval))
    assert decoded == retval
