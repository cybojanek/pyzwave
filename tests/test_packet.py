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

from zwave.packet import MessageType
from zwave.packet import Packet
from zwave.packet import PacketACK
from zwave.packet import PacketCAN
from zwave.packet import PacketNAK
from zwave.packet import PacketParser
from zwave.packet import PacketParserBadChecksum
from zwave.packet import PacketParserBadLength
from zwave.packet import PacketParserUnknownMessageType
from zwave.packet import PacketParserUnknownPacketType
from zwave.packet import PacketParserUnknownPreamble
from zwave.packet import PacketType
from zwave.packet import Preamble


class TestPacket(object):

    def test_ack_message(self):
        """Create PacketACK"""
        packet = PacketACK()

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((Preamble.ACK, None, None, None, [], None)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(True))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([Preamble.ACK])))

        # Check properties
        assert_that(packet.special, equal_to(True))
        assert_that(packet.request, equal_to(False))
        assert_that(packet.response, equal_to(False))

        # Check string functions work without error
        string = "%s %r" % (packet, packet)

    def test_nak_message(self):
        """Create PacketNAK"""
        packet = PacketNAK()

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((Preamble.NAK, None, None, None, [], None)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(True))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([Preamble.NAK])))

        # Check properties
        assert_that(packet.special, equal_to(True))
        assert_that(packet.request, equal_to(False))
        assert_that(packet.response, equal_to(False))

        # Check string functions work without error
        string = "%s %r" % (packet, packet)

    def test_can_message(self):
        """Create PacketCAN"""
        packet = PacketCAN()

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((Preamble.CAN, None, None, None, [], None)))
        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(True))

        # Check contents
        assert_that(packet.bytes(), equal_to(bytearray([Preamble.CAN])))

        # Check properties
        assert_that(packet.special, equal_to(True))
        assert_that(packet.request, equal_to(False))
        assert_that(packet.response, equal_to(False))

        # Check string functions work without error
        string = "%s %r" % (packet, packet)

    def test_single_byte_packet_errors(self):
        """Single byte Packet errors"""
        for p in (Preamble.ACK, Preamble.NAK, Preamble.CAN):

            # No length allowed
            assert_that(calling(Packet).with_args(p, length=1),
                        raises(ValueError))

            # No packet_type allowed
            assert_that(calling(Packet).with_args(p, packet_type=PacketType.REQUEST),
                        raises(ValueError))

            # No message_type allowed
            assert_that(calling(Packet).with_args(p, message_type=MessageType.ZW_SEND_DATA),
                        raises(ValueError))

            # No body allowed
            assert_that(calling(Packet).with_args(p, body=[]),
                        raises(ValueError))

            # No checksum allowed
            assert_that(calling(Packet).with_args(p, checksum=0x23),
                        raises(ValueError))

    def test_multi_byte_packet_errors(self):
        """Multi byte Packet errors"""

        # Not SOF and unknown
        assert_that(calling(Packet).with_args(
            0x23, length=0x03, packet_type=PacketType.REQUEST,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, checksum=0xfe),
            raises(ValueError))

        # Not SOF, but known
        assert_that(calling(Packet).with_args(
            Preamble.ACK, length=0x03, packet_type=PacketType.REQUEST,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, checksum=0xfe),
            raises(ValueError))

        # Missing length
        assert_that(calling(Packet).with_args(
            Preamble.SOF, packet_type=PacketType.REQUEST,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, checksum=0xfd),
            raises(ValueError))

        # Bad length
        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x04, packet_type=PacketType.REQUEST,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, checksum=0xf9),
            raises(ValueError))

        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x05, packet_type=PacketType.REQUEST,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, body=[0x67],
            checksum=0x9f),
            raises(ValueError))

        # Missing packet_type
        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x02,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, checksum=0xff),
            raises(ValueError))

        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x03,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, checksum=0xfe),
            raises(ValueError))

        # Unknown packet_type
        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x03, packet_type=0x03,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, checksum=0xfd),
            raises(ValueError))

        # Missing message_type
        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x02, packet_type=PacketType.REQUEST,
            checksum=0xfd),
            raises(ValueError))

        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x03, packet_type=PacketType.REQUEST,
            checksum=0xfc),
            raises(ValueError))

        # Unknown message_type
        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x03, packet_type=PacketType.REQUEST,
            message_type=0xff, checksum=0x03),
            raises(ValueError))

        # Bad checksum
        assert_that(calling(Packet).with_args(
            Preamble.SOF, length=0x03, packet_type=PacketType.REQUEST,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA, checksum=0xfd),
            raises(ValueError))

    def test_create_packet_with_bad_body(self):
        """Create packet with bad body byte"""

        # > 0xff
        assert_that(calling(Packet.create).with_args(
            packet_type=PacketType.RESPONSE,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA,
            body=[256]), raises(ValueError))

        # < 0x00
        assert_that(calling(Packet.create).with_args(
            packet_type=PacketType.RESPONSE,
            message_type=MessageType.SERIAL_API_GET_INIT_DATA,
            body=[-1]), raises(ValueError))

    def test_create_packet_no_body(self):
        """Create packet with no body"""
        packet = Packet.create(packet_type=PacketType.REQUEST,
                               message_type=MessageType.SERIAL_API_GET_INIT_DATA)

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((Preamble.SOF, 0x03, PacketType.REQUEST,
                              MessageType.SERIAL_API_GET_INIT_DATA, [], 0xfe)))

        # Check contents
        assert_that(packet.bytes(), equal_to(
            bytearray([Preamble.SOF, 0x03, PacketType.REQUEST,
                       MessageType.SERIAL_API_GET_INIT_DATA, 0xfe])))

        # Check properties
        assert_that(packet.special, equal_to(False))
        assert_that(packet.request, equal_to(True))
        assert_that(packet.response, equal_to(False))

        # Validate checksum
        assert_that(packet.validate_checksum(), equal_to(True))

    def test_create_packet_with_body(self):
        """Create packet with a body"""
        packet = Packet.create(packet_type=PacketType.RESPONSE,
                               message_type=MessageType.SERIAL_API_GET_INIT_DATA,
                               body=[0x45, 0x78])

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((Preamble.SOF, 0x05, PacketType.RESPONSE,
                              MessageType.SERIAL_API_GET_INIT_DATA,
                              [0x45, 0x78], 0xc4)))

        # Check contents
        assert_that(packet.bytes(), equal_to(
            bytearray([Preamble.SOF, 0x05, PacketType.RESPONSE,
                       MessageType.SERIAL_API_GET_INIT_DATA, 0x45, 0x78,
                       0xc4])))

        # Check properties
        assert_that(packet.special, equal_to(False))
        assert_that(packet.request, equal_to(False))
        assert_that(packet.response, equal_to(True))

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
        assert_that(self.parser.update(Preamble.SOF), none())
        # Length
        assert_that(self.parser.update(0x03), none())
        # Bad packet type
        assert_that(calling(self.parser.update).with_args(0x02),
                    raises(PacketParserUnknownPacketType))

    def test_unknown_message_type(self):
        """Unknown message type"""
        # SOF
        assert_that(self.parser.update(Preamble.SOF), none())
        # Length
        assert_that(self.parser.update(0x03), none())
        # Packet type REQUEST
        assert_that(self.parser.update(PacketType.REQUEST), none())
        # Bad message type
        assert_that(calling(self.parser.update).with_args(0xff),
                    raises(PacketParserUnknownMessageType))

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
        assert_that(packet, instance_of(Packet))

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
