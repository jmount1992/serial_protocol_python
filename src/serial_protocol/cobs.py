#!/usr/bin/env python3

import ast
from typing import Union


def bytearray_to_hexstring(data: bytearray, use_0x_format: bool = True) -> str:
    fmt = "0x{:02x}" if use_0x_format else "{:02x}"
    return " ".join(fmt.format(x) for x in data)


def bytearray_to_string(data: bytearray) -> str:
    return " ".join("{:03d}".format(x) for x in data)


def hexstring_to_bytearray(hexstr: str) -> bytearray:
    """
    Detects the hex format and converts it to a bytearray.
    Supports both '0x' prefixed and plain hex strings.
    """
    hexstr = hexstr.strip()

    if is_0x_format(hexstr):
        byte_values = [ast.literal_eval(token) for token in hexstr.split()]
    else:
        byte_values = bytearray.fromhex(hexstr)

    return bytearray(byte_values)


def is_0x_format(hexstr: str) -> bool:
    """Check if a hex string uses the '0x' format."""
    tokens = hexstr.split()
    if all(token.startswith("0x") for token in tokens):
        return True
    if any(token.startswith("0x") for token in tokens):
        err = "The hex string contains mixed '0x' and plain hex formats."
        raise ValueError(err)
    return False


def encode(data: Union[str, list, bytearray]) -> bytearray:
    if not isinstance(data, bytearray):
        if isinstance(data, str):
            bytes = hexstring_to_bytearray(data)
        elif isinstance(data, list):
            bytes = bytearray(data)
    else:
        bytes = data[:]

    encoded = bytearray([0x00])  # with place holder for first marker
    zero_block_len = 1  # Length counter for zero markers
    zero_marker_pos = 0  # Position of the current zero marker

    for byte in bytes:
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


def decode(data: bytearray) -> bytearray:
    bytes = data[:]  # Copy input data
    decoded = bytearray()

    num_bytes_until_zero = bytes[0] - 1  # index of first zero
    overhead_byte_added = (0xff == bytes[0])  # set to true if more than 255 bytes before next zero in decoded data
    for byte in bytes[1:]:
        if byte == 0x00:
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
