#!/usr/bin/env python3

import ast


def bytearray_to_hexstring(data: bytearray, use_0x_format: bool = True) -> str:
    """Converts a bytearray to a hex string with optional '0x' format."""
    fmt = "0x{:02x}" if use_0x_format else "{:02x}"
    return " ".join(fmt.format(x) for x in data)


def hexstring_to_bytearray(hexstr: str) -> bytearray:
    """Detects the hex format and converts it to a bytearray."""
    hexstr = hexstr.strip()

    if is_0x_format(hexstr):
        byte_values = [ast.literal_eval(token) for token in hexstr.split()]
    else:
        byte_values = bytearray.fromhex(hexstr)

    return bytearray(byte_values)


def is_0x_format(hexstr: str) -> bool:
    """Checks if a hex string uses the '0x' format."""
    tokens = hexstr.split()
    if all(token.startswith("0x") for token in tokens):
        return True
    if any(token.startswith("0x") for token in tokens):
        raise ValueError("The hex string contains mixed '0x' and plain hex formats.")
    return False


def bytearray_to_decstring(data: bytearray) -> str:
    """Converts a bytearray to a space-separated decimal string representation."""
    return " ".join("{:03d}".format(x) for x in data)