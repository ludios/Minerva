import struct
from typing import ClassVar

import pytest
from hypothesis import given
from hypothesis import strategies as st

from minerva.decoders import (
    Decoder,
    DelimitedStringDecoder,
    FrameTooLong,
    Int32StringDecoder,
    StringTooLongError,
)
from tests.helpers import dice, split_at


def test_dice() -> None:
    assert list(dice(b"hello", 1)) == [b"h", b"e", b"l", b"l", b"o"]
    assert list(dice(b"hello", 2)) == [b"he", b"ll", b"o"]
    assert list(dice(b"hello", 5)) == [b"hello"]
    assert list(dice(b"hello", 6)) == [b"hello"]
    assert list(dice(b"", 3)) == []


def feed_all(decoder: Decoder, pieces: list[bytes]) -> list[bytes]:
    frames = []
    for piece in pieces:
        frames.extend(decoder.feed(piece))
    return frames


class CommonTests:
    decoder: ClassVar[type[DelimitedStringDecoder | Int32StringDecoder]]
    strings: ClassVar[list[bytes]]
    # Each of these is too long for `max_length=50`.
    too_long_sequences: ClassVar[list[bytes]]

    @pytest.mark.parametrize("packet_size", range(1, 20))
    def test_any_packet_size(self, packet_size: int) -> None:
        """
        Frames are decoded correctly no matter how the bytes are chunked.
        """
        data = b"".join(map(self.decoder.encode, self.strings))
        decoder = self.decoder(max_length=699)
        assert feed_all(decoder, list(dice(data, packet_size))) == self.strings

    @pytest.mark.parametrize("packet_size", range(1, 20))
    def test_too_long_with_any_packet_size(self, packet_size: int) -> None:
        for sequence in self.too_long_sequences:
            decoder = self.decoder(max_length=50)
            with pytest.raises(FrameTooLong):
                feed_all(decoder, list(dice(sequence, packet_size)))

    def test_keeps_raising_after_too_long(self) -> None:
        for sequence in self.too_long_sequences:
            decoder = self.decoder(max_length=50)
            with pytest.raises(FrameTooLong):
                decoder.feed(sequence)
            with pytest.raises(FrameTooLong):
                decoder.feed(self.decoder.encode(b"ok"))


class TestDelimitedStringDecoder(CommonTests):
    decoder = DelimitedStringDecoder
    strings: ClassVar = [b"", b"hello", b"world", b"how", b"are", b"you123"]
    too_long_sequences: ClassVar = [b"x" * 51 + b"\n", b"x" * 51]

    def test_encode(self) -> None:
        assert DelimitedStringDecoder.encode(b"") == b"\n"
        assert DelimitedStringDecoder.encode(b"h") == b"h\n"
        assert DelimitedStringDecoder.encode(b"a longer string") == b"a longer string\n"
        # It doesn't check whether the frame contains the delimiter.
        assert DelimitedStringDecoder.encode(b"\n") == b"\n\n"

    def test_buffer_size_limit(self) -> None:
        """
        If 200 bytes arrive at once, with a delimiter every 8th byte, the
        frames are extracted without `FrameTooLong`, even though the buffer as
        a whole is far longer than `max_length`.
        """
        strings = [bytes([65 + i]) * 7 for i in range(20)]
        decoder = DelimitedStringDecoder(max_length=10)
        assert decoder.feed(b"".join(s + b"\n" for s in strings)) == strings

    def test_remaining_buffer_too_long(self) -> None:
        """
        If complete frames are followed by an incomplete frame that is already
        too long, `FrameTooLong` is raised.
        """
        decoder = DelimitedStringDecoder(max_length=5)
        with pytest.raises(FrameTooLong):
            decoder.feed(b"hello\nthere\n8chars")

    @given(
        frames=st.lists(st.binary().filter(lambda b: b"\n" not in b)),
        data=st.data(),
    )
    def test_any_chunking(self, frames: list[bytes], data: st.DataObject) -> None:
        stream = b"".join(map(DelimitedStringDecoder.encode, frames))
        cuts = data.draw(st.lists(st.integers(0, len(stream))).map(sorted))
        decoder = DelimitedStringDecoder(max_length=2**20)
        assert feed_all(decoder, split_at(stream, cuts)) == frames


class TestInt32StringDecoder(CommonTests):
    decoder = Int32StringDecoder
    strings: ClassVar = [b"", b"a", b"b" * 16, b"c" * 17, b"d" * 255, b"e" * 256]
    too_long_sequences: ClassVar = [b"\xff\x00\x00\x00XX", b"\xff\xff\xff\xffXX"]

    def test_zero_length_string(self) -> None:
        """
        A 0-length frame is delivered when the fourth byte of the prefix
        arrives.
        """
        decoder = Int32StringDecoder(max_length=0)
        assert decoder.feed(b"\x00") == []
        assert decoder.feed(b"\x00") == []
        assert decoder.feed(b"\x00") == []
        assert decoder.feed(b"\x00") == [b""]

    def test_partial(self) -> None:
        decoder = Int32StringDecoder(max_length=2**20)
        assert feed_all(decoder, list(dice(b"\x00\x00\x00\xffhello there", 1))) == []

    def test_encode(self) -> None:
        assert Int32StringDecoder.encode(b"foo") == b"\x00\x00\x00\x03foo"
        assert Int32StringDecoder.encode(b"b" * 16) == struct.pack("!I", 16) + b"b" * 16

    def test_decode(self) -> None:
        decoder = Int32StringDecoder(max_length=10)
        assert decoder.feed(b"\x00\x00\x00\x04ubar") == [b"ubar"]

    def test_encode_too_long(self) -> None:
        """
        A 32-bit prefix needs a 4 GiB frame to overflow, so test the overflow
        check with a 16-bit prefix instead.
        """

        class Int16StringDecoder(Int32StringDecoder):
            prefix = struct.Struct("!H")

        Int16StringDecoder.encode(b"x" * 65535)
        with pytest.raises(StringTooLongError):
            Int16StringDecoder.encode(b"x" * 65536)

    def test_length_limit_exceeded(self) -> None:
        decoder = Int32StringDecoder(max_length=10)
        with pytest.raises(FrameTooLong):
            decoder.feed(struct.pack("!I", 11))

    def test_long_string_not_delivered(self) -> None:
        """
        A frame longer than `max_length` is rejected even if it all arrives at
        once.
        """
        decoder = Int32StringDecoder(max_length=10)
        with pytest.raises(FrameTooLong):
            decoder.feed(struct.pack("!I", 11) + b"x" * 11)

    def test_length_checked_at_fourth_byte(self) -> None:
        decoder = Int32StringDecoder(max_length=10)
        # This indicates a really long frame, but the length isn't looked at
        # until all four bytes of the prefix arrive.
        assert decoder.feed(b"\xff") == []
        assert decoder.feed(b"\x00") == []
        assert decoder.feed(b"\x00") == []
        with pytest.raises(FrameTooLong):
            decoder.feed(b"\x00")

    @given(frames=st.lists(st.binary()), data=st.data())
    def test_any_chunking(self, frames: list[bytes], data: st.DataObject) -> None:
        stream = b"".join(map(Int32StringDecoder.encode, frames))
        cuts = data.draw(st.lists(st.integers(0, len(stream))).map(sorted))
        decoder = Int32StringDecoder(max_length=2**20)
        assert feed_all(decoder, split_at(stream, cuts)) == frames
