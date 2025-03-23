#!/usr/bin/env python3

from enum import Enum
from typing import Union
from serial_protocol import utils


class TLVValueReturnType(Enum):
    """
    Supported return types for decoding the value portion of a TLV packet.
    """
    BYTEARRAY = "bytearray"
    INT = "int"
    FLOAT = "float"


class TLVPacket:
    """
    Type-Length-Value packet encoder and decoder.

    This class supports configurable field widths for both the length and value
    fields using `MaxUInt`, and supports IEEE 754 float encoding via `FloatPrecision`.

    Example:
        >>> tlv = TLVPacket()
        >>> packet = tlv.encode(1, 300)
        >>> tlv.decode(packet)
        (1, 2, 300)
    """

    def __init__(self,
                 max_data_length: utils.MaxUInt = utils.MaxUInt.UINT8,
                 max_data_value: utils.MaxUInt = utils.MaxUInt.UINT8,
                 float_byte_size: utils.FloatPrecision = utils.FloatPrecision.FLOAT32):

        self.__max_data_length = utils.coerce_enum(max_data_length, utils.MaxUInt)
        self.__max_data_value = utils.coerce_enum(max_data_value, utils.MaxUInt)
        self.__float_byte_size = utils.coerce_enum(float_byte_size, utils.FloatPrecision)

    @property
    def max_data_length(self) -> utils.MaxUInt:
        return self.__max_data_length

    @max_data_length.setter
    def max_data_length(self, value: utils.MaxUInt):
        self.__max_data_length = utils.coerce_enum(value, utils.MaxUInt)

    @property
    def max_data_value(self) -> utils.MaxUInt:
        return self.__max_data_value

    @max_data_value.setter
    def max_data_value(self, value: utils.MaxUInt):
        self.__max_data_value = utils.coerce_enum(value, utils.MaxUInt)

    @property
    def float_byte_size(self) -> utils.FloatPrecision:
        return self.__float_byte_size

    @float_byte_size.setter
    def float_byte_size(self, value: utils.FloatPrecision):
        self.__float_byte_size = utils.coerce_enum(value, utils.FloatPrecision)

    def encode(self,
               type_: Union[int, bytearray],
               value_: Union[int, float, bytearray]) -> bytearray:
        """
        Encode a TLV packet.

        Args:
            type_ (int | bytearray): Type field (must fit in one byte).
            value_ (int | float | bytearray): Value field to encode.

        Returns:
            bytearray: Encoded TLV packet.

        Example:
            >>> TLVPacket().encode(1, 42)
            bytearray(b'\\x01\\x01\\x00\\x2a')
        """
        type_ = self._validate_and_convert_type(type_)
        value_ = self._validate_and_convert_value(value_)
        length_ = utils.int_to_bytearray(len(value_), self.max_data_length)

        return bytearray(type_ + length_ + value_)

    def decode(self,
               packet: bytearray,
               return_value_as: TLVValueReturnType = TLVValueReturnType.BYTEARRAY
               ) -> tuple[int, int, Union[int, float, bytearray]]:
        """
        Decode a TLV packet and extract type, length, and value.

        Args:
            packet (bytearray): The TLV packet to decode.
            return_value_as (TLVValueReturnType): Desired return type for the value.

        Returns:
            tuple[int, int, int|float|bytearray]: (type, length, decoded value)

        Raises:
            TypeError: If inputs are of incorrect types.
            ValueError: If packet structure is invalid.

        Example:
            >>> tlv = TLVPacket()
            >>> pkt = tlv.encode(1, 123)
            >>> tlv.decode(pkt, TLVValueReturnType.INT)
            (1, 1, 123)
        """
        if not isinstance(packet, bytearray):
            raise TypeError(f"Expected bytearray for packet, got {type(packet).__name__}")
        if not isinstance(return_value_as, TLVValueReturnType):
            raise TypeError(f"Expected TLVValueReturnType, got {type(return_value_as).__name__}")

        num_len_bytes = self.max_data_length.num_bytes
        if len(packet) < 1 + num_len_bytes:
            raise ValueError(f"Packet too short to contain a valid TLV header (got {len(packet)} bytes).")

        type_ = int(packet[0])
        length_ = int.from_bytes(packet[1:num_len_bytes + 1], byteorder='little')
        expected_total_len = 1 + num_len_bytes + length_

        if len(packet) != expected_total_len:
            raise ValueError(
                f"Packet length mismatch: expected {expected_total_len} bytes "
                f"(type=1, length field={length_}), got {len(packet)} bytes."
            )

        value_bytes = packet[num_len_bytes + 1:]
        if return_value_as == TLVValueReturnType.BYTEARRAY:
            value_ = value_bytes
        elif return_value_as == TLVValueReturnType.INT:
            value_ = utils.bytearray_to_int(value_bytes)
        elif return_value_as == TLVValueReturnType.FLOAT:
            value_ = self._decode_float(value_bytes)
        else:
            raise ValueError(f"Unsupported return type: {return_value_as}")

        return type_, length_, value_

    def _decode_float(self, b: bytearray) -> float:
        """Helper to decode float with byte size check."""
        if len(b) != self.float_byte_size.num_bytes:
            raise ValueError(
                f"Float value length mismatch: expected {self.float_byte_size.num_bytes} bytes, got {len(b)}."
            )
        return utils.bytearray_to_float(b, self.float_byte_size)

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

    def _validate_and_convert_value(self, value_: Union[int, float, bytearray]) -> bytearray:
        """
        Validate and convert the value to a bytearray.

        Example:
            >>> TLVPacket()._validate_and_convert_value(42)
            bytearray(b'*')
        """
        if isinstance(value_, int):
            return utils.int_to_bytearray(value_, self.max_data_value)
        if isinstance(value_, float):
            return utils.float_to_bytearray(value_, self.float_byte_size)
        if isinstance(value_, bytearray):
            return value_

        raise TypeError("Input value_ must be an integer, float, or bytearray.")
