import argparse
import sys

from zwave.controller import ZWaveController
from zwave.message import Message, MessageType, ControllerMessageType
from zwave.message import MessageAck, MessageNak


def main():
    parser = argparse.ArgumentParser(description='Run zwave commands')
    parser.add_argument('--device', help='device path',
                        default='/dev/tty.usbmodem1421')

    args = parser.parse_args()

    z = ZWaveController(args.device)

    message = Message.create(
            message_type=MessageType.REQUEST,
            controller_message_type=ControllerMessageType.SERIAL_API_GET_INIT_DATA)
    print(message.bytes())
    z.write(message)

    message = z.read()
    if isinstance(message, MessageAck):
        z.write(MessageAck())
    else:
        print("Unknown: %s" % (message))
        sys.exit(1)

    message = z.read()
    print("Received: %s" % (message.bytes()))

if __name__ == '__main__':
    main()
