
=========
Discovery
=========
To get a list of node ids on the ZWave network, send a discovery message, and ACK the response. The response format includes the serial API version and capabilities. The node ids used on the network are stored as a bitmap, with the number of bitfield bytes specifying the total number of ids (starting at 1), and should be 29 bytes (0x1d * 8 = 232 devices maximum).


	Send:
	----------------------------------------------------------------
	| SOF | Length | REQUEST | SERIAL_API_GET_INIT_DATA | CHECKSUM |
	----------------------------------------------------------------
	| x01 |    x03 |     x00 |                      x02 |      xfe |
	----------------------------------------------------------------

	Receive:
	-------
	| ACK |
	-------
	| x06 |
	-------

	-----------------------------------------------------------
	| SOF | Length | RESPONSE | SERIAL_API_GET_INIT_DATA | ...
	-----------------------------------------------------------
	| x01 |   x??  |      x01 |                      x02 | ...    
	-----------------------------------------------------------

	-----------------------------------------------------------
	... | Version | Capabilities | Number bitfield bytes | ...
	-----------------------------------------------------------
	... |     x?? |          x?? |                   x1d | ...
	-----------------------------------------------------------

	-----------------------------------------------------------
	... |               Node id bytes |  ?? |  ?? |  checksum |
	-----------------------------------------------------------
	... | Number bitfield bytes * x?? | x?? | x00 |       x?? |
	-----------------------------------------------------------

	Send:
	-------
	| ACK |
	-------
	| x06 |
	-------	    

