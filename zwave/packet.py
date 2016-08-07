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

import logging

logger = logging.getLogger(__name__)


class Preamble(object):
    """Preamble bytes at the begining of a packet

    SOF - start of frame
    ACK - acknowledgement
    NAK - not acknowledged
    CAN - can't send

    """
    SOF = 0x01
    ACK = 0x06
    NAK = 0x15
    CAN = 0x18

    ALL = set([SOF, ACK, NAK, CAN])


class PacketType(object):
    """Type of packet, request or response

    REQUEST - request
    RESPONSE - response

    """
    REQUEST = 0x00
    RESPONSE = 0x01

    ALL = set([REQUEST, RESPONSE])


class MessageType(object):
    """Specific API call

    """
    NONE = 0x00
    SERIAL_API_GET_INIT_DATA = 0x02
    ZW_GET_CONTROLLER_CAPABILITIES = 0x05
    SERIAL_API_GET_CAPABILITIES = 0x07
    ZW_SEND_DATA = 0x13

    ALL = set([NONE, SERIAL_API_GET_INIT_DATA, ZW_GET_CONTROLLER_CAPABILITIES,
               SERIAL_API_GET_CAPABILITIES, ZW_SEND_DATA])


class Packet(object):
    """A ZWave packet

    Attributes:
        preamble (int): Preamble
        length (int): can be None
        packet_type (int): PacketType can be None
        message_type (int): MessageType can be None
        body (list(int)): bytes of body
        checksum (int): can be None

    """

    def __init__(self, preamble, length=None, packet_type=None,
                 message_type=None, body=None, checksum=None):
        """New ZWave packet

        Arguments:
            preamble (int):

        Keyword Arguments:
            length (int): default is None
            packet_type (int): PacketType, defeault is None
            message_type (int): MessageType, default is None
            body (list(int)): default is empty list
            checksum (int): default is None

        """
        super(Packet, self).__init__()
        self.preamble = preamble
        self.length = length
        self.packet_type = packet_type
        self.message_type = message_type
        self.body = body or list()
        self.checksum = checksum

    def validate_checksum(self):
        """Check if checksum validates for message. If preamble is ACK, NAK, or
        CAN, then the checksum always validates, because there is none

        Return
            True/False

        """
        # No checksum, validates if not SOF
        if self.checksum is None and self.preamble != Preamble.SOF:
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

    def bytes(self):
        """Get the bytes that form this packet

        Return:
            bytearray

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

    @staticmethod
    def create(preamble=Preamble.SOF, packet_type=None, message_type=None,
               body=None):
        """Create a Packet. The checksum is filled in based on the given
        parameters. Note that no logic checks exist to validate the message,
        i.e. you can create an ACK with a body and checksum...

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

            # Skip preamble and start at 0xff
            check = 0xff
            # Length
            check ^= length
            # Packet type
            if packet_type is not None:
                check ^= packet_type
            # Message type
            if message_type is not None:
                check ^= message_type
            # Body
            if body is not None:
                for x in body:
                    check ^= x
            # Final checksum
            checksum = check

        return Packet(preamble, length=length, packet_type=packet_type,
                      message_type=message_type, body=body, checksum=checksum)

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
        packet (Packet): malformed Packet

    """

    def __init__(self, error, packet):
        super(PacketParserException, self).__init__(error)
        self.packet = packet


class PacketParserUnknownPreamble(PacketParserException):
    """PacketParser error due to unsupported Preamble

    """

    def __init__(self, preamble):
        super(PacketParserUnknownPreamble, self).__init__(
                'Unknown packet preamble [0x%02x]' % (preamble), None)


class PacketParserUnknownType(PacketParserException):
    """PacketParser error due to unsupported PacketType

    """

    def __init__(self, packet_type, packet):
        super(PacketParserUnknownType, self).__init__(
                'Unknown packet type [0x%02x]' % (packet_type), packet)


class PacketParserBadChecksum(PacketParserException):
    """PacketParser error due to a bad checksum

    """

    def __init__(self, packet):
        super(PacketParserBadChecksum, self).__init__('Bad packet checksum',
                                                      packet)


class PacketParserBadLength(PacketParserException):
    """PacketParser error due to a bad length

    """

    def __init__(self, packet):
        super(PacketParserBadLength, self).__init__('Packet too length',
                                                    packet)


class PacketParser(object):
    """Parses packet bytes into Packets

    Attributes:
        packet (Packet): ongoing packet
        state (int): current packet parsing state

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
        self.packet = None
        self.state = PacketParser.State.PREAMBLE

    def _reset_state(self):
        """Reset state and return current packet

        Return:
            Packet

        """
        packet, self.packet = self.packet, None
        self.state = PacketParser.State.PREAMBLE
        return packet

    def update(self, n):
        """Update the parse state

        Arguments:
            n (int): byte value

        Return:
            Packet if finished parsing, else None

        Raises:
            ValueError: if n is not in range of [0, 255]
            PacketParserUnknownPreamble; if bad Preamble
            PacketParserBadLength: if bad length
            PacketParserUnknownType: if unknown PacketType
            PacketParserBadChecksum: if bad checksum

        """

        # Get integer from byte
        if (n < 0 or n > 255):
            raise ValueError('n must be within byte range of [0, 255]')

        if self.state == PacketParser.State.PREAMBLE:
            # Got preamble
            if n not in Preamble.ALL:
                raise PacketParserUnknownPreamble(n)

            if n == Preamble.ACK:
                # ACKs are just 0x06
                return PacketACK()
            elif n == Preamble.NAK:
                # NACKs are just 0x15
                return PacketNAK()
            elif n == Preamble.CAN:
                # CANs are just 0x18
                return PacketCAN()
            else:
                # Create new packet
                self.packet = Packet(n)
                self.state = PacketParser.State.LENGTH

        elif self.state == PacketParser.State.LENGTH:
            # Got length

            self.packet.length = n

            if n in (0, 1, 2):
                raise PacketParserBadLength(self._reset_state())
            else:
                self.state = PacketParser.State.PACKET_TYPE

        elif self.state == PacketParser.State.PACKET_TYPE:
            # Got packet type

            if n not in PacketType.ALL:
                # Reset
                raise PacketParserUnknownType(n, self._reset_state())
            else:
                # Set packet type
                self.packet.packet_type = n
                self.state = PacketParser.State.MESSAGE_TYPE

        elif self.state == PacketParser.State.MESSAGE_TYPE:
            # Got controller packet type
            if n not in MessageType.ALL:
                logger.warn('Unknown byte [%02x] waiting for message type ', n)

            self.packet.message_type = n

            # Done, because message type counts towards length
            if self.packet.length == 3:
                # Just get checksum
                self.state = PacketParser.State.CHECKSUM
            else:
                # Get body bytes
                self.state = PacketParser.State.BODY

        elif self.state == PacketParser.State.BODY:
            # Get body byte
            self.packet.body.append(n)

            # Subtract 3 for: packet type, message type, checksum
            if len(self.packet.body) == self.packet.length - 3:
                self.state = PacketParser.State.CHECKSUM

        else:  # self.state == PacketParser.State.CHECKSUM
            # Got checksum
            self.packet.checksum = n

            # Return and reset
            if not self.packet.validate_checksum():
                raise PacketParserBadChecksum(self._reset_state())
            else:
                return self._reset_state()
