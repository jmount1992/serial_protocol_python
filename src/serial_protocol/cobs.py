#!/usr/bin/env python3

from typing import Union
from serial_protocol.utils import hexstring_to_bytearray


def encode(data: Union[str, list, bytearray]) -> bytearray:
    """
    Encodes the given data using COBS encoding.

    Handles input conversion from different formats (str, list, bytearray) before
    passing it to `encode_bytearray`.

    Args:
        data (Union[str, list, bytearray]): The input data to encode.

    Returns:
        bytearray: The COBS-encoded byte sequence.
    """
    if isinstance(data, str):
        data = hexstring_to_bytearray(data)
    elif isinstance(data, list):
        data = bytearray(data)
    elif not isinstance(data, bytearray):
        raise TypeError("Input data must be a bytearray, list, or hex string.")

    return encode_bytearray(data)


def encode_bytearray(data: bytearray) -> bytearray:
    """
    Encodes the given data using Consistent Overhead Byte Stuffing (COBS).

    COBS replaces zero bytes (`0x00`) in the input with a length-based encoding.
    This ensures that encoded data contains no zeros except for the final frame delimiter (`0x00`).

    Args:
        data (Union[str, list, bytearray]): The input data to encode.
            - `str`: A hex string (e.g., "00 11 22").
            - `list`: A list of integer byte values.
            - `bytearray`: A raw bytearray.

    Returns:
        bytearray: The COBS-encoded byte sequence.
    """
    if not isinstance(data, bytearray):
        raise TypeError("Input data must be a bytearray.")

    encoded = bytearray([0x00])  # with place holder for first marker
    zero_block_len = 1  # Length counter for zero markers
    zero_marker_pos = 0  # Position of the current zero marker

    for byte in data:
        # Check to see if we need to add an extra byte
        if zero_block_len == 0xff:
            # set current zero marker to be 0xff, and add another
            # zero into encoded data
            encoded[zero_marker_pos] = 0xff
            encoded.append(0x00)

            # reset zero marker position and length of this
            # zero block
            zero_marker_pos = len(encoded) - 1
            zero_block_len = 1

        # Now check value of the byte
        if byte == 0x00:
            encoded[zero_marker_pos] = zero_block_len
            encoded.append(0x00)
            zero_marker_pos = len(encoded) - 1
            zero_block_len = 1
        else:
            encoded.append(byte)
            zero_block_len += 1

    # Handle the final marker
    if len(data) != 1:
        encoded[zero_marker_pos] = zero_block_len
        encoded.append(0x00)  # Frame delimiter
    return encoded


def decode(data: Union[str, list, bytearray]) -> bytearray:
    """
    Decodes the given COBS-encoded data back into its original form.

    Handles input conversion before passing it to `decode_bytearray`.

    Args:
        data (Union[str, list, bytearray]): The COBS-encoded data.

    Returns:
        bytearray: The original decoded byte sequence.
    """
    if isinstance(data, str):
        data = hexstring_to_bytearray(data)
    elif isinstance(data, list):
        data = bytearray(data)
    elif not isinstance(data, bytearray):
        raise TypeError("Input data must be a bytearray, list, or hex string.")

    return decode_bytearray(data)


def decode_bytearray(data: bytearray) -> bytearray:
    """
    Decodes a COBS-encoded bytearray back to its original form.

    Args:
        data (bytearray): The COBS-encoded byte sequence.

    Returns:
        bytearray: The original decoded byte sequence.
    """
    if not isinstance(data, bytearray):
        raise TypeError("Input data must be a bytearray.")
    decoded = bytearray()

    num_bytes_until_zero = data[0] - 1  # index of first zero
    overhead_byte_added = (0xff == data[0])  # set to true if more than 255 bytes before next zero in decoded data
    for byte in data[1:]:
        if byte == 0x00:
            if len(decoded) == 0:
                decoded.append(0x00)
            continue  # found delimiter frame

        if num_bytes_until_zero != 0:
            decoded.append(byte)
            num_bytes_until_zero -= 1
        else:
            # check for actual 0 or added byte
            if overhead_byte_added:
                overhead_byte_added = False
            else:
                decoded.append(0x00)
            num_bytes_until_zero = byte - 1
            overhead_byte_added = (0xff == byte)

    return decoded
