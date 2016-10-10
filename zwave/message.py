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

import struct

from zwave.packet import MessageType
from zwave.packet import Packet
from zwave.packet import PacketType
from zwave.packet import Preamble


class TransmitOption(object):
    """Transmit options for ZW_SEND_DATA

    Attributes:
        ACK (int):
        LOW_POWER (int):
        AUTO_ROUTE (int):
        NO_ROUTE (int):
        EXPLORE (int):
        ALL (:obj:`set` of :obj:`int`): all transmit options

    """
    ACK = 0x01
    LOW_POWER = 0x02
    AUTO_ROUTE = 0x04
    NO_ROUTE = 0x10
    EXPLORE = 0x20

    ALL = set([ACK, LOW_POWER, AUTO_ROUTE, NO_ROUTE, EXPLORE])


class TransmitComplete(object):
    """Transmit options for ???

    Attributes:
        NO_ACK (int): no ack - device might be asleep
        FAIL (int): failed
        NOT_IDLE (int): network is busy
        NO_ROUTE (int): no route to node
        ALL (:obj:`set` of :obj:`int`): all transmit complete

    """
    OK = 0x00
    NO_ACK = 0x01
    FAIL = 0x02
    NOT_IDLE = 0x03
    NO_ROUTE = 0x04

    ALL = set([OK, NO_ACK, FAIL, NOT_IDLE, NO_ROUTE])


class CommandClass(object):
    """Command class

    Attributes:
        BASIC (int):
        CONTROLLER_REPLICATION (int):
        APPLICATION_STATUS (int):
        HAIL (int):
        ALL (:obj:`set` of :obj:`int`): all command class

    """
    BASIC = 0x20
    CONTROLLER_REPLICATION = 0x21
    APPLICATION_STATUS = 0x22
    HAIL = 0x23

    ALL = set([BASIC, CONTROLLER_REPLICATION, APPLICATION_STATUS, HAIL])


class Message(Packet):

    def __init__(self, packet):
        super(Message, self).__init__(packet.preamble, length=packet.length,
                                      packet_type=packet.packet_type,
                                      message_type=packet.message_type,
                                      body=packet.body,
                                      checksum=packet.checksum)


class SerialAPIGetCapabilities(Message):
    """Reply to SERIAL_API_GET_CAPABILITIES

    Attributes:
        version (int):
        manufacturer_id (int):
        product_type (int):
        product_id (int):
        bitmap_bytes (:obj:`list` of :obj:`int`):
        message_types (:obj:`list` of :obj:`int`):

    """

    def __init__(self, packet: Packet):
        """Create a SerialAPIGetCapabilities message from a packet

        Arguments:
            packet (Packet): from a SERIAL_API_GET_CAPABILITIES request

        Raises:
            ValueError: on malformed packet

        """
        super(SerialAPIGetCapabilities, self).__init__(packet)

        # Check prefix matches
        expected_prefix_request = (Preamble.SOF, 0x03, PacketType.REQUEST,
                                   MessageType.SERIAL_API_GET_CAPABILITIES)
        expected_prefix_response = (Preamble.SOF, 0x2b, PacketType.RESPONSE,
                                    MessageType.SERIAL_API_GET_CAPABILITIES)
        actual_prefix = (self.preamble, self.length, self.packet_type,
                         self.message_type)

        if actual_prefix == expected_prefix_request:
            self.version = 0
            self.manufacturer_id = 0
            self.product_type = 0
            self.product_id = 0
            self.bitmap_bytes = []
            self.message_types = []
        elif actual_prefix == expected_prefix_response:
            # Parse version
            self.version = struct.unpack('<H', bytearray(self.body[0:2]))[0]
            # Parse manufacturer
            self.manufacturer_id = struct.unpack('>H', bytearray(self.body[2:4]))[0]
            # Parse product type
            self.product_type = struct.unpack('>H', bytearray(self.body[4:6]))[0]
            # Parse product id
            self.product_id = struct.unpack('>H', bytearray(self.body[6:8]))[0]

            # Store bytes, and extract node ids
            self.bitmap_bytes = self.body[8:]

            # Store bitmap values
            self.message_types = []
            for i, x in enumerate(self.bitmap_bytes):
                for b in range(8):
                    if (x & (1 << b)) != 0:
                        self.message_types.append(1 + (i * 8) + b)
        else:
            raise ValueError('Bad discover message prefix: [%s]' % (
                    str(actual_prefix)))

    def supports_message_type(self, message_type: int) -> bool:
        """Check if a given message type is supported

        Arguments:
            message_type (int): MessageType

        Returns:
            bool

        """
        if self.request:
            return False
        return (message_type in self.message_types)

    @classmethod
    def create_request(cls) -> Packet:
        """Create a request packet for SERIAL_API_GET_CAPABILITIES

        Return:
            Packet

        """
        return Packet.create(packet_type=PacketType.REQUEST,
                             message_type=MessageType.SERIAL_API_GET_CAPABILITIES)


class SerialAPIGetInitData(Message):
    """Reply to SERIAL_API_GET_INIT_DATA

    Attributes:
        version (int):
        capabilities (int):
        bitmap_byte_length (int): always 0x1d
        bitmap_bytes (list(int)): bitmap of 29 bytes
        nodes (list(int)): of node ids on the network
        secondary (bool): is controller secondary (based on capabilities)
        static_update (bool): is controller static update (based on capabilities)

    """

    def __init__(self, packet):
        """Create a SerialAPIGetInitData message from a packet

        Arguments:
            packet (Packet): from a SERIAL_API_GET_INIT_DATA request

        Raises:
            ValueError: on malformed message

        """
        super(SerialAPIGetInitData, self).__init__(packet)

        # Check prefix matches
        expected_prefix_request = (Preamble.SOF, 0x03, PacketType.REQUEST,
                                   MessageType.SERIAL_API_GET_INIT_DATA)
        expected_prefix_response = (Preamble.SOF, 0x25, PacketType.RESPONSE,
                                    MessageType.SERIAL_API_GET_INIT_DATA)
        actual_prefix = (self.preamble, self.length, self.packet_type,
                         self.message_type)

        if actual_prefix == expected_prefix_request:
            pass
        elif actual_prefix == expected_prefix_response:
            # Parse version and capabilities
            self.version = self.body[0]
            self.capabilities = self.body[1]
            self.bitmap_byte_length = self.body[2]

            # Should be 29 for 29 * 8 = 232 bits / node ids
            if self.bitmap_byte_length != 0x1d:
                raise ValueError('Bad bitmap byte length: [%#02x] expected '
                                 '[0x1d]' % (self.bitmap_byte_length))

            # Store bytes, and extract node ids
            self.bitmap_bytes = self.body[3 : 3 + 29]

            self.nodes = []
            for i, x in enumerate(self.bitmap_bytes):
                for b in range(8):
                    if (x & (1 << b)) != 0:
                        self.nodes.append(1 + (i * 8) + b)
        else:
            raise ValueError('Bad discover message prefix: [%s] expected '
                             '[%s] or [%s]' % (actual_prefix,
                                               expected_prefix_request,
                                               expected_prefix_response))

    @property
    def secondary(self):
        return self.response and (self.capabilities & 0x04) != 0

    @property
    def static_update(self):
        return self.response and (self.capabilities & 0x08) != 0

    @classmethod
    def create_request(cls):
        """Create a request packet for SERIAL_API_GET_INIT_DATA

        Return:
            Packet

        """
        return Packet.create(packet_type=PacketType.REQUEST,
                             message_type=MessageType.SERIAL_API_GET_INIT_DATA)


class ZWGetControllerCapabilities(Message):
    """Reply to ZW_GET_CONTROLLER_CAPABILITIES

    Attribytes:
        capabilities (int):
        secondary (bool): if controller is secondary (based on capabilities)
        non_standard_home_id (bool): using a different home id (based on capabilities)
        suc_id_server (bool): if there is a suc id server (based on capabilities)
        was_primary (bool): controller was primary before SIS (based on capabilities)
        static_update_controller (bool): controller is static update (based on capabilities)

    """

    def __init__(self, packet):
        """Create a ZWGetControllerCapabilities message from a packet

        Arguments:
            packet (Packet): from a ZW_GET_CONTROLLER_CAPABILITIES request

        Raises:
            ValueError: on malformed message

        """
        super(ZWGetControllerCapabilities, self).__init__(packet)

        # Check prefix matches
        expected_prefix_request = (Preamble.SOF, 0x03, PacketType.REQUEST,
                                   MessageType.ZW_GET_CONTROLLER_CAPABILITIES)
        expected_prefix_response = (Preamble.SOF, 0x04, PacketType.RESPONSE,
                                    MessageType.ZW_GET_CONTROLLER_CAPABILITIES)
        actual_prefix = (self.preamble, self.length, self.packet_type,
                         self.message_type)

        if actual_prefix == expected_prefix_request:
            pass
        elif actual_prefix == expected_prefix_response:
            self.capabilities = self.body[0]
        else:
            raise ValueError('Bad discover packet prefix: [%s]' % (
                    str(actual_prefix)))

    @property
    def secondary(self):
        return self.response and (self.capabilities & 0x01) != 0

    @property
    def non_standard_home_id(self):
        return self.response and (self.capabilities & 0x02) != 0

    @property
    def suc_id_server(self):
        return self.response and (self.capabilities & 0x04) != 0

    @property
    def was_primary(self):
        return self.response and (self.capabilities & 0x08) != 0

    @property
    def static_update_controller(self):
        return self.response and (self.capabilities & 0x10) != 0

    @classmethod
    def create_request(cls):
        """Create a request packet for ZW_GET_CONTROLLER_CAPABILITIES

        Return:
            Packet

        """
        return Packet.create(packet_type=PacketType.REQUEST,
                             message_type=MessageType.ZW_GET_CONTROLLER_CAPABILITIES)


class ZWSendData(Message):

    def __init__(self, packet):
        """Create a ZWSendData from a packet

        Arguments:
            packet (Packet): from a ZWSendData request

        Raises:
            ValueError: on malformed message

        """
        super(ZWSendData, self).__init__(packet)

        # Check prefix matches
        expected_prefix = (Preamble.SOF, PacketType.RESPONSE,
                           MessageType.ZW_SEND_DATA)
        actual_prefix = (self.preamble, self.packet_type, self.message_type)

        if actual_prefix != expected_prefix:
            raise ValueError('Bad ZWSendData packet prefix: [%s]' % (
                    str(actual_prefix)))

    @classmethod
    def create_request(cls, node_id, command_class, payload=None,
                       transmit_options=None, callback_id=None):
        """Create a request packet for ZW_SEND_DATA

        Arguments:
            node_id (int):
            command_class (int): from CommandClass

        Keyword Arguments:
            payload (list(int)):
            transmit_options (int): or'ed options of TransmitOption
            callback_id (int):

        Return:
            Packet

        """

        # Body: | NODE_ID | LENGTH_OF_PAYLOAD  + 1 | COMMAND_CLASS |
        #       | PAYLOAD | TRANSMIT_OPTIONS | CALLBACK_ID |
        # Set up defaults
        payload = payload or []
        transmit_options = (transmit_options if transmit_options is not None
                            else (TransmitOption.ACK
                                  | TransmitOption.AUTO_ROUTE
                                  | TransmitOption.EXPLORE))
        body = [node_id, 1 + len(payload), command_class]
        body = body + payload
        body.append(transmit_options)
        if (callback_id is not None):
            body.append(callback_id)

        return Packet.create(packet_type=PacketType.REQUEST,
                             message_type=MessageType.ZW_SEND_DATA,
                             body=body)


class BasicCommand(ZWSendData):
    SET = 0x01
    GET = 0x02
    REPORT = 0x03

    ALL = set([SET, GET, REPORT])

    def __init__(self, packet):
        super(BasicCommand, self).__init__(packet)


    @classmethod
    def create_request_set(cls, node_id, value, transmit_options=None,
                           callback_id=None):
        return ZWSendData.create_request(node_id, CommandClass.BASIC,
                                         payload=[BasicCommand.SET, value],
                                         transmit_options=transmit_options,
                                         callback_id=callback_id)

    @classmethod
    def create_request_get(cls, node_id, transmit_options=None,
                           callback_id=None):
        return ZWSendData.create_request(node_id, CommandClass.BASIC,
                                         payload=[BasicCommand.GET],
                                         transmit_options=transmit_options,
                                         callback_id=callback_id)
