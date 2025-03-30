#!/usr/bin/env python3


import struct
from enum import Enum
from typing import Union

########################
# --- ENUM HELPERS --- #
########################


class ValueFormat(Enum):
    """
    Enumeration of supported value formats, including unsigned integers and IEEE 754 floats.

    Each member defines:
    - Number of bytes (1, 2, 4, or 8)
    - Category: either 'uint' or 'float'
    - A descriptive label (e.g., 'uint16')
    - A format character used by `struct` (only for float types)

    Example:
        >>> ValueFormat.FLOAT32.num_bytes
        4
        >>> ValueFormat.UINT16.category
        'uint'
    """
    UINT8 = (1, "uint", "uint8", None)
    UINT16 = (2, "uint", "uint16", None)
    UINT32 = (4, "uint", "uint32", None)
    FLOAT32 = (4, "float", "float32", 'f')
    FLOAT64 = (8, "float", "float64", 'd')

    @property
    def num_bytes(self) -> int:
        """Number of bytes used to store the value."""
        return self.value[0]

    @property
    def category(self) -> str:
        """The category of the value type: 'uint' or 'float'."""
        return self.value[1]

    @property
    def label(self) -> str:
        """A human-readable string label for the format."""
        return self.value[2]

    @property
    def format_char(self) -> str:
        """Struct format character used for float encoding/decoding."""
        return self.value[3]

    @property
    def max_value(self) -> int:
        """Maximum value (only valid for unsigned int types)."""
        if self.is_uint():
            return 2**(self.num_bytes * 8) - 1
        return None

    def is_uint(self) -> bool:
        """Return True if format represents an unsigned integer."""
        return self.category == "uint"

    def is_float(self) -> bool:
        """Return True if format represents a float."""
        return self.category == "float"

    @classmethod
    def coerce(cls, value: Union['ValueFormat', str]) -> 'ValueFormat':
        """
        Ensure the input is a ValueFormat enum instance.

        Args:
            value (ValueFormat or str): Value to convert. If str, must match a member's label.

        Returns:
            ValueFormat: The coerced enum value.

        Raises:
            ValueError: If input doesn't match any label.
        """
        if isinstance(value, cls):
            return value
        for member in cls:
            if value == member.label:
                return member
        raise ValueError(f"Invalid value for {cls.__name__}: {value}")

    def __str__(self):
        return self.label


##########################
# --- FORMAT HELPERS --- #
##########################

def is_0x_format(hex_string: str) -> bool:
    """
    Determines whether a given hex string uses the '0x' prefix format.

    Args:
        hex_string (str): A space-separated string of hexadecimal values.

    Returns:
        bool: True if all tokens use the '0x' prefix, False if all are plain hex.

    Raises:
        ValueError: If the string contains a mix of formats.

    Example:
        >>> is_0x_format("0x01 0x02 0x03")
        True
        >>> is_0x_format("01 02 03")
        False
        >>> is_0x_format("0x01 02")
        ValueError
    """
    tokens = hex_string.split()
    has_0x = [token.startswith("0x") for token in tokens]
    if all(has_0x):
        return True
    if any(has_0x):
        raise ValueError("The hex string contains mixed '0x' and plain hex formats.")
    return False


##############################
# --- CONVERSION HELPERS --- #
##############################

def bytearray_to_hexstring(data: bytearray, use_0x_format: bool = True) -> str:
    """
    Converts a bytearray to a space-separated hex string.

    Args:
        data (bytearray): The bytearray to convert.
        use_0x_format (bool): Whether to include '0x' prefix. Default is True.

    Returns:
        str: A space-separated hex string.

    Example:
        >>> bytearray_to_hexstring(bytearray([0, 15, 255]))
        '0x00 0x0f 0xff'
        >>> bytearray_to_hexstring(bytearray([0, 15, 255]), use_0x_format=False)
        '00 0f ff'
    """
    fmt = "0x{:02x}" if use_0x_format else "{:02x}"
    return " ".join(fmt.format(x) for x in data)


def hexstring_to_bytearray(hex_string: str) -> bytearray:
    """
    Converts a space-separated hex string into a bytearray.

    Args:
        hex_string (str): The hex string to convert.

    Returns:
        bytearray: The resulting bytearray.

    Raises:
        ValueError: If mixed '0x' and plain hex formats are used.

    Example:
        >>> hexstring_to_bytearray("0x00 0x0f 0xff")
        bytearray(b'\x00\x0f\xff')
        >>> hexstring_to_bytearray("00 0f ff")
        bytearray(b'\x00\x0f\xff')
    """
    hex_string = hex_string.strip()
    if is_0x_format(hex_string):
        return bytearray(int(token, 16) for token in hex_string.split())
    return bytearray.fromhex(hex_string)


def bytearray_to_decstring(data: bytearray) -> str:
    """
    Converts a bytearray to a space-separated decimal string.

    Args:
        data (bytearray): The bytearray to convert.

    Returns:
        str: A string of zero-padded 3-digit decimal numbers.

    Example:
        >>> bytearray_to_decstring(bytearray([1, 15, 255]))
        '001 015 255'
    """
    return " ".join("{:03d}".format(x) for x in data)


def int_to_bytearray(value: int, format_: ValueFormat, byteorder: str = "little") -> bytearray:
    """
    Converts an integer into a bytearray based on a value format.

    Args:
        value (int): The integer value to convert.
        format_ (format): The format type. Cannot be FLOAT32 or FLOAT64.
        byteorder (str): Byte order ('little' or 'big'). Default is 'little'.

    Returns:
        bytearray: The resulting bytearray.

    Raises:
        ValueError: If value is out of bounds.

    Example:
        >>> int_to_bytearray(1025, ValueFormat.UINT16)
        bytearray(b'\x01\x04')
    """
    format_ = ValueFormat.coerce(format_)
    if format_.is_float():
        raise ValueError("The format cannot be FLOAT32 or FLOAT64.")
    if not (0 <= value <= format_.max_value):
        raise ValueError(f"Value must be in range [0, {format_.max_value}].")
    return bytearray(value.to_bytes(format_.num_bytes, byteorder=byteorder))


def bytearray_to_int(value: bytearray, byteorder: str = "little") -> int:
    """
    Converts a bytearray to an integer.

    Args:
        value (bytearray): The input bytearray.
        byteorder (str): Byte order ('little' or 'big'). Default is 'little'.

    Returns:
        int: The resulting integer.

    Example:
        >>> bytearray_to_int(bytearray([1, 4]))
        1025
    """
    if not isinstance(value, bytearray):
        raise TypeError("Input value must be of type bytearray.")
    return int.from_bytes(value, byteorder=byteorder)


def float_to_bytearray(value: float, precision: ValueFormat, byteorder: str = "little") -> bytearray:
    """
    Convert a float to a bytearray using IEEE 754 format.

    Args:
        value (float): The float to encode.
        precision (ValueFormat): Must be FLOAT32 or FLOAT64.
        byteorder (str): Byte order ('little' or 'big').

    Returns:
        bytearray: Encoded float bytes.

    Raises:
        ValueError: If precision is not a valid float format.

    Example:
        >>> float_to_bytearray(3.14, ValueFormat.FLOAT32)
        bytearray(b'\\xc3\\xf5H@')
    """
    precision = ValueFormat.coerce(value=precision)
    if not precision.is_float():
        raise ValueError("The precision must be FLOAT32 or FLOAT64.")
    packed = struct.pack(precision.format_char, value)
    return bytearray(packed if byteorder == "little" else packed[::-1])


def bytearray_to_float(value: bytearray, precision: ValueFormat, byteorder: str = "little") -> float:
    """
    Decode a float from a bytearray using IEEE 754 format.

    Args:
        value (bytearray): Raw float bytes.
        precision (ValueFormat): Must be FLOAT32 or FLOAT64.
        byteorder (str): Byte order ('little' or 'big').

    Returns:
        float: Decoded float value.

    Raises:
        TypeError: If input is not a bytearray.
        ValueError: If precision is not a valid float format.

    Example:
        >>> bytearray_to_float(bytearray(b'\\xc3\\xf5H@'), ValueFormat.FLOAT32)
        3.14
    """
    if not isinstance(value, bytearray):
        raise TypeError("Input value must be of type bytearray.")
    precision = ValueFormat.coerce(value=precision)
    if not precision.is_float():
        raise ValueError("The precision must be FLOAT32 or FLOAT64.")
    byte_seq = bytes(value if byteorder == "little" else value[::-1])
    return struct.unpack(precision.format_char, byte_seq)[0]
