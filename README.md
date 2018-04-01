PBlock toolset
==============

Just playing around with serving random-access files using streams.

THE MIGHTY "PBLOCK STREAM" I SHALL CALL THE INTERFACE!1

Tools
-----

Tools done:
*

Tools in progress:

* `pblock-srv` - serve a file using pblock stream
  * write support to be tested
  * after file end there should be ocean of zeroes
* `pblock-cat` - receive/send file from/to pblock stream
  * write support to be added
  * should not support gaps in file
  * rename to `pblock-read` because it's not like `cat` at all

Tools intended:

* `pblock-write` - write stdin to pblock at specified offset
* `pblock-mix` - mix many files like in overlay-fs
* `pblock-hub` - serve same file to multiple clients
  (Possibly may be integrated with `pblock-mix`?)
* `pblock-mount` - mount stream using fuse interface
* `pblock-http` - http(s) (using byte ranges) to pblock stream interface
* compression/decompression commnand maybe?
* `pblock-sniff` - (sniffs only one side of a connection?)
* `pblock-mirror` - parallel usage of multiple underlying pblocks like in RAID-1.
  (Possibly may be integrated with `pblock-mix`?)
* `pblock-cache` - ???
  Not sure if possible, necessary and in-good-taste. Don't know how to inalidate cache.
* `pblock-rw` - route READ and WRITE segments to different connections
  (Possibly may be integrated with `pblock-mix`?)

Protocol
--------

**v0.1**

Axioms:

* PBlock connection allows for acces to single file.
* PBlock interface works on top of pair of ordered, reliable, unidirectional byte streams.
* Files are infinite, 0-based byte sequences. We have no notion of file size nor of "missing/unset blocks".
* Access to files is transactional. In each transaction one can atomicaly write and read file in many locations, not necessarily coherent.

Nice-to-haves:

* PBlock interface should integrate well with zero-copy kernel interfaces like `sendfile()` system call. This will ensure space for performance improvement, especialy in large file-mangling pipelines.
* For large transfers PBlock interface shouldn't add much overhead.

Implementation of preceding statements:

* Each half of connection is composed of *transaction* objects.
* Each *transaction* object begins with varint `n` and then goes `n` *segments*.
* Each *segment* has (in order)
  * `type` (byte `r` or `w`),
    * `r` segments are used to request data ranges
    * `w` segments are used to transmit data
  * `offset` varint
  * `length` varint
  * if type is `w` then there is payload - blob with size `length`
