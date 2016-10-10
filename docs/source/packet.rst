*************
Packet Format
*************

Single Byte
===========

Single byte packets consist of only a preamble: ACK 0x06 (acknowledged), NAK 0x15 (not acknowledged), CAN 0x18 (can't acknowledge)

.. code-block:: none

    ------------
    | Preamble |
    ------------
    |     0x?? |
    ------------

.. todo::

    When do ACKs, NAKs, CANs happen? And when are they necessary? CAN happens during mixed transmission of multiple ZW_SEND_DATA commands, if sent in bad sequence without waiting for previous messages


Multi Byte
==========

Multi byte packets consist of a SOF 0x01 (start of frame) preamble, followed by a one byte length. The length is the length of the rest of the message (packet type, message type, body, checksum). The packet type is one of REQUEST 0x00 or RESPONSE 0x01. The message type describes the functional message itself, ie request list of nodes, send data to a node etc... The body is the payload of the message. And finally, the checksum, is an XOR starting at 0xff, over everything after the preamble (not including the checksum itself). A message is allowed to have a 0 byte length body.

.. code-block:: none

    --------------------------------------------------------------------
    | Preamble | Length | Packet Type | Message Type | Body | Checksum |
    --------------------------------------------------------------------
    |     0x01 |   0x?? |        0x?? |         0x?? |  ??  |    0x??  |
    --------------------------------------------------------------------
