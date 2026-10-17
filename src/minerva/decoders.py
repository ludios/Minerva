"""
Framers that split a stream of bytes into Minerva frames (and back).

HTTP transports use newline-delimited frames; the Flash socket transport uses
frames prefixed with a 32-bit big-endian length.

This module is private.
"""

import struct
from typing import ClassVar, Protocol


class FrameTooLong(Exception):
    """
    The peer sent (or is sending) a frame longer than the decoder's
    `max_length`.  The stream can't be decoded any further.
    """


class StringTooLongError(Exception):
    """
    The string is too long to encode.
    """


class Decoder(Protocol):
    def feed(self, data: bytes) -> list[bytes]: ...

    @classmethod
    def encode(cls, frame: bytes) -> bytes: ...


class DelimitedStringDecoder:
    """
    Decodes a stream of newline-terminated byte strings.
    """

    # This *must* be 1 byte; `feed` relies on it.
    delimiter: ClassVar[bytes] = b"\n"

    def __init__(self, max_length: int) -> None:
        self.max_length = max_length
        self._buffer = bytearray()

    @classmethod
    def encode(cls, frame: bytes) -> bytes:
        """
        Delimit `frame`.  The caller must make sure that it contains no
        delimiter bytes.
        """
        return frame + cls.delimiter

    def feed(self, data: bytes) -> list[bytes]:
        """
        Add `data` to the buffer and return the complete frames in it.

        Raises `FrameTooLong` if a frame exceeds `max_length`, and keeps
        raising it if fed more data afterwards.
        """
        self._buffer += data
        buffer = self._buffer
        # Look for the delimiter only in the new data, so that a peer can't
        # make us repeatedly rescan a big buffer by dribbling in one byte at a
        # time.  This works because the delimiter is a single byte.
        if self.delimiter not in data:
            self._check_length(len(buffer))
            return []

        frames = []
        at = 0
        while (end := buffer.find(self.delimiter, at)) != -1:
            self._check_length(end - at)
            frames.append(bytes(buffer[at:end]))
            at = end + 1
        del buffer[:at]
        self._check_length(len(buffer))
        return frames

    def _check_length(self, length: int) -> None:
        if length > self.max_length:
            raise FrameTooLong(f"{length} > {self.max_length}")


class Int32StringDecoder:
    """
    Decodes a stream of byte strings, each prefixed by its length as a
    big-endian unsigned 32-bit integer.
    """

    prefix: ClassVar[struct.Struct] = struct.Struct("!I")

    def __init__(self, max_length: int) -> None:
        self.max_length = max_length
        self._buffer = bytearray()

    @classmethod
    def encode(cls, frame: bytes) -> bytes:
        """
        Length-prefix `frame`.
        """
        if len(frame) >= 2 ** (8 * cls.prefix.size):
            raise StringTooLongError(
                f"Cannot encode {len(frame)} bytes in a {cls.prefix.size}-byte prefix"
            )
        return cls.prefix.pack(len(frame)) + frame

    def feed(self, data: bytes) -> list[bytes]:
        """
        Add `data` to the buffer and return the complete frames in it.

        Raises `FrameTooLong` as soon as a length prefix exceeds `max_length`,
        and keeps raising it if fed more data afterwards.
        """
        self._buffer += data
        buffer = self._buffer
        prefix_length = self.prefix.size
        frames = []
        at = 0
        # Keep in mind that 0-length frames are valid.
        while len(buffer) - at >= prefix_length:
            (length,) = self.prefix.unpack_from(buffer, at)
            if length > self.max_length:
                raise FrameTooLong(f"{length} > {self.max_length}")
            start = at + prefix_length
            if len(buffer) - start < length:
                break
            frames.append(bytes(buffer[start : start + length]))
            at = start + length
        del buffer[:at]
        return frames
