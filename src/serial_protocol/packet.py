#!/usr/bin/env python3

import crc
from dataclasses import dataclass
from typing import Union, Optional
from serial_protocol import tlv, cobs, utils


@dataclass
class SerialPacketStruct:
    """
    A simple dataclass representing the components of a serial packet.

    Fields:
        device_id (Optional[int]): Optional device identifier (prepended to payload).
        type_ (int): TLV type identifier.
        value_ (int|float|bytearray): The data payload to encode.
        format_ (ValueFormat): Format used to encode the value.
    """
    device_id: Optional[int] = None
    type_: int = None
    value_: Union[int, float, bytearray] = None
    format_: utils.ValueFormat = None

    def __str__(self):
        return (
            f"Device ID: {self.device_id}, "
            f"Type: {self.type_}, "
            f"Value: {self.value_}, "
            f"Format: {self.format_}"
        )


class SerialPacket:
    """
    SerialPacket wraps TLV encoding with optional device ID, CRC checksums, and optional COBS encoding.

    Args:
        max_data_length (ValueFormat | str): TLV max data length field width (UINT8, UINT16, etc.)
        crc_ (crc.Calculator): CRC algorithm to use (default = CRC16-XMODEM)
        crc_format (ValueFormat): How many bytes to use for the CRC checksum (default = UINT16)

    Usage:
        >>> pkt = SerialPacket()
        >>> encoded = pkt.encode(1, 42, ValueFormat.UINT8)
    """

    def __init__(self, max_data_length: Union[utils.ValueFormat, str] = utils.ValueFormat.UINT8,
                 crc_=crc.Crc16.XMODEM,
                 crc_format: utils.ValueFormat = utils.ValueFormat.UINT16):
        self._tlv_packet = tlv.TLVPacket(max_data_length)
        self._crc_calc = crc.Calculator(crc_)
        self._crc_format = crc_format

    def encode(self,
               data_: Union[int, SerialPacketStruct],
               value_: Union[int, float, bytearray] = None,
               format_: utils.ValueFormat = None,
               device_id: int = None,
               cobs_encode: bool = False) -> bytearray:
        """
        Encode a serial packet with TLV, CRC, optional device ID, and optional COBS wrapping.

        Args:
            data_ (int or SerialPacketStruct): Type ID or full packet structure.
            value_ (int|float|bytearray, optional): Payload (if not using a struct).
            format_ (ValueFormat, optional): Format used to encode the value (if not using a struct).
            device_id (int, optional): Optional device ID byte to prepend (if not using a struct).
            cobs_encode (bool): Whether to apply COBS encoding (default: False).

        Returns:
            bytearray: Fully encoded serial packet.
        """
        if isinstance(data_, SerialPacketStruct):
            return self._encode(data_.type_, data_.value_,
                                data_.format_, data_.device_id, cobs_encode)
        elif isinstance(data_, int):
            return self._encode(data_, value_, format_, device_id, cobs_encode)

        raise ValueError("The data_ argument must be of type int or "
                         f"SerialPacketStruct not {type(data_)}")

    def decode(self,
               data_: bytearray,
               format_: utils.ValueFormat = None,
               device_id: bool = False,
               cobs_encoded: bool = False) -> SerialPacketStruct:
        """
        Decode a serial packet into its structured components.

        This method reverses the encoding process by optionally COBS-decoding the data,
        validating the CRC checksum, extracting a device ID (if present), validating
        the TLV length field, and optionally decoding the value into an int or float
        based on the provided `format_`.

        Args:
            data_ (bytearray): Raw packet data, potentially COBS encoded and containing CRC.
            format_ (ValueFormat, optional): Expected format of the payload value.
                                             If not provided, the value is returned as raw bytes.
            device_id (bool): Whether the packet includes a one-byte device ID prefix.
            cobs_encoded (bool): Whether the input data is COBS-encoded.

        Returns:
            SerialPacketStruct: Parsed and decoded structure with optional device ID, type,
                                decoded value, and format.

        Raises:
            TypeError: If the data_ input is not a bytearray.
            ValueError: If CRC validation fails or TLV length field is inconsistent.
        """
        if not isinstance(data_, bytearray):
            raise TypeError("Input must be a bytearray")

        # Perform COBS decoding if necessary
        if cobs_encoded:
            data_ = cobs.decode(data_)

        # Verify Checksum
        num_bytes = self._crc_format.num_bytes
        sent_checksum = data_[-num_bytes:]
        data_ = data_[:-num_bytes]
        checksum = self._crc_calc.checksum(data_)
        checksum = utils.int_to_bytearray(checksum, self._crc_format)
        if checksum != sent_checksum:
            raise ValueError("Checksum verification failed. "
                             f"Received checksum: {utils.bytearray_to_hexstring(sent_checksum)}. "
                             f"Calculated checksum: {utils.bytearray_to_hexstring(checksum)}.")

        # Extract Device ID if necessary
        retval = SerialPacketStruct()
        if device_id:
            retval.device_id = data_[0]
            data_ = data_[1:]

        # Validate length
        max_data_length = self._tlv_packet.max_data_length
        num_len_bytes = max_data_length.num_bytes
        length_field = utils.bytearray_to_int(data_[1:1+num_len_bytes], "little")
        if length_field != len(data_) - 1 - num_len_bytes:
            raise ValueError("Invalid length")

        # Extract Data
        retval.type_ = data_[0]
        retval.value_ = data_[1+num_len_bytes:]

        # Convert value to format if specified
        if format_ is not None:
            retval.format_ = format_
            retval.value_ = utils.bytearray_to_value(retval.value_, format_)

        return retval

    def _encode(self,
                type_: int,
                value_: Union[int, float, bytearray],
                format_: utils.ValueFormat,
                device_id: int = None,
                cobs_encode: bool = False) -> bytearray:
        """
        Internal implementation of the encode logic with all components unpacked.
        """
        # TLV encode packet and preprend device ID if supplied
        packet_ = self._tlv_packet.encode(type_, value_, format_)
        if device_id is not None:
            packet_ = bytearray([device_id]) + packet_

        # Calculate checksum and add to packet
        checksum = self._crc_calc.checksum(packet_)
        checksum = utils.int_to_bytearray(checksum, self._crc_format)
        packet_ = packet_ + checksum

        # Cobs encode packet if enabled
        if cobs_encode:
            packet_ = cobs.encode(packet_)
        return packet_
