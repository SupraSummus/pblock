PBlock toolset
==============

Just playing around with serving random-access files using streams.

THE MIGHTY "PBLOCK STREAM" I SHALL CALL THE INTERFACE!1

Tools done
* -

Tools in progress
* `pblock-srv` - serve a file using pblock stream
  * write support to be tested
* `pblock-cat` - receive/send file from/to pblock stream
  * write support to be added

Tools intended
* `pblock-hub` - mix many files like in overlay-fs and/or split them to multiple clients
* `pblock-mount` - mount stream using fuse interface
* `pblock-http` - http (using byte ranges) to pblock stream interface
* compression/decompression commnand maybe?

Protocol
--------

Not realy documented well but eehh..

* Each half of connection is composed of *transaction* objects.
* Each transaction object begins with varint `n` and then goes `n` *segments*.
* Each segment has (in order)
  * `type` (byte `r` or `w`),
    * `r` segments are used to request data ranges
    * `w` segments are used to transmit data
  * `offset` varint
  * `length` varint
  * if type is `w` then there is payload - blob with size `length`
