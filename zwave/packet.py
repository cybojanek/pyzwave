"""
Copyright (C) 2016 Jan Kasiak

This file is part of pyzwave.

    pyzwave is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pyzwave is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with pyzwave.  If not, see <http://www.gnu.org/licenses/>.
"""

from typing import ByteString
from typing import List

import logging


logger = logging.getLogger(__name__)


class Preamble(object):
    """Preamble bytes at the begining of a packet

    Attributes:
        SOF (int): start of frame
        ACK (int): acknowledged
        NAK (int): not acknowledged
        CAN (int): can't acknowledge
        ALL (:obj:`set` of :obj:`int`): all preamble types

    """
    SOF = 0x01
    ACK = 0x06
    NAK = 0x15
    CAN = 0x18

    ALL = set([SOF, ACK, NAK, CAN])


class PacketType(object):
    """Type of packet, request or response

    Attributes:
        REQUEST (int): request
        RESPONSE (int): response
        ALL (:obj:`set` of :obj:`int`): all packet types

    """
    REQUEST = 0x00
    RESPONSE = 0x01

    ALL = set([REQUEST, RESPONSE])


class MessageType(object):
    """Specific API call

    Attributes:
        NONE (int):
        SERIAL_API_GET_INIT_DATA (int):
        APPLICATION_COMMAND_HANDLER (int):
        ZW_GET_CONTROLLER_CAPABILITIES (int):
        SERIAL_API_GET_CAPABILITIES (int):
        ZW_SEND_DATA (int):
        ZW_APPLICATION_UPDATE (int):
        ALL (:obj:`set` of :obj:`int`): all message types

    """
    NONE = 0x00
    SERIAL_API_GET_INIT_DATA = 0x02
    APPLICATION_COMMAND_HANDLER = 0x04
    ZW_GET_CONTROLLER_CAPABILITIES = 0x05
    SERIAL_API_GET_CAPABILITIES = 0x07
    ZW_SEND_DATA = 0x13
    ZW_APPLICATION_UPDATE = 0x49

    ALL = set([NONE, SERIAL_API_GET_INIT_DATA, APPLICATION_COMMAND_HANDLER,
               ZW_GET_CONTROLLER_CAPABILITIES, SERIAL_API_GET_CAPABILITIES,
               ZW_SEND_DATA, ZW_APPLICATION_UPDATE])


class Packet(object):
    """A ZWave packet

    Args:
        preamble (int):
        length (int, optional): default is None
        packet_type (int, optional): PacketType, defeault is None
        message_type (int, optional): MessageType, default is None
        body (:obj:`list` of :obj:`int`, optional): default is empty list
        checksum (int, optional): default is None

    Attributes:
        preamble (int): Preamble
        length (int): can be None
        packet_type (int): PacketType can be None
        message_type (int): MessageType can be None
        body (:obj:`list` of :obj:`int`): bytes of body
        checksum (int): can be None

        special (bool): if one of ACK, NAK, CAN
        request (bool): if PacketType.REQUEST
        response (bool): if PacketType.RESPONSE

    Raises:
        ValueError: if packet bytes are invalid

    """

    def __init__(self, preamble: int, length: int=None, packet_type: int=None,
                 message_type: int=None, body: List[int]=None,
                 checksum: int=None):
        super(Packet, self).__init__()

        self.preamble = preamble
        self.length = length
        self.packet_type = packet_type
        self.message_type = message_type
        self.body = body or list()
        self.checksum = checksum

        # Check preamble
        if (preamble in (Preamble.ACK, Preamble.NAK, Preamble.CAN)):
            # Single byte packet
            if ((length, packet_type, message_type, body, checksum) !=
                    (None, None, None, None, None)):
                raise ValueError('ACK, NAK, CAN must be single byte packets')
        else:
            # Only SOF
            if preamble != Preamble.SOF:
                raise ValueError('Unknown Preamble:0x%02x' % (preamble))

            # Length is: packet_type + message_type + body + checksum
            if length is None:
                raise ValueError('Length cannot be None')
            if 3 + len(self.body) != length:
                raise ValueError('Length does not match: 0x%02x != 0x%02x' % (
                                 length, 3 + len(self.body)))

            # Must be known
            if packet_type is None:
                raise ValueError('Packet type for SOF cannot be None')
            if packet_type not in PacketType.ALL:
                raise ValueError('Unknown packet type: 0x%02x' % (packet_type))

            # Must be known
            if message_type is None:
                raise ValueError('Packet type for SOF cannot be None')
            if message_type not in MessageType.ALL:
                raise ValueError('Unknown message type: 0x%02x' % (
                    message_type))

            # Only allow bytes within [0x00, 0xff]
            if len(list(filter(lambda x: x < 0 or x > 255, self.body))) > 0:
                raise ValueError('Body contains non-byte range values')

            # Checksum
            if not self.validate_checksum():
                raise ValueError('Checksum failed to validate')

    @property
    def special(self) -> bool:
        return (self.preamble in (Preamble.ACK, Preamble.NAK, Preamble.CAN))

    @property
    def request(self) -> bool:
        return (self.packet_type == PacketType.REQUEST)

    @property
    def response(self) -> bool:
        return (self.packet_type == PacketType.RESPONSE)

    def validate_checksum(self) -> bool:
        """Check if checksum validates for message. If preamble is ACK, NAK, or
        CAN, then the checksum always validates, because there is none

        Return
            True/False

        """
        # No checksum, validates if not SOF
        if self.checksum is None and self.special:
            return True

        # Skip preamble and checksum
        b = self.bytes()[1:-1]
        # Checksum starts with 0xff
        check = 0xff
        for x in b:
            # XOR bytes
            check ^= x
        # Compare
        return check == self.checksum

    def bytes(self) -> bytes:
        """Get the bytes that form this packet

        Returns:
            bytes

        """
        b = bytearray()
        b.append(self.preamble)
        if self.length is not None:
            b.append(self.length)
        if self.packet_type is not None:
            b.append(self.packet_type)
        if self.message_type is not None:
            b.append(self.message_type)
        for x in self.body:
            b.append(x)
        if self.checksum is not None:
            b.append(self.checksum)
        return b

    @classmethod
    def create(cls, preamble: int=Preamble.SOF, packet_type: int=None,
               message_type: int=None, body: List[int]=None) -> 'Packet':
        """Create a Packet. The checksum is filled in based on the given
        parameters.

        Keyword Arguments:
            preamble (int): Preamble, default is SOF
            packet_type (int): PacketType default is None
            message_type (int): MessageType, default is None
            body (list(int)): default is None

        Return:
            Packet

        """
        length = None
        checksum = None

        # Get length, excluding preamble
        computed_length = 0
        # Add packet type
        if packet_type is not None:
            computed_length += 1
        # Add message type
        if message_type is not None:
            computed_length += 1
        # Add body
        computed_length += 0 if body is None else len(body)

        # Add checksum if theres something to checksum
        if computed_length > 0:
            # Length is bytes to checksum and checksum
            length = computed_length + 1
            checksum = Packet.compute_checksum(length, packet_type,
                                               message_type, body)

        return Packet(preamble, length=length, packet_type=packet_type,
                      message_type=message_type, body=body, checksum=checksum)

    @classmethod
    def compute_checksum(cls, length: int, packet_type: int, message_type: int,
                         body: List[int]=None):
        check = 0xff ^ length ^ packet_type ^ message_type
        if body is not None:
            for x in body:
                check ^= x
        return check

    def __str__(self):
        return 'Packet: P:[0x%02x] L:[%s] T:[%s] M:[%s] B:[%s] C:[%s]' % (
                self.preamble,
                '    ' if self.length is None else '0x%02x' % (self.length),
                '    ' if self.packet_type is None else '0x%02x' % (
                        self.packet_type),
                '    ' if self.message_type is None else '0x%02x' % (
                        self.message_type),
                ', '.join(['0x%02x' % x for x in self.body]),
                '    ' if self.checksum is None else '0x%02x' % (
                        self.checksum))

    def __repr__(self):
        return 'Packet: [%s]' % (self.bytes())


class PacketACK(Packet):
    """A simple ACK packet

    """

    def __init__(self):
        super(PacketACK, self).__init__(Preamble.ACK)


class PacketNAK(Packet):
    """A simple NAK packet

    """

    def __init__(self):
        super(PacketNAK, self).__init__(Preamble.NAK)


class PacketCAN(Packet):
    """A simple CAN packet

    """

    def __init__(self):
        super(PacketCAN, self).__init__(Preamble.CAN)


class PacketParserException(Exception):
    """A PacketParser Exception

    Attributes:
        error (str): message

    """

    def __init__(self, error: str):
        super(PacketParserException, self).__init__(error)


class PacketParserBadLength(PacketParserException):
    """PacketParser error due to a bad length

    """

    def __init__(self, length: int):
        super(PacketParserBadLength, self).__init__(
            'Bad packet length [0x%02x]' % (length))


class PacketParserUnknownPreamble(PacketParserException):
    """PacketParser error due to unsupported Preamble

    """

    def __init__(self, preamble: int):
        super(PacketParserUnknownPreamble, self).__init__(
            'Unknown packet preamble [0x%02x]' % (preamble))


class PacketParserUnknownPacketType(PacketParserException):
    """PacketParser error due to unsupported PacketType

    """

    def __init__(self, packet_type: int):
        super(PacketParserUnknownPacketType, self).__init__(
            'Unknown packet type [0x%02x]' % (packet_type))


class PacketParserUnknownMessageType(PacketParserException):
    """PacketParser error due to unsupported MessageType

    """

    def __init__(self, message_type: int):
        super(PacketParserUnknownMessageType, self).__init__(
            'Unknown message type [0x%02x]' % (message_type))


class PacketParserBadChecksum(PacketParserException):
    """PacketParser error due to a bad checksum

    """

    def __init__(self, checksum: int):
        super(PacketParserBadChecksum, self).__init__(
            'Bad packet checksum [0x%02x]' % (checksum))


class PacketParser(object):
    """Parses packet bytes into Packets

    Attributes:
        packet (Packet): ongoing packet
        state (int): current packet parsing state one of PacketParser.State

    """

    class State(object):
        """Internal parsing state

        Attributes:

            PREAMBLE (int): waiting for Preamble byte
            LENGTH (int): waiting for length
            PACKET_TYPE (int): waiting for PacketType
            MESSAGE_TYPE (int): waiting for MessageType
            BODY (int): waiting for body bytes
            CHECKSUM (int): waiting for checksum

        """
        PREAMBLE = 1
        LENGTH = 2
        PACKET_TYPE = 3
        MESSAGE_TYPE = 4
        BODY = 5
        CHECKSUM = 6

    def __init__(self):
        super(PacketParser, self).__init__()
        self._reset_state()

    def _reset_state(self):
        """Reset state and return current packet

        """
        self._state = PacketParser.State.PREAMBLE
        self._length = 0
        self._packet_type = 0
        self._message_type = 0
        self._body = list()
        self._checksum = 0

    def update(self, n: int) -> Packet:
        """Update the parse state

        Arguments:
            n (int): byte value

        Returns:
            Packet: if finished parsing, else None

        Raises:
            ValueError: if n is not in range of [0, 255]
            PacketParserUnknownPreamble; if bad Preamble
            PacketParserBadLength: if bad length
            PacketParserUnknownPacketType: if unknown PacketType
            PacketParserBadChecksum: if bad checksum

        """

        # Get integer from byte
        if (n < 0 or n > 255):
            raise ValueError('n must be within byte range of [0, 255]')

        if self._state == PacketParser.State.PREAMBLE:
            # Got preamble
            if n not in Preamble.ALL:
                self._reset_state()
                raise PacketParserUnknownPreamble(n)

            if n == Preamble.ACK:
                # ACKs are just 0x06
                self._reset_state()
                return PacketACK()
            elif n == Preamble.NAK:
                # NACKs are just 0x15
                self._reset_state()
                return PacketNAK()
            elif n == Preamble.CAN:
                # CANs are just 0x18
                self._reset_state()
                return PacketCAN()
            else: # SOF
                self._state = PacketParser.State.LENGTH

        elif self._state == PacketParser.State.LENGTH:
            # Got length
            self._length = n

            if n in (0, 1, 2):
                self._reset_state()
                raise PacketParserBadLength(n)
            else:
                self._state = PacketParser.State.PACKET_TYPE

        elif self._state == PacketParser.State.PACKET_TYPE:
            # Got packet type

            if n not in PacketType.ALL:
                # Reset
                self._reset_state()
                raise PacketParserUnknownPacketType(n)
            else:
                # Set packet type
                self._packet_type = n
                self._state = PacketParser.State.MESSAGE_TYPE

        elif self._state == PacketParser.State.MESSAGE_TYPE:
            # Got message type

            if n not in MessageType.ALL:
                self._reset_state()
                raise PacketParserUnknownMessageType(n)

            self._message_type = n

            # Done, because message type counts towards length
            if self._length == 3:
                # Just get checksum
                self._state = PacketParser.State.CHECKSUM
            else:
                # Get body bytes
                self._state = PacketParser.State.BODY

        elif self._state == PacketParser.State.BODY:
            # Get body byte
            self._body.append(n)

            # Subtract 3 for: packet type, message type, checksum
            if len(self._body) == self._length - 3:
                self._state = PacketParser.State.CHECKSUM

        else:  # self._state == PacketParser.State.CHECKSUM
            # Got checksum
            self._checksum = n
            checksum = Packet.compute_checksum(
                self._length, self._packet_type, self._message_type,
                self._body)

            # Return and reset
            if self._checksum != checksum:
                self._reset_state()
                raise PacketParserBadChecksum(self._checksum)
            else:
                packet = Packet(Preamble.SOF, length=self._length,
                                packet_type=self._packet_type,
                                message_type=self._message_type,
                                body=self._body, checksum=self._checksum)
                self._reset_state()
                return packet
