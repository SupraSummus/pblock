from enum import Enum
import logging
import os
import varint


logger = logging.getLogger(__name__)


class SegmentType(Enum):
    READ = b'r'
    WRITE = b'w'
    COMMIT = b'c'

    @classmethod
    def from_stream(cls, stream):
        read_value = stream.read(1)
        if len(read_value) != 1:
            raise EOFError()
        for v in cls:
            if v.value == read_value:
                return v
        assert(False)

    def write_to_stream(self, stream):
        stream.write(self.value)


def move_between_fds(src, dst, size):
    total_sent = 0
    while size > 0:
        b = os.read(src, size)
        written = os.write(dst, b)
        sent = len(b)
        assert written == sent
        logger.debug("moved %d bytes between fds %d -> %d", sent, src, dst)
        total_sent += sent
        size -= sent
        if sent == 0:
            break
    return total_sent


class Connection:
    @classmethod
    def open_desc(cls, desc, mode):
        # try parse to int - it may be fd
        try:
            desc = int(desc)
        except ValueError:
            pass
        return open(desc, mode, buffering=0)

    def __init__(self, reading_stream, writing_stream, **kwargs):
        super().__init__(**kwargs)
        self.reading_stream = reading_stream
        self.writing_stream = writing_stream

    def handle_transaction(self):
        i = 0
        while True:
            # TODO try-catch only first segment in transaction
            # others are errors
            s = self.handle_segment()
            if not s:
                break
            i += 1
        return i

    def handle_segment(self):
        logger.debug("awaiting segment")
        try:
            type = SegmentType.from_stream(self.reading_stream)
        except EOFError:
            return False

        if type == SegmentType.READ:
            offset = varint.decode_stream(self.reading_stream)
            size = varint.decode_stream(self.reading_stream)
            logger.debug("processing READ offset={} size={}".format(offset, size))
            return self.handle_read(offset, size)
        elif type == SegmentType.WRITE:
            offset = varint.decode_stream(self.reading_stream)
            size = varint.decode_stream(self.reading_stream)
            logger.debug("processing WRITE header offset={} size={}".format(offset, size))
            return self.handle_write_header(offset, size)
        elif type == SegmentType.COMMIT:
            logger.debug("processing COMMIT")
            return self.handle_commit()
        else:
            raise NotImplementedError("unsupported segment type {}".format(type))

    def handle_read(self, offset, size):
        raise NotImplementedError("read requests are not supported")

    def handle_write_header(self, offset, size):
        raise NotImplementedError()

    def handle_commit(self):
        return False

    def send_read(self, offset, size):
        logger.debug("sending READ offset=%d size=%d", offset, size)
        SegmentType.READ.write_to_stream(self.writing_stream)
        self.writing_stream.write(varint.encode(offset))
        self.writing_stream.write(varint.encode(size))

    def send_write_header(self, offset, size):
        logger.debug("sending WRITE header offset=%d size=%d", offset, size)
        SegmentType.WRITE.write_to_stream(self.writing_stream)
        self.writing_stream.write(varint.encode(offset))
        self.writing_stream.write(varint.encode(size))

    def send_commit(self, flush=True):
        logger.debug("sending COMMIT")
        SegmentType.COMMIT.write_to_stream(self.writing_stream)
        if flush:
            self.writing_stream.flush()

    def read(self, n):
        b = bytearray(n)
        offset = 0
        while offset < n:
            read = self.reading_stream.readinto(b[offset:])
            offset += read
        return b

    def run(self):
        raise NotImplementedError()


class ConnectionToClient(Connection):
    def __init__(self, reading_stream, writing_stream, **kwargs):
        logger.debug("opening reading connection to client: {}".format(reading_stream))
        r = self.open_desc(reading_stream, 'rb')
        logger.debug("opening writing connection to client: {}".format(writing_stream))
        w = self.open_desc(writing_stream, 'wb')
        super().__init__(
            reading_stream=r,
            writing_stream=w,
            **kwargs,
        )

    def handle_commit(self):
        self.send_commit()
        return super().handle_commit()

    def run(self):
        while True:
            r = self.handle_transaction()
            if r == 0:
                break


class ConnectionToServer(Connection):
    def __init__(self, reading_stream, writing_stream, **kwargs):
        logger.debug("opening writing connection to server: {}".format(writing_stream))
        w = self.open_desc(writing_stream, 'wb')
        logger.debug("opening reading connection to server: {}".format(reading_stream))
        r = self.open_desc(reading_stream, 'rb')
        super().__init__(
            reading_stream=r,
            writing_stream=w,
            **kwargs,
        )


