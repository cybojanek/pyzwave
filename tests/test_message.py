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

from hamcrest import *

from zwave.message import Message
from zwave.message import MessageAck
from zwave.message import MessageNak
from zwave.message import MessageParser
from zwave.message import MessageParserBadChecksum
from zwave.message import MessageParserUnkownMessageType
from zwave.message import MessageParserUnkownPreamble
from zwave.message import MessageParserMessageTooShort


class TestMessage(object):

    def test_ack_message(self):
        """Message only with preamble"""
        message = MessageAck()
        assert_that(message.preamble, equal_to(0x06))
        assert_that(message.length, equal_to(None))
        assert_that(message.message_type, equal_to(None))
        assert_that(message.controller_message_type, equal_to(None))
        assert_that(message.body, has_length(0))
        assert_that(message.checksum, equal_to(None))
        assert_that(message.validate_checksum(), equal_to(True))

        # Check contents
        assert_that(message.bytes(), equal_to(bytearray([0x06])))

        # Check string functions work correctly
        string = "%s %r" % (message, message)

    def test_partial_message(self):
        """Partial messages from errors"""

        ############################# Only length ##############################
        message = Message(0x01, length=0x03)

        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(0x03))
        assert_that(message.message_type, equal_to(None))
        assert_that(message.controller_message_type, equal_to(None))
        assert_that(message.body, has_length(0))
        assert_that(message.checksum, equal_to(None))
        assert_that(message.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(message.bytes(), equal_to(bytearray([0x01, 0x03])))

        # Check string functions work correctly
        string = "%s %r" % (message, message)

        ########################## With message type ###########################
        message = Message(0x01, length=0x03, message_type=0x01)

        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(0x03))
        assert_that(message.message_type, equal_to(0x01))
        assert_that(message.controller_message_type, equal_to(None))
        assert_that(message.body, has_length(0))
        assert_that(message.checksum, equal_to(None))
        assert_that(message.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(message.bytes(), equal_to(bytearray([0x01, 0x03, 0x01])))

        # Check string functions work correctly
        string = "%s %r" % (message, message)

        ##################### With controller message type #####################
        message = Message(0x01, length=0x03, message_type=0x01,
                          controller_message_type=0x02)

        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(0x03))
        assert_that(message.message_type, equal_to(0x01))
        assert_that(message.controller_message_type, equal_to(0x02))
        assert_that(message.body, has_length(0))
        assert_that(message.checksum, equal_to(None))
        assert_that(message.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(message.bytes(), equal_to(bytearray([0x01, 0x03, 0x01,
                                                         0x02])))

        # Check string functions work correctly
        string = "%s %r" % (message, message)

        ############################## With body ###############################
        message = Message(0x01, length=0x03, message_type=0x01,
                          controller_message_type=0x02,
                          body=bytearray([0x04, 0x05]))

        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(0x03))
        assert_that(message.message_type, equal_to(0x01))
        assert_that(message.controller_message_type, equal_to(0x02))
        assert_that(message.body, equal_to(bytearray([0x04, 0x05])))
        assert_that(message.checksum, equal_to(None))
        assert_that(message.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(message.bytes(), equal_to(bytearray([0x01, 0x03, 0x01,
                                                         0x02, 0x04, 0x05])))

        # Check string functions work correctly
        string = "%s %r" % (message, message)

        ############################ With checksum #############################
        message = Message(0x01, length=0x03, message_type=0x01,
                          controller_message_type=0x02,
                          body=bytearray([0x04, 0x05]), checksum=0x34)

        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(0x03))
        assert_that(message.message_type, equal_to(0x01))
        assert_that(message.controller_message_type, equal_to(0x02))
        assert_that(message.body, equal_to(bytearray([0x04, 0x05])))
        assert_that(message.checksum, equal_to(0x34))
        assert_that(message.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(message.bytes(), equal_to(bytearray([0x01, 0x03, 0x01,
                                                         0x02, 0x04, 0x05,
                                                         0x34])))

        # Check string functions work correctly
        string = "%s %r" % (message, message)

    def test_create_message_no_body(self):
        """Create message with no body"""
        message = Message.create(message_type=0x00,
                                 controller_message_type=0x02)

        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(3))
        assert_that(message.message_type, equal_to(0x00))
        assert_that(message.controller_message_type, equal_to(0x02))
        assert_that(message.body, has_length(0))
        assert_that(message.checksum, equal_to(0xfe))
        assert_that(message.validate_checksum(), equal_to(True))

    def test_create_message_with_body(self):
        """Create message with a body"""
        # NOTE: bad preamble, but continue
        message = Message.create(preamble=0x04, message_type=0x00,
                                 controller_message_type=0x02,
                                 body=bytearray([0x45, 0x78]))

        assert_that(message.preamble, equal_to(0x04))
        assert_that(message.length, equal_to(5))
        assert_that(message.message_type, equal_to(0x00))
        assert_that(message.controller_message_type, equal_to(0x02))
        assert_that(message.body, equal_to(bytearray([0x45, 0x78])))
        assert_that(message.checksum, equal_to(0xc5))
        assert_that(message.validate_checksum(), equal_to(True))


class TestMessageParser(object):

    def setup(self):
        self.parser = MessageParser()

    def parse_message(self, bs):
        for b in bs[0:-1]:
            message = self.parser.update(bytearray([b]))
            assert_that(message, equal_to(None))
        return self.parser.update(bytearray([bs[-1]]))

    def test_unknown_preamble(self):
        """Unknown preamble"""
        assert_that(calling(self.parser.update).with_args(b'\x02'),
                    raises(MessageParserUnkownPreamble))

    def test_unknown_message_type(self):
        """Unknown message type"""
        # SOF
        assert_that(self.parser.update(b'\x01'), equal_to(None))
        # Length
        assert_that(self.parser.update(b'\x03'), equal_to(None))
        # Bad message type
        assert_that(calling(self.parser.update).with_args(b'\x02'),
                    raises(MessageParserUnkownMessageType))

    def test_ack(self):
        """ACK message"""
        message = self.parser.update(b'\x06')
        assert_that(message, instance_of(MessageAck))

    def test_nak(self):
        """NAK message"""
        message = self.parser.update(b'\x15')
        assert_that(message, instance_of(MessageNak))

    def test_bad_checksum(self):
        """Bad checksum"""
        message = (b'\x01\x25\x01\x02\x05\x00\x1d\x07\x00\x00\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                   b'\x00\x00\x00\x11\x00\x27\x00\x14\x05\x00\xe0')
        assert_that(calling(self.parse_message).with_args(message),
                    raises(MessageParserBadChecksum))

    def test_bad_length_message(self):
        """Edge case zero length message"""
        message = (b'\x01\x00')
        assert_that(calling(self.parse_message).with_args(message),
                    raises(MessageParserMessageTooShort))

        message = (b'\x01\x01\x01')
        assert_that(calling(self.parse_message).with_args(message),
                    raises(MessageParserMessageTooShort))

        message = (b'\x01\x02\x01\x02')
        assert_that(calling(self.parse_message).with_args(message),
                    raises(MessageParserMessageTooShort))

    def test_three_length_message(self):
        """Edge case minimum"""
        assert_that(self.parser.update(b'\x01'), equal_to(None))
        assert_that(self.parser.update(b'\x03'), equal_to(None))
        assert_that(self.parser.update(b'\x01'), equal_to(None))
        assert_that(self.parser.update(b'\x02'), equal_to(None))
        message = self.parser.update(b'\xff')
        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(3))
        assert_that(message.message_type, equal_to(0x01))
        assert_that(message.controller_message_type, equal_to(0x02))
        assert_that(message.body, has_length(0))
        assert_that(message.checksum, equal_to(0xff))

    def test_four_length_message(self):
        """Edge case minimum + 1"""
        assert_that(self.parser.update(b'\x01'), equal_to(None))
        assert_that(self.parser.update(b'\x04'), equal_to(None))
        assert_that(self.parser.update(b'\x01'), equal_to(None))
        assert_that(self.parser.update(b'\x02'), equal_to(None))
        assert_that(self.parser.update(b'\x03'), equal_to(None))
        message = self.parser.update(b'\xfb')
        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(4))
        assert_that(message.message_type, equal_to(0x01))
        assert_that(message.controller_message_type, equal_to(0x02))
        assert_that(message.body, equal_to(bytearray([0x03])))
        assert_that(message.checksum, equal_to(0xfb))

    def test_full_message(self):
        """Full message parsing"""

        # Discovery message used as sample
        message = self.parse_message(b'\x01\x25\x01\x02\x05\x00\x1d\x07\x00'
                                     b'\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                     b'\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                     b'\x00\x00\x00\x00\x11\x00\x27\x00\x14'
                                     b'\x05\x00\xe1')
        assert_that(message.preamble, equal_to(0x01))
        assert_that(message.length, equal_to(0x25))
        assert_that(message.message_type, equal_to(0x01))
        assert_that(message.controller_message_type, equal_to(0x02))
        assert_that(message.body, equal_to(b'\x05\x00\x1d\x07\x00\x00\x00\x00'
                                           b'\x00\x00\x00\x00\x00\x00\x00\x00'
                                           b'\x00\x00\x00\x00\x00\x00\x00\x00'
                                           b'\x00\x00\x00\x11\x00\x27\x00\x14'
                                           b'\x05\x00'))
        assert_that(message.checksum, equal_to(0xe1))

