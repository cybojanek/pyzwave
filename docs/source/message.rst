**************
Message Format
**************

SERIAL_API_GET_CAPABILITIES
===========================

Get serial API capabilities, including the version, manufacturer and product information, and a bitmap of supported message types, indexed by message type value.

.. code-block:: none

	>>>>
	----------------------------------------------------------------------
	| SOF | Length | REQUEST | SERIAL_API_GET_CAPABILITIES | Checksum |
	----------------------------------------------------------------------
	| x01 |    x03 |     x00 |                         x07 |      xfb |
	----------------------------------------------------------------------

	<<<<
	-------
	| ACK |
	-------
	| x06 |
	-------

	<<<<
	-----------------------------------------------------------------
	| SOF | Length | RESPONSE | SERIAL_API_GET_CAPABILITIES | ...
	-----------------------------------------------------------------
	| x01 |   x2b  |      x01 |                         x07 | ...
	-----------------------------------------------------------------

	------------------------------------------------------------------
	... | Version | Manufacturer ID | Product Type | Product ID | ...
	------------------------------------------------------------------
	... | x?? x?? |         x?? x?? |      x?? x?? |    x?? x?? | ...
	------------------------------------------------------------------

	----------------------------------------
	.... | Supported API Bitmap | Checksum |
	----------------------------------------
	.... |       32 bytes * x?? |      x?? |
	----------------------------------------

	Version: 2 byte little endian
	Manufacturer ID: 2 byte big endian (check endiannes?)
	Product Type: 2 byte big endian (check endiannes?)
	Product ID: 2 byte big endian (check endiannes?)


	Supported API Bitmap:
		Byte 0:
		------------------------------------------
		| Bit 7 |                             ?? |
		| Bit 6 |    SERIAL_API_GET_CAPABILITIES |
		| Bit 5 |                             ?? |
		| Bit 4 | ZW_GET_CONTROLLER_CAPABILITIES |
		| Bit 3 |                             ?? |
		| Bit 2 |                             ?? |
		| Bit 1 |       SERIAL_API_GET_INIT_DATA |
		| Bit 0 |                            ??  |
		------------------------------------------

		Byte 1 - 31:
		same pattern

	>>>>
	-------
	| ACK |
	-------
	| x06 |
	-------


SERIAL_API_GET_INIT_DATA
========================

To get a list of node ids on the ZWave network, send a SERIAL_API_GET_INIT_DATA message, and ACK the response. The response format includes the serial API version and capabilities. The node ids used on the network are stored as a bitmap, with the number of bitfield bytes specifying the total number of ids (starting at 1), and should be 29 bytes (0x1d * 8 = 232 devices maximum).

.. code-block:: none

	>>>>
	----------------------------------------------------------------
	| SOF | Length | REQUEST | SERIAL_API_GET_INIT_DATA | Checksum |
	----------------------------------------------------------------
	| x01 |    x03 |     x00 |                      x02 |      xfe |
	----------------------------------------------------------------

	<<<<
	-------
	| ACK |
	-------
	| x06 |
	-------

	<<<<
	-----------------------------------------------------------
	| SOF | Length | RESPONSE | SERIAL_API_GET_INIT_DATA | ...
	-----------------------------------------------------------
	| x01 |   x25  |      x01 |                      x02 | ...
	-----------------------------------------------------------

	-----------------------------------------------------------
	... | Version | Capabilities | Number bitfield bytes | ...
	-----------------------------------------------------------
	... |     x?? |          x?? |                   x1d | ...
	-----------------------------------------------------------

	-----------------------------------------------------------
	... |               Node id bytes |  ?A |  ?B |  Checksum |
	-----------------------------------------------------------
	... | Number bitfield bytes * x?? | x?? | x?? |       x?? |
	-----------------------------------------------------------

	Version: ??

	Capabilities:
	------------------------------------
	| Bit 7 |                       ?? |
	| Bit 6 |                       ?? |
	| Bit 5 |                       ?? |
	| Bit 4 |                       ?? |
	| Bit 3 | Static Update Controller |
	| Bit 2 |     Secondary Controller |
	| Bit 1 |                       ?? |
	| Bit 0 |                       ?? |
	------------------------------------

	Node id bytes:
		Byte 0:
		-----------------------------
		| Bit 7 | Node ID 8 Present |
		| Bit 6 | Node ID 7 Present |
		| Bit 5 | Node ID 6 Present |
		| Bit 4 | Node ID 5 Present |
		| Bit 3 | Node ID 4 Present |
		| Bit 2 | Node ID 3 Present |
		| Bit 1 | Node ID 2 Present |
		| Bit 0 | Node ID 1 Present |
		-----------------------------

		Byte 1:
		------------------------------
		| Bit 7 | Node ID 16 Present |
		| Bit 6 | Node ID 15 Present |
		| Bit 5 | Node ID 14 Present |
		| Bit 4 | Node ID 13 Present |
		| Bit 3 | Node ID 12 Present |
		| Bit 2 | Node ID 11 Present |
		| Bit 1 | Node ID 10 Present |
		| Bit 0 |  Node ID 9 Present |
		------------------------------

		Byte 2 - 28:
		same pattern

	?A: ??

	?B: ??

	>>>>
	-------
	| ACK |
	-------
	| x06 |
	-------

ZW_GET_CONTROLLER_CAPABILITIES
==============================

Get ZWave controller capabilities

.. code-block:: none

	>>>>
	----------------------------------------------------------------------
	| SOF | Length | REQUEST | ZW_GET_CONTROLLER_CAPABILITIES | Checksum |
	----------------------------------------------------------------------
	| x01 |    x03 |     x00 |                            x05 |      xf9 |
	----------------------------------------------------------------------

	<<<<
	-------
	| ACK |
	-------
	| x06 |
	-------

	<<<<
	-----------------------------------------------------------------
	| SOF | Length | RESPONSE | ZW_GET_CONTROLLER_CAPABILITIES | ...
	-----------------------------------------------------------------
	| x01 |   x04  |      x01 |                            x05 | ...
	-----------------------------------------------------------------

	-------------------------------
	... | Capabilities | Checksum |
	-------------------------------
	... |          x?? |      x?? |
	-------------------------------

	Capabilities:
	------------------------------------
	| Bit 7 |                       ?? |
	| Bit 6 |                       ?? |
	| Bit 5 |                       ?? |
	| Bit 4 | Static update controller |
	| Bit 3 |              Was primary |
	| Bit 2 |  Static update ID server |
	| Bit 1 |     Non standard home ID |
	| Bit 0 |     Secondary Controller |
	------------------------------------

	>>>>
	-------
	| ACK |
	-------
	| x06 |
	-------

ZW_SEND_DATA
============

ZWave send data bytes to a node. There are two ways of sending data: with and without a callback id. For learning purposes, the method without a callback id is described first. In order to avoid undefined behaviour, this method is *DISCOURAGED*. Instead, you should always use a callback id (described later).

On a freshly plugged in serial controller, sending a ZW_SEND_DATA message without a callback ID, results in the message propagating correctly, but only receiving a single confirmation from the controller. On a controller which had previously responded to messages with a callback ID, that callback ID is included in another message, following the controller confirmation, even if no callback id is specified in the request. For this reason, you should always use a callback id.

.. code-block:: none

	>>>>
	------------------------------------------------------------------------
	| SOF | Length | REQUEST | ZW_SEND_DATA | Node ID | Length Payload | ...
	------------------------------------------------------------------------
	| x01 |    x?? |     x00 |          x13 |     x?? |            x?? | ...
	------------------------------------------------------------------------

	--------------------------------------------------------------------------
	... | Command Class |                     Payload | Transmit Options | ...
	--------------------------------------------------------------------------
	... |           x?? | (Length Payload - 1) *  x?? |              x?? | ...
	--------------------------------------------------------------------------

	----------------
	... | Checksum |
	----------------
	... |      x?? |
	----------------

	Node ID: target node id
	Length Payload: 1 + length(payload)
	Transmit Options: ??

	<<<<
	-------
	| ACK |
	-------
	| x06 |
	-------

	<<<<
	-----------------------------------------------------------
	| SOF | Length | RESPONSE | ZW_SEND_DATA |  ?? | Checksum |
	-----------------------------------------------------------
	| x01 |    x04 |      x01 |          x13 | x01 |     x?? |
	-----------------------------------------------------------

	>>>>
	-------
	| ACK |
	-------
	| x06 |
	-------

A callback ID should be specified by the caller, and appended after the transmit options. The callback should be greater than 10 (0x0a) (TODO: Why?)

.. code-block:: none

	>>>>
	------------------------------------------------------------------------
	| SOF | Length | REQUEST | ZW_SEND_DATA | Node ID | Length Payload | ...
	------------------------------------------------------------------------
	| x01 |    x?? |     x00 |          x13 |     x?? |            x?? | ...
	------------------------------------------------------------------------

	--------------------------------------------------------------------------
	... | Command Class |                     Payload | Transmit Options | ...
	--------------------------------------------------------------------------
	... |           x?? | (Length Payload - 1) *  x?? |              x?? | ...
	--------------------------------------------------------------------------

	------------------------------
	... | Callback ID | Checksum |
	------------------------------
	... |         x?? |      x?? |
	------------------------------

	Node ID: target node id
	Length Payload: 1 + length(payload)
	Transmit Options: ??
	Callback ID: chosen callback ID, > 0x0a (TODO: something about NONCE messages)

	<<<<
	-------
	| ACK |
	-------
	| x06 |
	-------

	<<<<
	-----------------------------------------------------------
	| SOF | Length | RESPONSE | ZW_SEND_DATA |  ?? | Checksum |
	-----------------------------------------------------------
	| x01 |    x04 |      x01 |          x13 | x01 |      x?? |
	-----------------------------------------------------------

	>>>>
	-------
	| ACK |
	-------
	| x06 |
	-------

	<<<<
	-------------------------------------------------------------------
	| SOF | Length | REQUEST | ZW_SEND_DATA | Callback ID | Error | ...
	-------------------------------------------------------------------
	| x01 |    x07 |     x00 |          x13 |         x?? |   x?? | ...
	-------------------------------------------------------------------

	----------------------------
	... |  xA |  xB | Checksum |
	----------------------------
	... | x?? | x?? |      x?? |
	----------------------------

	PacketType: REQUEST
	Callback ID: matching that above (TODO: otherwise what??)
	Error:
		------------------------------------
		| 0x00 |       TransmitComplete.OK |
		| 0x01 |   TransmitComplete.NO_ACK |
		| 0x02 |     TransmitComplete.FAIL |
		| 0x03 | TransmitComplete.NOT_IDLE |
		| 0x04 | TransmitComplete.NO_ROUTE |
		------------------------------------
	xA: ??
	xB: ??

	>>>>
	-------
	| ACK |
	-------
	| x06 |
	-------

.. todo::

	Why do we get CAN messages if we don't wait for a full sequence to finish?

BASIC_COMMAND
=============

A basic command is a ZW_SEND_DATA command that gets/sets a byte value on a node. It has one of the three payload types:

.. code-block:: none

	SET
	-------------------
	| Command | Value |
	-------------------
	|    0x01 |  0x?? |
	-------------------

	GET
	-----------
	| Command |
	-----------
	|    0x02 |
	-----------

	REPORT
	-----------
	| Command |
	-----------
	|    0x02 |
	-----------

For example, to turn on a basic light switch, you would do: SET(0xFF), to turn it off SET(0x00), and to get the current value GET(), which returns a REPORT type.
