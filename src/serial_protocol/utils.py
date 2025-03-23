#!/usr/bin/env python3

from enum import Enum
import struct


########################
# --- ENUM HELPERS --- #
########################

class MaxUInt(Enum):
    """
    Enumeration of maximum unsigned integer values with associated byte sizes.

    Members:
        UINT8:  8-bit unsigned integer (1 byte, max 255)
        UINT16: 16-bit unsigned integer (2 bytes, max 65535)
        UINT32: 32-bit unsigned integer (4 bytes, max 4294967295)

    Properties:
        num_bytes (int): Number of bytes required to represent the value.
        max_value (int): Maximum value for the unsigned integer type.

    Example:
        >>> MaxUInt.UINT16.num_bytes
        2
        >>> MaxUInt.UINT16.max_value
        65535
    """
    UINT8 = (1, 255)
    UINT16 = (2, 65535)
    UINT32 = (4, 4294967295)

    @property
    def num_bytes(self) -> int:
        return self.value[0]

    @property
    def max_value(self) -> int:
        return self.value[1]


class FloatPrecision(Enum):
    """
    Enumeration of IEEE 754 floating point precisions with byte size and format.

    Members:
        FLOAT32: 32-bit (4-byte) single-precision float ('f' format character)
        FLOAT64: 64-bit (8-byte) double-precision float ('d' format character)

    Properties:
        num_bytes (int): Number of bytes used to represent the float.
        format_char (str): Format character used for struct packing/unpacking.

    Example:
        >>> FloatPrecision.FLOAT64.num_bytes
        8
        >>> FloatPrecision.FLOAT64.format_char
        'd'
    """
    FLOAT32 = (4, 'f')  # IEEE 754 single-precision
    FLOAT64 = (8, 'd')  # IEEE 754 double-precision

    @property
    def num_bytes(self) -> int:
        return self.value[0]

    @property
    def format_char(self):
        return self.value[1]


def coerce_enum(value, enum_class):
    """
    Ensures that a given value is an instance of the provided Enum class.

    Args:
        value: The value to check or convert.
        enum_class (Enum): The target Enum class.

    Returns:
        Enum: An instance of the Enum class.

    Raises:
        ValueError: If value cannot be converted to the Enum.
    """
    if isinstance(value, enum_class):
        return value
    try:
        return enum_class(value)
    except ValueError:
        raise ValueError(f"Invalid value for {enum_class.__name__}.")


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


def int_to_bytearray(value: int, max_uint: MaxUInt, byteorder: str = "little") -> bytearray:
    """
    Converts an integer into a bytearray based on the MaxUInt limit.

    Args:
        value (int): The integer value to convert.
        max_uint (MaxUInt): The maximum uint type.
        byteorder (str): Byte order ('little' or 'big'). Default is 'little'.

    Returns:
        bytearray: The resulting bytearray.

    Raises:
        ValueError: If value is out of bounds.

    Example:
        >>> int_to_bytearray(1025, MaxUInt.UINT16)
        bytearray(b'\x01\x04')
    """
    max_uint = coerce_enum(value=max_uint, enum_class=MaxUInt)
    if not (0 <= value <= max_uint.max_value):
        raise ValueError(f"Value must be in range [0, {max_uint.max_value}].")
    return bytearray(value.to_bytes(max_uint.num_bytes, byteorder=byteorder))


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


def float_to_bytearray(value: float, precision: FloatPrecision, byteorder: str = "little") -> bytearray:
    """
    Converts a float to a bytearray using IEEE 754 format.

    Args:
        value (float): The float to convert.
        precision (FloatPrecision): Desired float precision.
        byteorder (str): Byte order ('little' or 'big'). Default is 'little'.

    Returns:
        bytearray: The resulting bytearray.

    Example:
        >>> float_to_bytearray(3.14, FloatPrecision.FLOAT32)
        bytearray(b'\xc3\xf5H@')
    """
    precision = coerce_enum(value=precision, enum_class=FloatPrecision)
    packed = struct.pack(precision.format_char, value)
    return bytearray(packed if byteorder == "little" else packed[::-1])


def bytearray_to_float(value: bytearray, precision: FloatPrecision, byteorder: str = "little") -> float:
    """
    Converts a bytearray to a float using IEEE 754 format.

    Args:
        value (bytearray): The bytearray to convert.
        precision (FloatPrecision): Desired float precision.
        byteorder (str): Byte order ('little' or 'big'). Default is 'little'.

    Returns:
        float: The resulting float.

    Example:
        >>> bytearray_to_float(bytearray(b'\xc3\xf5H@'), FloatPrecision.FLOAT32)
        3.14
    """
    if not isinstance(value, bytearray):
        raise TypeError("Input value must be of type bytearray.")
    precision = coerce_enum(value=precision, enum_class=FloatPrecision)
    byte_seq = bytes(value if byteorder == "little" else value[::-1])
    return struct.unpack(precision.format_char, byte_seq)[0]
