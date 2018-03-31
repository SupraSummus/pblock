from collections import namedtuple
from enum import Enum
import fcntl
import logging
import os
import varint


logger = logging.getLogger(__name__)


class Transaction(namedtuple('Transaction', ('segments'))):
    @classmethod
    def from_stream(cls, stream):
        length = varint.decode_stream(stream)
        segments = [Segment.from_stream(stream) for _ in range(length)]
        return cls(segments=segments)

    def write_to_stream(self, stream):
        stream.write(varint.encode(len(self.segments)))
        for segment in self.segments:
            segment.write_to_stream(stream)


class SegmentType(Enum):
    READ = b'r'
    WRITE = b'w'

    @classmethod
    def from_stream(cls, stream):
        read_value = stream.read(1)
        assert(len(read_value) == 1)
        if read_value == cls.READ.value:
            return cls.READ
        elif read_value == cls.WRITE.value:
            return cls.WRITE
        else:
            assert(False)

    def write_to_stream(self, stream):
        stream.write(self.value)


class Segment(namedtuple('Segment', ('type', 'offset', 'length', 'payload'))):
    @classmethod
    def read_request(cls, offset, length):
        return cls(
            type=SegmentType.READ,
            offset=offset,
            length=length,
            payload=None,
        )

    @classmethod
    def write_request(cls, offset, buf):
        return cls(
            type=SegmentType.WRITE,
            offset=offset,
            length=len(buf),
            payload=buf,
        )

    @classmethod
    def from_stream(cls, stream):
        type = SegmentType.from_stream(stream)
        offset = varint.decode_stream(stream)
        length = varint.decode_stream(stream)
        payload = None
        if type == SegmentType.WRITE:
            payload = stream.read(length)
        return cls(
            type=type,
            offset=offset,
            length=length,
            payload=payload,
        )

    def write_to_stream(self, stream):
        self.type.write_to_stream(stream)
        stream.write(varint.encode(self.offset))
        stream.write(varint.encode(self.length))
        if self.type == SegmentType.WRITE:
            stream.write(self.payload)


class Connection(namedtuple('Connection', ('reading_stream', 'writing_stream'))):
    @classmethod
    def open_desc(cls, desc, mode):
        # try parse to int - it may be fd
        try:
            desc = int(desc)
        except ValueError:
            pass
        return open(desc, mode)


class ConnectionToClient(Connection):
    @classmethod
    def open(cls, r_desc, w_desc):
        logger.debug("opening reading connection to client: {}".format(r_desc))
        r = cls.open_desc(r_desc, 'rb')
        logger.debug("opening writing connection to client: {}".format(w_desc))
        w = cls.open_desc(w_desc, 'wb')
        return cls(
            reading_stream=r,
            writing_stream=w,
        )


class ConnectionToServer(Connection):
    @classmethod
    def open(cls, r_desc, w_desc):
        logger.debug("opening writing connection to server: {}".format(w_desc))
        w = cls.open_desc(w_desc, 'wb')
        logger.debug("opening reading connection to server: {}".format(r_desc))
        r = cls.open_desc(r_desc, 'rb')
        return cls(
            reading_stream=r,
            writing_stream=w,
        )
