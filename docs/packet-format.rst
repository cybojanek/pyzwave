=======
General
=======
Single byte packets consist of only a preamble: ACK 0x06 (acknowledged),
NAK 0x15 (not acknowledged), CAN 0x18 (can't send?)

	------------
 	| Preamble |
	------------
	|  1 byte  |
	------------


Multi byte packets consist of a SOF 0x01 (start of frame) preamble, followed
by a one byte length. The length is the length of the rest of the message
(type, controller type, body, checksum). The message type is one of
REQUEST 0x00 or RESPONSE 0x01. The controller message type describes the
functional message itself, ie request list of nodes, send data to a node etc...
The body is the payload of the message. And finally, the checksum, is an XOR
starting at 0xFF, over everything after the preamble (not including the
checksum itself). A message is allowed to have a 0 byte length body.

	--------------------------------------------------------------------
	| Preamble | Length | Packet Type | Message Type | Body | Checksum |
	--------------------------------------------------------------------
	|  1 byte  | 1 byte |    1 byte   |    1 byte    |  ??  |  1 byte  |
	--------------------------------------------------------------------

====
ACKs
====
When do they happen? And when are they necessary?


====
NAKs
====
When do they happen? And when are they necessary?


====
CANs
====
When do they happen? And when are they necessary?
