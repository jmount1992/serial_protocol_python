#!/usr/bin/env python3

from enum import Enum
from typing import Union
from serial_protocol import utils


class TLVPacket:
    """
    Type-Length-Value packet encoder and decoder.

    This class supports configurable field widths for both the data length and encode/decode value
    fields using `ValueFormat`.

    Example:
        >>> tlv = TLVPacket()
        >>> packet = tlv.encode(1, 300)
        >>> tlv.decode(packet)
        (1, 2, 300)
    """

    def __init__(self,
                 max_data_length: utils.ValueFormat = utils.ValueFormat.UINT8):
        """
        Initialize a TLV packet encoder/decoder.

        Args:
            max_data_length (ValueFormat): Format used to encode the length field.

        Raises:
            ValueError: If the format is not an unsigned integer type.
        """
        self.__max_data_length = utils.ValueFormat.coerce(max_data_length)
        if not self.max_data_length.is_uint():
            raise ValueError("The max data length must be of category uint "
                             f"not {self.max_data_length.category}")

    @property
    def max_data_length(self) -> utils.ValueFormat:
        """Format used to encode the length field (must be an unsigned integer)."""
        return self.__max_data_length

    @max_data_length.setter
    def max_data_length(self, value: utils.ValueFormat):
        self.__max_data_length = utils.ValueFormat.coerce(value)

    def encode(self,
               type_: Union[int, bytearray],
               value_: Union[int, float, bytearray],
               format_: utils.ValueFormat) -> bytearray:
        """
        Encode a TLV packet.

        Args:
            type_ (int | bytearray): Type field (must fit in one byte).
            value_ (int | float | bytearray): Value field to encode.
            format_ (ValueFormat): Format of the value.

        Returns:
            bytearray: Encoded TLV packet.

        Example:
            >>> TLVPacket().encode(1, 42)
            bytearray(b'\\x01\\x01\\x00\\x2a')
        """
        type_ = self._validate_and_convert_type(type_)
        value_ = self._validate_and_convert_value(value_, format_)
        length_ = utils.int_to_bytearray(len(value_), self.max_data_length)

        return bytearray(type_ + length_ + value_)

    def decode(self,
               packet: bytearray,
               value_format: utils.ValueFormat | None = None
               ) -> tuple[int, int, Union[int, float, bytearray]]:
        """
        Decode a TLV packet and extract type, length, and value.

        Args:
            packet (bytearray): The TLV packet to decode.
            value_format (ValueFormat, optional): If provided, decode the value accordingly.
                                                If None, the value is returned as a raw bytearray.

        Returns:
            tuple[int, int, int|float|bytearray]: (type, length, decoded value)

        Raises:
            TypeError: If input is not a bytearray.
            ValueError: If packet structure is invalid or decoding fails.

        Example:
            >>> tlv = TLVPacket()
            >>> pkt = tlv.encode(1, 3.14, ValueFormat.FLOAT32)
            >>> tlv.decode(pkt, ValueFormat.FLOAT32)
            (1, 4, 3.14)
        """
        if not isinstance(packet, bytearray):
            raise TypeError(f"Expected bytearray for packet, got {type(packet).__name__}")

        num_len_bytes = self.max_data_length.num_bytes
        if len(packet) < 1 + num_len_bytes:
            raise ValueError(f"Packet too short to contain a valid TLV header (got {len(packet)} bytes).")

        type_ = int(packet[0])
        length_ = int.from_bytes(packet[1:num_len_bytes + 1], byteorder='little')
        expected_total_len = 1 + num_len_bytes + length_

        if len(packet) != expected_total_len:
            raise ValueError(
                f"Packet length mismatch: expected {expected_total_len} bytes "
                f"(type={type_}, length field={length_}), got {len(packet)} bytes."
            )

        value_bytes = packet[num_len_bytes + 1:]

        # Handle decoding based on ValueFormat
        if value_format is None:
            value_ = value_bytes
        else:
            value_ = utils.bytearray_to_value(value_bytes, value_format)

        return type_, length_, value_

    def _validate_and_convert_type(self, type_: Union[int, bytearray]) -> bytearray:
        """
        Validate and convert the type field to a single-byte bytearray.

        Example:
            >>> TLVPacket()._validate_and_convert_type(5)
            bytearray(b'\\x05')
        """
        if isinstance(type_, int):
            if not (0 <= type_ <= 255):
                raise ValueError("Input type_ must be in the range [0, 255].")
            return bytearray([type_])
        if isinstance(type_, bytearray):
            if len(type_) != 1:
                raise ValueError("Input type_ must be exactly 1 byte.")
            return type_

        raise TypeError("Input type_ must be an integer or a 1-byte bytearray.")

    def _validate_and_convert_value(self,
                                    value_: Union[int, float, bytearray],
                                    format_: utils.ValueFormat) -> bytearray:
        """
        Validate and convert the value to a bytearray.

        Example:
            >>> TLVPacket()._validate_and_convert_value(42, ValueFormat.UINT8)
            bytearray(b'*')
        """
        format_ = utils.ValueFormat.coerce(format_)

        if isinstance(value_, bytearray):
            return value_

        if format_.is_float():
            if not isinstance(value_, float):
                raise TypeError(f"Expected float for format {format_.label}, got {type(value_).__name__}")
            return utils.float_to_bytearray(value_, format_)

        if format_.is_uint():
            if not isinstance(value_, int):
                raise TypeError(f"Expected integer for format {format_.label}, got {type(value_).__name__}")
            return utils.int_to_bytearray(value_, format_)

        raise TypeError(f"Unsupported format type: {format_.label}")
