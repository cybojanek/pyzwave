import argparse
import sys

import serial

from zwave.controller import ZWaveController
from zwave.packet import Packet, Preamble, PacketType, MessageType
from zwave.packet import PacketACK, PacketNAK, PacketCAN
from zwave.message import SerialAPIGetInitData
from zwave.message import SerialAPIGetCapabilities
from zwave.message import ZWGetControllerCapabilities


def discover(z, args):
    # Write request
    z.write(SerialAPIGetInitData.create_request())

    # ACK from controller
    packet = z.read()
    if packet.preamble != Preamble.ACK:
        sys.stderr.write('Failed to get ACK: %s' % (packet))
        sys.exit(1)

    # Reply
    packet = z.read()
    if packet.preamble != Preamble.SOF:
        sys.stderr.write('Failed to get SOF packet: %s' % (packet))
        sys.exit(1)
    print(packet)

    # Parse packet
    serial_api_init_data = SerialAPIGetInitData(packet)
    print('Serial API Init Data\n====================\n'
          'Version: %s\nSecondary: %s\nStatic Update: %s\nNodes: %s' % (
                serial_api_init_data.version, serial_api_init_data.secondary,
                serial_api_init_data.static_update,
                serial_api_init_data.nodes))

    # Write request
    z.write(SerialAPIGetCapabilities.create_request())

    # ACK from controller
    packet = z.read()
    if packet.preamble != Preamble.ACK:
        sys.stderr.write('Failed to get ACK: %s' % (packet))
        sys.exit(1)

    # Reply
    packet = z.read()
    if packet.preamble != Preamble.SOF:
        sys.stderr.write('Failed to get SOF packet: %s' % (packet))
        sys.exit(1)

    # Parse packet
    serial_api_capabilities = SerialAPIGetCapabilities(packet)
    print('\nSerial API Capabilities\n=======================\n'
          'Version: %#04x\nManufacturer: %#04x\nProduct type: %#04x\n'
          'Product ID: %#04x' % (
                serial_api_capabilities.version,
                serial_api_capabilities.manufacturer_id,
                serial_api_capabilities.product_type,
                serial_api_capabilities.product_id))
    print('Message Types: %s\n' % (
            ', '.join(['0x%02x' % x for x in
                      serial_api_capabilities.message_types])))

    # Write request
    z.write(ZWGetControllerCapabilities.create_request())

    # ACK from controller
    packet = z.read()
    if packet.preamble != Preamble.ACK:
        sys.stderr.write('Failed to get ACK: %s' % (packet))
        sys.exit(1)

    # Reply
    packet = z.read()
    if packet.preamble != Preamble.SOF:
        sys.stderr.write('Failed to get SOF packet: %s' % (packet))
        sys.exit(1)

    zw_capabilities = ZWGetControllerCapabilities(packet)
    print('\nZW Controller Capabilities\n==========================\n'
          'Secondary: %s\nNon standard home id: %s\nSUC ID server: %s\n'
          'Was primary: %s\nStatic update: %s' % (
            zw_capabilities.secondary, zw_capabilities.non_standard_home_id,
            zw_capabilities.suc_id_server, zw_capabilities.was_primary,
            zw_capabilities.static_update_controller))

    # Close
    z.close()

def switch(z, args):
    print('Switch!')


def main():
    parser = argparse.ArgumentParser(description='Run zwave commands')
    parser.add_argument('--device', default='/dev/tty.usbmodem1421',
                        help='device path (default: /dev/tty.usbmodem1421)')

    subparsers = parser.add_subparsers(dest='COMMAND')
    subparsers.required = True

    parser_discover = subparsers.add_parser('discover')
    parser_discover.set_defaults(func=discover)

    parser_switch = subparsers.add_parser('switch')
    parser_switch.set_defaults(func=switch)
    parser_switch.add_argument('node_id', type=int, choices=range(1, 233),
                                help='Node ID in the range of [1, 232]')
    parser_switch.add_argument('mode', choices=['on', 'off'])

    args = parser.parse_args()

    z = None
    try:
        z = ZWaveController(args.device)
    except serial.serialutil.SerialException:
        sys.stderr.write('Serial device [%s] not found' % (args.device))

    args.func(z, args)

if __name__ == '__main__':
    main()
