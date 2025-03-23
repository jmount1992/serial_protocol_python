#!/usr/bin/env python3

from enum import Enum
import struct


class MaxUintValues(Enum):
    UINT8_MAX = 255
    UINT16_MAX = 65535
    UINT32_MAX = 4294967295


class FloatByteSize(Enum):
    FLOAT32 = 4  # IEEE 754 single-precision
    FLOAT64 = 8  # IEEE 754 double-precision


def bytearray_to_hexstring(data: bytearray, use_0x_format: bool = True) -> str:
    """
    Converts a bytearray to a space-separated hex string representation.

    Args:
        data (bytearray): The input byte sequence.
        use_0x_format (bool, optional): If True, prefixes each byte with '0x'.
                                        Defaults to True.

    Returns:
        str: A space-separated string of hexadecimal values.

    Example:
        >>> bytearray_to_hexstring(bytearray([0, 17, 34]), use_0x_format=True)
        '0x00 0x11 0x22'
        >>> bytearray_to_hexstring(bytearray([0, 17, 34]), use_0x_format=False)
        '00 11 22'
    """
    fmt = "0x{:02x}" if use_0x_format else "{:02x}"
    return " ".join(fmt.format(x) for x in data)


def hexstring_to_bytearray(hexstr: str) -> bytearray:
    """
    Converts a space-separated hex string into a bytearray.

    Detects whether the input uses '0x' prefixes or plain hex values and 
    converts accordingly. Raises an error if mixed formats are detected.

    Args:
        hexstr (str): A space-separated string of hexadecimal values.

    Returns:
        bytearray: The corresponding byte sequence.

    Raises:
        ValueError: If the string contains a mix of '0x' prefixed and plain hex formats.

    Example:
        >>> hexstring_to_bytearray("0x00 0x11 0xff")
        bytearray(b'\\x00\\x11\\xff')
        >>> hexstring_to_bytearray("00 11 ff")
        bytearray(b'\\x00\\x11\\xff')
        >>> hexstring_to_bytearray("00 0x11 ff")
        ValueError: The hex string contains mixed '0x' and plain hex formats.
    """
    hexstr = hexstr.strip()

    if is_0x_format(hexstr):
        byte_values = [int(token, 16) for token in hexstr.split()]
    else:
        byte_values = bytearray.fromhex(hexstr)

    return bytearray(byte_values)


def is_0x_format(hexstr: str) -> bool:
    """
    Determines whether a given hex string uses the '0x' prefix format.

    Ensures that the entire string follows a consistent format, either all
    '0x' prefixed or all plain hex. Raises an error if mixed formats are found.

    Args:
        hexstr (str): A space-separated string of hexadecimal values.

    Returns:
        bool: True if all tokens use the '0x' prefix, False if all are plain hex.

    Raises:
        ValueError: If the string contains a mix of '0x' prefixed and plain hex formats.

    Example:
        >>> is_0x_format("0x00 0x11 0xff")
        True
        >>> is_0x_format("00 11 ff")
        False
        >>> is_0x_format("00 0x11 ff")
        ValueError: The hex string contains mixed '0x' and plain hex formats.
    """
    tokens = hexstr.split()
    if all(token.startswith("0x") for token in tokens):
        return True
    if any(token.startswith("0x") for token in tokens):
        raise ValueError("The hex string contains mixed '0x' and plain hex formats.")
    return False


def bytearray_to_decstring(data: bytearray) -> str:
    """
    Converts a bytearray to a space-separated decimal string representation.

    Each byte value is represented as a three-digit decimal number (zero-padded).

    Args:
        data (bytearray): The input byte sequence.

    Returns:
        str: A space-separated string of decimal values.

    Example:
        >>> bytearray_to_decstring(bytearray([0, 17, 255]))
        '000 017 255'
    """
    return " ".join("{:03d}".format(x) for x in data)


def number_of_bytes_from_max_value(max_value: MaxUintValues) -> int:
    # Ensure max value is of MaxUintValues type and if not
    # make sure it is a valid value of one of the MaxUintValues before
    # converting it to the MaxUintValues enum type
    if not isinstance(max_value, MaxUintValues):
        if max_value not in {e.value for e in MaxUintValues}:
            raise ValueError("Invalid value for max_data_length attribute.")
        max_value = MaxUintValues(max_value)

    # Determine byte size needed (default to single byte, max 255 value)
    num_bytes = 1
    if max_value == MaxUintValues.UINT16_MAX:
        num_bytes = 2
    elif max_value == MaxUintValues.UINT32_MAX:
        num_bytes = 4
    return num_bytes


def int_to_bytearray(value: int, max_value: MaxUintValues) -> bytearray:
    """Convert an integer to a bytearray of appropriate length based on max value.

    Args:
        value (int): The integer value to encode.
        max_value (MaxUintValues): The max value determining byte size.

    Returns:
        bytearray: The encoded integer as bytes.

    Raises:
        ValueError: If max_value is not a valid MaxUintValues.
        ValueError: If value is out of range.
    """
    # Ensure max value is of MaxUintValues type and if not
    # make sure it is a valid value of one of the MaxUintValues before
    # converting it to the MaxUintValues enum type
    if not isinstance(max_value, MaxUintValues):
        if max_value not in {e.value for e in MaxUintValues}:
            raise ValueError("Invalid value for max_data_length attribute.")
        max_value = MaxUintValues(max_value)

    # Determine byte size needed (default to single byte, max 255 value)
    num_bytes = number_of_bytes_from_max_value(max_value)

    # Determine actual max value and ensure value is in range
    max_value = (2**(num_bytes*8)) - 1
    if not (0 <= value <= max_value):
        raise ValueError(f"value must be in range [0, {max_value}].")

    # Convert integer to bytearray (Little Endian)
    return bytearray(value.to_bytes(num_bytes, byteorder="little"))


def float_to_bytearray(value: float, num_bytes: FloatByteSize) -> bytearray:
    """Convert a float to a 4-byte or 8-byte bytearray using IEEE 754 format.

    Args:
        value (float): The float to encode.
        num_bytes (FloatByteSize): The number of bytes (4 or 8).

    Returns:
        bytearray: The encoded float as bytes.

    Raises:
        ValueError: If num_bytes is not a valid FloatByteSize.
    """
    # Ensure max value is of FloatByteSize type and if not
    # make sure it is a valid value of one of the FloatByteSize before
    # converting it to the FloatByteSize enum type
    if not isinstance(num_bytes, FloatByteSize):
        if num_bytes not in {e.value for e in FloatByteSize}:
            raise ValueError("Invalid value for float_byte_size attribute.")
        num_bytes = FloatByteSize(num_bytes)

    # Determine format char
    format_char = "f"
    if num_bytes == FloatByteSize.FLOAT64:
        format_char = "d"

    # Convert float to bytearray (Little Endian)
    return bytearray(struct.pack(format_char, value))
