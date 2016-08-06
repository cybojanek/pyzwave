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
    """Preamble bytes at the begining of a message

    SOF - start of frame
    ACK - acknowledgement
    NAK - not acknowledged
    CAN - ???

    """
    SOF = 0x01
    ACK = 0x06
    NAK = 0x15
    CAN = 0x18

    ALL = set([SOF, ACK, NAK, CAN])


class MessageType(object):
    """Type of message, request or response

    """
    REQUEST = 0x00
    RESPONSE = 0x01

    ALL = set([REQUEST, RESPONSE])


class ControllerMessageType(object):
    """Type of message, specific API call

    """
    NONE = 0x00
    SERIAL_API_GET_INIT_DATA = 0x02

    ALL = set([NONE, SERIAL_API_GET_INIT_DATA])


class Message(object):

    def __init__(self, preamble, length=None, message_type=None,
                 controller_message_type=None, body=None, checksum=None):
        super(Message, self).__init__()
        self.preamble = preamble
        self.length = length
        self.message_type = message_type
        self.controller_message_type = controller_message_type
        self.body = body or bytearray()
        self.checksum = checksum

    def validate_checksum(self):
        # No checksum, validates
        if self.checksum is None and self.preamble in (Preamble.ACK, Preamble.NAK):
            return True

        # Skip preamble and checksum
        b = self.bytes()[1:-1]
        check = 0xff
        for x in b:
            check ^= x
        return check == self.checksum

    def bytes(self):
        b = bytearray()
        b.append(self.preamble)
        if self.length is not None:
            b.append(self.length)
        if self.message_type is not None:
            b.append(self.message_type)
        if self.controller_message_type is not None:
            b.append(self.controller_message_type)
        b += self.body
        if self.checksum is not None:
            b.append(self.checksum)
        return b

    @staticmethod
    def create(preamble=Preamble.SOF, message_type=None,
               controller_message_type=None, body=None):
        length = None
        checksum = None

        # Get length, excluding preamble
        computed_length = 0
        if message_type is not None:
            computed_length += 1
        if controller_message_type is not None:
            computed_length += 1
        computed_length += 0 if body is None else len(body)

        # Add checksum if theres something to checksum
        if computed_length > 0:
            # Add checksum bytes
            length = computed_length + 1

            # Skip preamble
            check = 0xff
            # Length
            check ^= length
            # Message type
            if message_type is not None:
                check ^= message_type
            # Controller message type
            if controller_message_type is not None:
                check ^= controller_message_type
            # Body
            if body is not None:
                for x in body:
                    check ^= x
            # Final checksum
            checksum = check

        return Message(preamble, message_type=message_type, length=length,
                       controller_message_type=controller_message_type,
                       body=body, checksum=checksum)

    def __str__(self):
        return 'Message: P:[%#02x] T:[%#02x] L:[%#02x] C:[%#02x] B:[%s] X:[%#02x]' % (
                self.preamble,
                -1 if self.message_type is None else self.message_type,
                -1 if self.length is None else self.length,
                -1 if self.controller_message_type is None else self.controller_message_type,
                self.body, -1 if self.checksum is None else self.checksum)

    def __repr__(self):
        return 'Message: [%s]' % (self.bytes())


class MessageAck(Message):

    def __init__(self):
        super(MessageAck, self).__init__(Preamble.ACK)


class MessageNak(Message):

    def __init__(self):
        super(MessageNak, self).__init__(Preamble.NAK)


class MessageParserException(Exception):
    """docstring for MessageParserException"""
    def __init__(self, error, message):
        super(MessageParserException, self).__init__(error)
        self.message = message


class MessageParserUnkownPreamble(MessageParserException):

    def __init__(self, preamble):
        super(MessageParserUnkownPreamble, self).__init__(
                'Unknown preamble [%02x]' % (preamble), None)


class MessageParserUnkownMessageType(MessageParserException):

    def __init__(self, message_type, message):
        super(MessageParserUnkownMessageType, self).__init__(
                'Unknown message type [%02x]' % (message_type), message)


class MessageParserBadChecksum(MessageParserException):

    def __init__(self, message):
        super(MessageParserBadChecksum, self).__init__(
                'Bad message checksum', message)


class MessageParserMessageTooShort(MessageParserException):

    def __init__(self, message):
        super(MessageParserMessageTooShort, self).__init__(
                'Message too short', message)


class MessageParser(object):

    class MessageParserState(object):
        EMPTY = 0
        LENGTH = 1,
        # PREAMBLE = 1
        MESSAGE_TYPE = 2
        LENGTH = 3
        CONTROLLER_MESSAGE_TYPE = 4
        BODY = 5
        CHECKSUM = 6

    def __init__(self):
        super(MessageParser, self).__init__()
        self.message = None
        self.state = MessageParser.MessageParserState.EMPTY

    def _reset_state(self):
        message, self.message = self.message, None
        self.state = MessageParser.MessageParserState.EMPTY
        return message

    def update(self, x):
        # Get integer from byte
        n = int.from_bytes(x, byteorder='little')

        if self.state == MessageParser.MessageParserState.EMPTY:
            # Got preamble
            if n not in Preamble.ALL:
                raise MessageParserUnkownPreamble(n)

            if n == Preamble.ACK:
                # ACKs are just 0x06
                return MessageAck()
            elif n == Preamble.NAK:
                # NACKs are just 0x15
                return MessageNak()
            else:
                # Create new message
                self.message = Message(n)
                self.state = MessageParser.MessageParserState.LENGTH

        elif self.state == MessageParser.MessageParserState.LENGTH:
            # Got length

            self.message.length = n

            if n in (0, 1, 2):
                raise MessageParserMessageTooShort(self._reset_state())
            else:
                self.state = MessageParser.MessageParserState.MESSAGE_TYPE
        elif self.state == MessageParser.MessageParserState.MESSAGE_TYPE:
            # Got message type

            if n not in MessageType.ALL:
                # Reset
                raise MessageParserUnkownMessageType(n, self._reset_state())
            else:
                # Set message type
                self.message.message_type = n
                self.state = MessageParser.MessageParserState.CONTROLLER_MESSAGE_TYPE
        elif self.state == MessageParser.MessageParserState.CONTROLLER_MESSAGE_TYPE:
            # Got controller message type
            if n not in ControllerMessageType.ALL:
                logger.warn('Unknown byte [%02x] waiting for controller message '
                            'type', n)

            self.message.controller_message_type = n

            # Done, because controller message type counts towards length
            if self.message.length == 3:
                # Just get checksum
                self.state = MessageParser.MessageParserState.CHECKSUM
            else:
                # Get body bytes
                self.state = MessageParser.MessageParserState.BODY
        elif self.state == MessageParser.MessageParserState.BODY:
            # Get body byte
            self.message.body.append(n)

            # Subtract 3 for: message type, controller message type, checksum
            if len(self.message.body) == self.message.length - 3:
                self.state = MessageParser.MessageParserState.CHECKSUM

        else:  # self.state == MessageParser.MessageParserState.CHECKSUM
            # Got checksum
            self.message.checksum = n

            if not self.message.validate_checksum():
                # Reset
                raise MessageParserBadChecksum(self._reset_state())
            else:
                # Return and reset
                return self._reset_state()

