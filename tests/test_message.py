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
from zwave.message import Message
from zwave.message import SerialAPIGetCapabilities
from zwave.message import SerialAPIGetInitData
from zwave.message import ZWGetControllerCapabilities


class TestMessage(object):

    def test_message(self):
        """Message creation from packet"""
        packet = Packet(0x03, length=0x23, packet_type=0x12, message_type=0x13,
                        body=[0x12, 0x32], checksum=0x13)
        message = Message(packet)

        # Check fields
        assert_that((packet.preamble, packet.length, packet.packet_type,
                     packet.message_type, packet.body, packet.checksum),
                    equal_to((0x03, 0x23, 0x12, 0x13, [0x12, 0x32], 0x13)))


class TestSerialAPIGetCapabilities(object):

    def test_bad_creation(self):
        """SerialAPIGetCapabilities bad packet"""
        body = [0x10, 0x20, 0x35, 0x86, 0x19, 0xa7, 0x87, 0x23,
                0x07, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xa7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x81, 0x05,
                0x00, 0x80 ]
        # OK Packet
        packet = Packet(0x01, length=0x2b, packet_type=0x01, message_type=0x07,
                        body=body, checksum=0xe1)
        message = SerialAPIGetCapabilities(packet)

        # Bad preamble
        packet.preamble = 0x00
        assert_that(calling(SerialAPIGetCapabilities).with_args(packet),
                    raises(ValueError))
        packet.preamble = 0x01

        # Bad length
        packet.length = 0x24
        assert_that(calling(SerialAPIGetCapabilities).with_args(packet),
                    raises(ValueError))
        packet.length = 0x2b

        # Bad packet type
        packet.packet_type = 0x00
        assert_that(calling(SerialAPIGetCapabilities).with_args(packet),
                    raises(ValueError))
        packet.packet_type = 0x01

        # Bad message type
        packet.message_type = 0x03
        assert_that(calling(SerialAPIGetCapabilities).with_args(packet),
                    raises(ValueError))
        packet.message_type = 0x07

    def test_good_creation(self):
        """SerialAPIGetCapabilities packet parsing"""
        body = [0x10, 0x20, 0x35, 0x86, 0x19, 0xa7, 0x87, 0x23,
                0x07, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xa7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x81, 0x05,
                0x00, 0x80 ]
        # OK Packet
        packet = Packet(0x01, length=0x2b, packet_type=0x01, message_type=0x07,
                        body=body, checksum=0xe1)
        message = SerialAPIGetCapabilities(packet)

        # Check version/manufacturer/product type/id
        assert_that((message.version, message.manufacturer_id,
                     message.product_type, message.product_id),
                    equal_to((0x2010, 0x3586, 0x19a7, 0x8723)))

        # Check body
        assert_that(message.bitmap_bytes, has_length(32))
        assert_that(message.bitmap_bytes, equal_to(body[8:]))

        # Check supported message types
        assert_that(message.message_types, equal_to(
                [1, 2, 3, 10, 97, 98, 99, 102, 104, 225, 232, 233, 235, 256 ]))

        for x in range(256):
            assert_that(message.supports_message_type(x),
                        equal_to(x in message.message_types))

    def test_create_request(self):
        """SerialAPIGetCapabilities create request"""
        packet = SerialAPIGetCapabilities.create_request()
        assert_that(packet.bytes(), equal_to(b'\x01\x03\x00\x07\xfb'))


class TestSerialAPIGetInitData(object):

    def test_bad_creation(self):
        """SerialAPIGetInitData bad packet"""
        body = [0x15, 0x23, 0x1d, 
                0x07, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xa7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x81,
                0x05, 0x00]
        # OK Packet
        packet = Packet(0x01, length=0x25, packet_type=0x01, message_type=0x02,
                        body=body, checksum=0xe1)
        message = SerialAPIGetInitData(packet)

        # Bad preamble
        packet.preamble = 0x00
        assert_that(calling(SerialAPIGetInitData).with_args(packet),
                    raises(ValueError))
        packet.preamble = 0x01

        # Bad length
        packet.length = 0x24
        assert_that(calling(SerialAPIGetInitData).with_args(packet),
                    raises(ValueError))
        packet.length = 0x25

        # Bad packet type
        packet.packet_type = 0x00
        assert_that(calling(SerialAPIGetInitData).with_args(packet),
                    raises(ValueError))
        packet.packet_type = 0x01

        # Bad message type
        packet.message_type = 0x03
        assert_that(calling(SerialAPIGetInitData).with_args(packet),
                    raises(ValueError))
        packet.message_type = 0x02

        # Bad body bitmap length
        packet.body[2] = 0x1c
        assert_that(calling(SerialAPIGetInitData).with_args(packet),
                    raises(ValueError))        
        packet.body[2] = 0x1d

    def test_good_creation(self):
        """SerialAPIGetInitData parsing"""
        body = [0x15, 0x23, 0x1d, 
                0x07, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xa7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x81,
                0x05, 0x00]
        packet = Packet(0x01, length=0x25, packet_type=0x01, message_type=0x02,
                        body=body, checksum=0xe1)
        message = SerialAPIGetInitData(packet)

        assert_that(message.version, equal_to(0x15))
        assert_that(message.capabilities, equal_to(0x23))

        assert_that(message.nodes, equal_to([1, 2, 3, 10, 97, 98, 99, 102, 104,
                                             225, 232]))

        # Test capabilities
        message.capabilities = 0x04
        assert_that(message.secondary, equal_to(True))
        assert_that(message.static_update, equal_to(False))

        message.capabilities = 0x08
        assert_that(message.secondary, equal_to(False))
        assert_that(message.static_update, equal_to(True))

        message.capabilities = 0x0c
        assert_that(message.secondary, equal_to(True))
        assert_that(message.static_update, equal_to(True))

        message.capabilities = 0xf3
        assert_that(message.secondary, equal_to(False))
        assert_that(message.static_update, equal_to(False))

    def test_create_request(self):
        """SerialAPIGetInitData create request"""
        packet = SerialAPIGetInitData.create_request()
        assert_that(packet.bytes(), equal_to(b'\x01\x03\x00\x02\xfe'))


class TestZWGetControllerCapabilities(object):

    def test_bad_creation(self):
        """ZWGetControllerCapabilities bad packet"""
        body = [0x0f]
        # OK Packet
        packet = Packet(0x01, length=0x04, packet_type=0x01, message_type=0x05,
                        body=body, checksum=0xe1)
        message = ZWGetControllerCapabilities(packet)

        # Bad preamble
        packet.preamble = 0x00
        assert_that(calling(ZWGetControllerCapabilities).with_args(packet),
                    raises(ValueError))
        packet.preamble = 0x01

        # Bad length
        packet.length = 0x03
        assert_that(calling(ZWGetControllerCapabilities).with_args(packet),
                    raises(ValueError))
        packet.length = 0x04

        # Bad packet type
        packet.packet_type = 0x00
        assert_that(calling(ZWGetControllerCapabilities).with_args(packet),
                    raises(ValueError))
        packet.packet_type = 0x01

        # Bad message type
        packet.message_type = 0x03
        assert_that(calling(ZWGetControllerCapabilities).with_args(packet),
                    raises(ValueError))
        packet.message_type = 0x05

    def test_good_creation(self):
        """ZWGetControllerCapabilities parsing"""
        body = [0x0f]
        # OK Packet
        packet = Packet(0x01, length=0x04, packet_type=0x01, message_type=0x05,
                        body=body, checksum=0xe1)
        message = ZWGetControllerCapabilities(packet)

        assert_that(message.capabilities, equal_to(0x0f))

        # Test capabilities
        message.capabilities = 0x01
        caps = (message.secondary, message.non_standard_home_id,
                message.suc_id_server, message.was_primary,
                message.static_update_controller)
        assert_that(caps, equal_to((True, False, False, False, False)))

        message.capabilities = 0x02
        caps = (message.secondary, message.non_standard_home_id,
                message.suc_id_server, message.was_primary,
                message.static_update_controller)
        assert_that(caps, equal_to((False, True, False, False, False)))

        message.capabilities = 0x04
        caps = (message.secondary, message.non_standard_home_id,
                message.suc_id_server, message.was_primary,
                message.static_update_controller)
        assert_that(caps, equal_to((False, False, True, False, False)))

        message.capabilities = 0x08
        caps = (message.secondary, message.non_standard_home_id,
                message.suc_id_server, message.was_primary,
                message.static_update_controller)
        assert_that(caps, equal_to((False, False, False, True, False)))

        message.capabilities = 0x10
        caps = (message.secondary, message.non_standard_home_id,
                message.suc_id_server, message.was_primary,
                message.static_update_controller)
        assert_that(caps, equal_to((False, False, False, False, True)))

        message.capabilities = 0x1f
        caps = (message.secondary, message.non_standard_home_id,
                message.suc_id_server, message.was_primary,
                message.static_update_controller)
        assert_that(caps, equal_to((True, True, True, True, True)))

    def test_create_request(self):
        """ZWGetControllerCapabilities create request"""
        packet = ZWGetControllerCapabilities.create_request()
        assert_that(packet.bytes(), equal_to(b'\x01\x03\x00\x05\xf9'))


