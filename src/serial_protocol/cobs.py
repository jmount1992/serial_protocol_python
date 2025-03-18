#!/usr/bin/env python3

from typing import Union
from serial_protocol.utils import hexstring_to_bytearray


def encode(data: Union[str, list, bytearray]) -> bytearray:
    """
    Encodes the given data using Consistent Overhead Byte Stuffing (COBS).

    This function handles input conversion before passing the data
    to `encode_bytearray()`.

    Args:
        data (Union[str, list, bytearray]): The input data to encode.
            - `str`: A hex string (e.g., "00 11 22").
            - `list`: A list of integer values.
            - `bytearray`: A raw bytearray.

    Returns:
        bytearray: The COBS-encoded byte sequence.

    Raises:
        TypeError: If `data` is not one of the supported types.
    """
    if isinstance(data, str):
        data = hexstring_to_bytearray(data)
    elif isinstance(data, list):
        data = bytearray(data)
    elif not isinstance(data, bytearray):
        raise TypeError("Input data must be a bytearray, list, or hex string.")

    return encode_bytearray(data)


def encode_bytearray(data: bytearray, delimiter: int = 0x00) -> bytearray:
    """
    Encodes a bytearray using Consistent Overhead Byte Stuffing (COBS).

    COBS ensures that the encoded data contains no occurrences of `0x00`,
    except for the final frame delimiter `0x00`. It does this by replacing
    zero bytes with a length marker.

    Args:
        data (bytearray): The input bytearray to encode.

    Returns:
        bytearray: The COBS-encoded byte sequence.

    Raises:
        TypeError: If `data` is not a bytearray.
        ValueError: If `data` is empty.
    """
    if not isinstance(data, bytearray):
        raise TypeError("Input data must be a bytearray.")
    if len(data) == 0:
        raise ValueError("Input data must not be empty.")
    if len(data) == 1 and data[0] == 0x00:
        return bytearray([0x01, 0x00]) # special case

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
    encoded[zero_marker_pos] = zero_block_len
    encoded.append(0x00)  # Frame delimiter
    return encoded


def decode(data: Union[str, list, bytearray]) -> bytearray:
    """
    Decodes COBS-encoded data back into its decoded form.

    This function handles input conversion before passing the data
    to `decode_bytearray()`.

    Args:
        data (Union[str, list, bytearray]): The COBS-encoded data.
            - `str`: A hex string (e.g., "00 11 22").
            - `list`: A list of integer values.
            - `bytearray`: A raw bytearray.

    Returns:
        bytearray: The decoded byte sequence.

    Raises:
        TypeError: If `data` is not one of the supported types.
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

    COBS decoding reconstructs the original byte sequence by inserting zero bytes
    at positions indicated by the length markers.

    Args:
        data (bytearray): The COBS-encoded byte sequence.

    Returns:
        bytearray: The original decoded byte sequence.

    Raises:
        TypeError: If `data` is not a bytearray.
        ValueError: If `data` has an invalid format:
            - Must have at least two elements.
            - Must end with a valid frame delimiter (`0x00`).
            - Cannot contain multiple frame delimiters.
            - Must not have invalid zero markers.
    """
    if not isinstance(data, bytearray):
        raise TypeError("Input data must be a bytearray.")
    if len(data) < 2:
        raise ValueError("Input data must have at least two elements.")
    if data[-1] != 0x00:
        raise ValueError("Invalid COBS-encoded data: missing final "
                         "frame delimiter (0x00)")
    if data.count(0x00) > 1:
        raise ValueError("Invalid COBS-encoded data: more than one "
                         "frame delimiter (0x00)")

    # Single zero encoded - special case
    if len(data) == 2 and data[0] == 0x01:
        return bytearray([0x00])

    # Other cases
    idx = 0
    decoded = bytearray()
    while idx < len(data) - 1:
        # first byte will be number of bytes until next delimiter
        bytes_until_delim = data[idx]

        # Ensure zero marker does not point beyond the available data
        if bytes_until_delim + idx >= len(data):
            raise ValueError("Invalid COBS-encoded data: invalid zero marker")

        # Move to data section
        idx += 1
        for _ in range(bytes_until_delim - 1):
            decoded.append(data[idx])
            idx += 1

        # Insert zero unless this was a max-length block (0xff)
        # or at the end of the data
        overhead_byte = bytes_until_delim == 0xff
        data_left_to_decode = idx < len(data) - 1
        if not overhead_byte and data_left_to_decode:
            decoded.append(0x00)

    return decoded
