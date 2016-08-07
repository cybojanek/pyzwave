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

from zwave.packet import Packet
from zwave.packet import PacketACK
from zwave.packet import PacketNAK
from zwave.packet import PacketCAN
from zwave.packet import PacketParser
from zwave.packet import PacketParserBadChecksum
from zwave.packet import PacketParserUnknownType
from zwave.packet import PacketParserUnknownPreamble
from zwave.packet import PacketParserBadLength


class TestPacket(object):

    def test_ack_message(self):
        """Message only with preamble"""
        packet = PacketACK()

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x06, None, None, None, [], None)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(True))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([0x06])))

        # Check string functions work correctly
        string = "%s %r" % (packet, packet)

    def test_partial_message(self):
        """Partial messages from errors"""

        ############################# Only length #############################
        packet = Packet(0x01, length=0x03)

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x01, 0x03, None, None, [], None)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([0x01, 0x03])))

        # Check string functions work correctly
        string = "%s %r" % (packet, packet)

        ########################## With message type ##########################
        packet = Packet(0x01, length=0x03, packet_type=0x01)

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x01, 0x03, 0x01, None, [], None)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([0x01, 0x03, 0x01])))

        # Check string functions work correctly
        string = "%s %r" % (packet, packet)

        ##################### With controller message type ####################
        packet = Packet(0x01, length=0x03, packet_type=0x01, message_type=0x02)

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x01, 0x03, 0x01, 0x02, [], None)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([0x01, 0x03, 0x01,
                                                        0x02])))

        # Check string functions work correctly
        string = "%s %r" % (packet, packet)

        ############################## With body ##############################
        packet = Packet(0x01, length=0x03, packet_type=0x01, message_type=0x02,
                        body=[0x04, 0x05])

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x01, 0x03, 0x01, 0x02, [0x04, 0x05], None)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([0x01, 0x03, 0x01, 0x02,
                                                        0x04, 0x05])))

        # Check string functions work correctly
        string = "%s %r" % (packet, packet)

        ############################ With checksum ############################
        packet = Packet(0x01, length=0x03, packet_type=0x01, message_type=0x02,
                        body=[0x04, 0x05], checksum=0x34)

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x01, 0x03, 0x01, 0x02, [0x04, 0x05], 0x34)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(False))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([0x01, 0x03, 0x01, 0x02,
                                                        0x04, 0x05, 0x34])))

        # Check string functions work correctly
        string = "%s %r" % (packet, packet)

    def test_create_message_no_body(self):
        """Create message with no body"""
        packet = Packet.create(packet_type=0x00, message_type=0x02)

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x01, 0x03, 0x00, 0x02, [], 0xfe)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(True))

    def test_create_message_with_body(self):
        """Create message with a body"""
        # NOTE: bad preamble, but continue
        packet = Packet.create(preamble=0x04, packet_type=0x00,
                               message_type=0x02, body=[0x45, 0x78])

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x04, 0x05, 0x00, 0x02, [0x45, 0x78], 0xc5)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(True))


class TestPacketParser(object):

    def setup(self):
        self.parser = PacketParser()

    def parse_packet(self, bs):
        """Helper method to send multiple bytes. Expects that no packet will be
        returned until last byte, when this function returns that value

        Arguments:
            bs list(int): body bytes to send

        Return:
            Packet or None

        """
        for b in bs[0:-1]:
            packet = self.parser.update(b)
            assert_that(packet, none())
        return self.parser.update(bs[-1])

    def test_bad_value(self):
        """Bad byte value"""
        assert_that(calling(self.parser.update).with_args(-1),
                    raises(ValueError))

        assert_that(calling(self.parser.update).with_args(256),
                    raises(ValueError))

    def test_unknown_preamble(self):
        """Unknown preamble"""
        assert_that(calling(self.parser.update).with_args(0x02),
                    raises(PacketParserUnknownPreamble))

    def test_unknown_packet_type(self):
        """Unknown packet type"""
        # SOF
        assert_that(self.parser.update(0x01), none())
        # Length
        assert_that(self.parser.update(0x03), none())
        # Bad packet type
        assert_that(calling(self.parser.update).with_args(0x02),
                    raises(PacketParserUnknownType))

    def test_unknown_message_type(self):
        """Unknown message type"""
        # Should be handled graceully with a warning in the log
        packet = (b'\x01\x03\x00\xFF\x03')
        assert_that(self.parse_packet(packet), not_none())

    def test_ack(self):
        """ACK packet"""
        packet = self.parser.update(0x06)
        assert_that(packet, instance_of(PacketACK))

    def test_nak(self):
        """NAK packet"""
        packet = self.parser.update(0x15)
        assert_that(packet, instance_of(PacketNAK))

    def test_can(self):
        """CAN packet"""
        packet = self.parser.update(0x18)
        assert_that(packet, instance_of(PacketCAN))

    def test_bad_checksum(self):
        """Bad checksum"""
        packet = (b'\x01\x25\x01\x02\x05\x00\x1d\x07\x00\x00\x00\x00\x00\x00'
                  b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                  b'\x00\x00\x00\x11\x00\x27\x00\x14\x05\x00\xe0')
        assert_that(calling(self.parse_packet).with_args(packet),
                    raises(PacketParserBadChecksum))

    def test_bad_length_packet(self):
        """Bad length packet"""
        packet = (b'\x01\x00')
        assert_that(calling(self.parse_packet).with_args(packet),
                    raises(PacketParserBadLength))

        packet = (b'\x01\x01\x01')
        assert_that(calling(self.parse_packet).with_args(packet),
                    raises(PacketParserBadLength))

        packet = (b'\x01\x02\x01\x02')
        assert_that(calling(self.parse_packet).with_args(packet),
                    raises(PacketParserBadLength))

    def test_three_length_packet(self):
        """Edge case minimum"""
        assert_that(self.parser.update(0x01), none())
        assert_that(self.parser.update(0x03), none())
        assert_that(self.parser.update(0x01), none())
        assert_that(self.parser.update(0x02), none())
        packet = self.parser.update(0xff)

        assert_that(packet.preamble, equal_to(0x01))
        assert_that(packet.length, equal_to(3))
        assert_that(packet.packet_type, equal_to(0x01))
        assert_that(packet.message_type, equal_to(0x02))
        assert_that(packet.body, has_length(0))
        assert_that(packet.checksum, equal_to(0xff))

    def test_four_length_packet(self):
        """Edge case minimum + 1"""
        assert_that(self.parser.update(0x01), none())
        assert_that(self.parser.update(0x04), none())
        assert_that(self.parser.update(0x01), none())
        assert_that(self.parser.update(0x02), none())
        assert_that(self.parser.update(0x03), none())
        packet = self.parser.update(0xfb)

        assert_that(packet.preamble, equal_to(0x01))
        assert_that(packet.length, equal_to(4))
        assert_that(packet.packet_type, equal_to(0x01))
        assert_that(packet.message_type, equal_to(0x02))
        assert_that(packet.body, equal_to([0x03]))
        assert_that(packet.checksum, equal_to(0xfb))

    def test_full_packet(self):
        """Full packet parsing"""

        # SERIAL_API_GET_INIT_DATA response used as sample
        packet = self.parse_packet(b'\x01\x25\x01\x02\x05\x00\x1d\x07\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x11\x00\x27\x00\x14\x05\x00\xe1')
        assert_that(packet.preamble, equal_to(0x01))
        assert_that(packet.length, equal_to(0x25))
        assert_that(packet.packet_type, equal_to(0x01))
        assert_that(packet.message_type, equal_to(0x02))
        assert_that(packet.body, equal_to([
                0x05, 0x00, 0x1d, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x11, 0x00, 0x27,
                0x00, 0x14, 0x05, 0x00]))
        assert_that(packet.checksum, equal_to(0xe1))
