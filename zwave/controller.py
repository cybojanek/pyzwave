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

import serial

import logging

from .packet import PacketACK
from .packet import PacketParser
from .packet import Preamble


logger = logging.getLogger(__name__)


class Transaction(object):

    def __init__(self, packet):
        pass


class ZWaveController(object):
    """Interfaces with serial device controller to read/write packets

    """

    def __init__(self, path):
        """
        Arguments:
            path (str): path to serial device

        Raises:
            serial.serialutil.SerialException: if failed to open device

        """
        super(ZWaveController, self).__init__()
        self.path = path
        self.device = serial.Serial(port=self.path, baudrate=115200,
                                    rtscts=True, dsrdtr=True)
        self.packet_parser = PacketParser()

    def read(self):
        """Read a packet from the serial device. Blocking.

        Return:
            Packet

        Raises:
            ValueError: if bad byte value not in range of [0, 255]
            zwave.packet.PacketParserException: if parsing exception occured

        """
        packet = None
        while packet is None:
            b = self.device.read()
            n = int.from_bytes(b, byteorder='little')
            packet = self.packet_parser.update(n)
        # Auto ACK SOF
        if packet.preamble == Preamble.SOF:
            self.write(PacketACK())
        return packet

    def write(self, packet):
        """Write a packet to the serial device.

        Arguments:
            packet (Packet): to write

        """
        # Get bytes
        to_write = packet.bytes()
        # Add newline
        to_write.append(ord('\n'))
        # Write!
        self.device.write(to_write)

    def close(self):
        self.device.close()
