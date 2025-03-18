#!/usr/bin/env python3


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