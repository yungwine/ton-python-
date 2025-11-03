import struct

from tl.tlobject import TLObject


class BinaryReader:

    def __init__(self, data: bytes, tl_objects: dict[int, TLObject]):
        self.stream = data or b''
        self.position = 0
        self._last = None  # Should come in handy to spot -404 errors
        self.tl_objects = tl_objects

    # "All numbers are written as little endian."
    # https://core.telegram.org/mtproto
    def read_byte(self):
        """Reads a single byte value."""
        value, = struct.unpack_from("<B", self.stream, self.position)
        self.position += 1
        return value

    def read_int(self, signed=True):
        """Reads an integer (4 bytes) value."""
        fmt = '<i' if signed else '<I'
        value, = struct.unpack_from(fmt, self.stream, self.position)
        self.position += 4
        return value

    def read_long(self, signed=True):
        """Reads a long integer (8 bytes) value."""
        fmt = '<q' if signed else '<Q'
        value, = struct.unpack_from(fmt, self.stream, self.position)
        self.position += 8
        return value

    def read_double(self):
        """Reads a real floating point (8 bytes) value."""
        value, = struct.unpack_from("<d", self.stream, self.position)
        self.position += 8
        return value

    def read_large_int(self, bits, signed=True):
        """Reads a n-bits long integer value."""
        return int.from_bytes(
            self.read(bits // 8), byteorder='little', signed=signed)

    def read(self, length=-1):
        """Read the given amount of bytes, or -1 to read all remaining."""
        if length >= 0:
            result = self.stream[self.position:self.position + length]
            self.position += length
        else:
            result = self.stream[self.position:]
            self.position += len(result)
        if (length >= 0) and (len(result) != length):
            raise BufferError(
                'No more data left to read (need {}, got {}: {}); last read {}'
                .format(length, len(result), repr(result), repr(self._last))
            )

        self._last = result
        return result

    def get_bytes(self):
        """Gets the byte array representing the current buffer as a whole."""
        return self.stream

    def tgread_bytes(self):
        """
        Reads a Telegram-encoded byte array, without the need of
        specifying its length.
        """
        first_byte = self.read_byte()
        if first_byte == 254:
            length = self.read_byte() | (self.read_byte() << 8) | (
                self.read_byte() << 16)
            padding = length % 4
        else:
            length = first_byte
            padding = (length + 1) % 4

        data = self.read(length)
        if padding > 0:
            padding = 4 - padding
            self.read(padding)

        return data

    def tgread_string(self):
        """Reads a Telegram-encoded string."""
        return str(self.tgread_bytes(), encoding='utf-8', errors='replace')

    def tgread_bool(self):
        """Reads a Telegram boolean value."""
        value = self.read_int(signed=False)
        if value == 0x997275b5:  # boolTrue
            return True
        elif value == 0xbc799737:  # boolFalse
            return False
        else:
            raise RuntimeError('Invalid boolean code {}'.format(hex(value)))

    def tgread_object(self):
        """Reads a TL object."""
        constructor_id = self.read_int(signed=False)
        class_ = self.tl_objects.get(constructor_id, None)
        if class_ is None:
            # The class was None, but there's still a
            # chance of it being a manually parsed value like bool!
            value = constructor_id
            if value == 0x997275b5:  # boolTrue
                return True
            elif value == 0xbc799737:  # boolFalse
                return False
            elif value == 0x1cb5c415:  # Vector
                return [self.tgread_object() for _ in range(self.read_int())]

            self.seek(-4)  # Go back
            pos = self.position
            error = Exception(constructor_id, self.read())
            self.position = pos
            raise error

        return class_.from_reader(self)


    def close(self):
        """Closes the reader, freeing the BytesIO stream."""
        self.stream = b''

    def seek(self, offset):
        """
        Seeks the stream position given an offset from the current position.
        The offset may be negative.
        """
        self.position += offset

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
