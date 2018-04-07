PBlock toolset
==============

Just playing around with serving random-access files using streams.

THE MIGHTY "PBLOCK STREAM" I SHALL CALL THE INTERFACE!1

Tools
-----

* `pblock-srv` - serve a file using pblock stream
  * should be renamed to `pblock-file`?
* `pblock-read` - read range from pblock stream and print to output
* `pblock-write` - write to pblock connection at specified offset

Tools in progress:

* `pblock-mix` - mix many files like in overlay-fs

Tools intended:

* `pblock-cp` - copy data from one pblock to another
* `pblock-swap` - swap data between to pblocks
* `pblock-server` - serve pblock connection over TCP or UNIX domain socket
  (This will allow for connecting multiple times to single pblock)
* `pblock-hub` - like `pblock-server` but works on pipes and client count is fixed in single run
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

**v0.2**

### Axioms

* PBlock connection allows for acces to single file.
* PBlock interface works on top of pair of ordered, reliable, unidirectional byte streams.
* Files are infinite, 0-based byte sequences. We have no notion of file size nor of "missing/unset blocks".
* Access to files is transactional. In each transaction one can atomicaly write and read file in many locations, not necessarily coherent.

### Nice-to-haves

* PBlock interface should integrate well with zero-copy kernel interfaces like `sendfile()` system call. This will ensure space for performance improvement, especialy in large file-mangling pipelines.
* For large transfers PBlock interface shouldn't add much overhead.

### Implementation

* Each half of connection is composed of *segment* objects.
* Each *segment* has (in order)
  * *type* (byte `r`, `w` or `c`),
    * `r` segments are used to request data ranges
    * `w` segments are used to transmit data
    * `c` segments commits pending operations
  * if *type* is `r` or `w`: *offset* varint
  * if *type* is `r` or `w`: *length* varint
  * if *type* is `w`: *payload* - blob with size `length`
* Client requests atomic reads and writes with `r` and `w` segments, then commits transaction with `c` segment.
* Server processes segments in order and confirms finished atomic actions with `c` segment.
  * For every `r` segment it must respond with `w` segment (with exact same *offset* and *length*).
  * For every `w` segment it performs writes according to is internal semantics.
