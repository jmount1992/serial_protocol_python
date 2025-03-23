#!/usr/bin/env python3

import struct
from enum import Enum
from typing import Union
from serial_protocol import utils


class TLVValueReturnType(Enum):
    BYTEARRAY = "bytearray"
    INT = "int"
    FLOAT = "float"


class tlv_packet():

    def __init__(self,
                 max_data_length: utils.MaxUintValues = utils.MaxUintValues.UINT8_MAX,
                 max_data_value: utils.MaxUintValues = utils.MaxUintValues.UINT8_MAX,
                 float_byte_size: utils.FloatByteSize = utils.FloatByteSize.FLOAT32):

        # Check and set properties
        self.__max_data_length = self.__max_data_length_setter(max_data_length)
        self.__max_data_value = self.__max_data_value_setter(max_data_value)
        self.__float_byte_size = self.__float_byte_size_setter(float_byte_size)

    @property
    def max_data_length(self) -> utils.MaxUintValues:
        return utils.MaxUintValues(self.__max_data_length)

    @max_data_length.setter
    def max_data_length(self, value: utils.MaxUintValues):
        self.__max_data_length = self.__max_data_length_setter(value)

    def __max_data_length_setter(self, value: utils.MaxUintValues):
        if not isinstance(value, utils.MaxUintValues):
            if value not in {e.value for e in utils.MaxUintValues}:
                raise ValueError("Invalid value for max_data_length attribute.")
        return value

    @property
    def max_data_value(self) -> utils.MaxUintValues:
        return utils.MaxUintValues(self.__max_data_value)

    @max_data_value.setter
    def max_data_value(self, value: utils.MaxUintValues):
        self.__max_data_value = self.__max_data_value_setter(value)

    def __max_data_value_setter(self, value: utils.MaxUintValues):
        if not isinstance(value, utils.MaxUintValues):
            if value not in {e.value for e in utils.MaxUintValues}:
                raise ValueError("Invalid value for max_data_value attribute.")
        return value

    @property
    def float_byte_size(self) -> utils.FloatByteSize:
        return utils.FloatByteSize(self.__float_byte_size)

    @float_byte_size.setter
    def float_byte_size(self, value: utils.FloatByteSize):
        self.__float_byte_size = self.__float_byte_size_setter(value)

    def __float_byte_size_setter(self, value: utils.FloatByteSize):
        if not isinstance(value, utils.FloatByteSize):
            if value not in {e.value for e in utils.FloatByteSize}:
                raise ValueError("Invalid value for float_byte_size attribute.")
        return value

    def encode(self,
               type_: Union[int, bytearray],
               value_: Union[int, float, bytearray]):
        """
        type_ must be in range [0,255]
        """
        type_ = self.__validate_and_convert_type(type_)
        value_ = self.__validate_and_convert_value(value_)
        length_ = utils.int_to_bytearray(len(value_), self.max_data_length)

        # Assemble and return packet
        return bytearray(type_ + length_ + value_)

    def decode(self, packet: bytearray, 
               return_value_as: TLVValueReturnType = TLVValueReturnType.BYTEARRAY) -> tuple:
        """Decode a TLV packet and return value as bytearray, int, or float.

        Args:
            packet (bytearray): The encoded TLV packet.
            return_value_as (str): One of "bytearray", "int", or "float".

        Returns:
            tuple: (type: int, length: int, value: Union[int, float, bytearray])

        Raises:
            ValueError: If packet is malformed or if value format doesn't match length.
        """
        if isinstance(packet, bytearray) == False:
            raise TypeError("The packet must be of type bytearray.")
        if isinstance(return_value_as, TLVValueReturnType) == False:
            raise TypeError("The return_value_as must be of type TLVValueReturnType.")

        num_len_bytes = utils.number_of_bytes_from_max_value(self.max_data_length)
        if len(packet) < 1 + num_len_bytes:
            raise ValueError(f"Packet is too short to contain a valid TLV header (got {len(packet)} bytes).")

        # Parse type and length
        type_ = int(packet[0])
        length_ = int.from_bytes(packet[1:num_len_bytes+1], byteorder='little')
        expected_total_len = 1 + num_len_bytes + length_
        if len(packet) != expected_total_len:
            raise ValueError(
                f"Packet length mismatch: expected {expected_total_len}"
                f" bytes, got {len(packet)} bytes."
            )

        # Extract value field
        value_bytes = packet[num_len_bytes+1:expected_total_len]

        # Decode value
        if return_value_as == TLVValueReturnType.BYTEARRAY:
            value_ = value_bytes
        elif return_value_as == TLVValueReturnType.INT:
            value_ = int.from_bytes(value_bytes, byteorder='little')
        elif return_value_as == TLVValueReturnType.FLOAT:
            if self.float_byte_size.value != len(value_bytes):
                raise ValueError(
                    "Float value length mismatch:"
                    f"expected {self.float_byte_size.value} bytes,"
                    f"got {len(value_bytes)}."
                )
            format_char = 'f' if self.float_byte_size == utils.FloatByteSize.FLOAT32 else 'd'
            value_ = struct.unpack(format_char, value_bytes)[0]

        return type_, length_, value_

    def __validate_and_convert_type(self,
                                    type_: Union[int, bytearray]
                                    ) -> bytearray:
        """Validate and convert type_ to a bytearray (1-byte identifier)."""
        if not isinstance(type_, (int, bytearray)):
            raise TypeError("Input type_ must be an integer or bytearray.")
        if isinstance(type_, bytearray) and len(type_) != 1:
            raise ValueError("Input type_ must be exactly 1 byte.")
        if isinstance(type_, int):
            if not (0 <= type_ <= 255):
                raise ValueError("Input type_ must be in the range [0,255].")
            type_ = bytearray([type_])
        return type_

    def __validate_and_convert_value(self,
                                     value_: Union[int, float, bytearray]
                                     ) -> bytearray:
        """Convert value_ to the appropriate byte representation."""
        if isinstance(value_, int):
            return utils.int_to_bytearray(value_, self.max_data_value)
        if isinstance(value_, float):
            return utils.float_to_bytearray(value_, self.float_byte_size)
        if isinstance(value_, bytearray):
            return value_

        raise TypeError("Input value_ must be an integer, float, or bytearray.")
