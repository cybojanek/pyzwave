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

from .message import MessageParser

import logging

logger = logging.getLogger(__name__)

class ZWaveController(object):
    """docstring for ZWaveController"""

    def __init__(self, path):
        super(ZWaveController, self).__init__()
        self.path = path
        self.device = s = serial.Serial(port=self.path, baudrate=115200,
                                        rtscts=True, dsrdtr=True)
        self.message_parser = MessageParser()

    def read(self):
        message = None
        while message is None:
            b = self.device.read()
            message = self.message_parser.update(b)
        return message

    def write(self, message):
        # Get bytes
        to_write = message.bytes()
        # Add newline
        to_write.append(ord('\n'))
        self.device.write(to_write)

