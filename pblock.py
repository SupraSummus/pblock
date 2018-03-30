from collections import namedtuple
from enum import Enum
import fcntl
import os
import varint


def custom_opener(mode):
    def open_a_file(arg):
        try:
            arg = int(arg)
        except ValueError:
            pass
        return open(arg, mode)

    return open_a_file


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
