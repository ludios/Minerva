"""
Minerva frames, and their wire encodings.

A frame is ASCII text whose *last* character determines its type.  There are
encoders for frames the server never sends (and decoders for frames it never
receives): they're used by the tests, and would be needed by a Python client.

Design note: frames that carry arbitrary text use a non-`[A-Za-z]` type
character, so that frames can't accidentally form words that proxies block.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Any, ClassVar, Self

from minerva.objcheck import (
    ensure_bool,
    ensure_non_neg_int_limit,
    str_to_int_in_range,
    str_to_non_neg_limit,
)
from minerva.window import SACK

# The largest integer that JavaScript can represent exactly; also the limit
# for sequence numbers and transport numbers.
MAX_SAFE_INT = 2**53


class InvalidFrame(Exception):
    pass


class InvalidHello(InvalidFrame):
    pass


def is_restricted_string(s: str) -> bool:
    """
    Is every character of `s` within the inclusive range `" "` - `"~"`?

    Minerva strings are restricted to these characters.
    """
    # For ASCII, "printable" is exactly 0x20 (space) to 0x7E (~).
    return s.isascii() and s.isprintable()


def sack_to_string(sack: SACK) -> str:
    return ",".join(map(str, sack.sack_list)) + "|" + str(sack.ack_number)


def sack_from_string(s: str) -> SACK:
    """
    Parse the output of `sack_to_string`.  Raises `ValueError` if malformed.
    """
    joined_sack_list, sep, ack_number = s.rpartition("|")
    if not sep:
        raise ValueError(f"no '|' in SACK string {s!r}")
    return SACK(
        str_to_int_in_range(ack_number, -1, MAX_SAFE_INT),
        tuple(
            str_to_non_neg_limit(n, MAX_SAFE_INT) for n in joined_sack_list.split(",")
        )
        if joined_sack_list
        else (),
    )


class HttpFormat(IntEnum):
    XHR = 2
    HTMLFILE = 3


def _strict_json_loads(s: str) -> Any:
    """
    Decode JSON, rejecting leading whitespace, trailing garbage, and the
    non-standard `NaN`, `Infinity`, and `-Infinity`.
    """

    def reject_constant(name: str) -> None:
        raise ValueError(f"{name} is not allowed")

    value, end = json.JSONDecoder(parse_constant=reject_constant).raw_decode(s)
    if end != len(s):
        raise ValueError(f"{len(s) - end} trailing characters after JSON")
    return value


# Marks a required field in `_parse_field`.
_REQUIRED = sentinel("_REQUIRED")


def _parse_field[T, D](
    data: Mapping[str, Any],
    key: str,
    parse: Callable[[Any], T],
    default: D | _REQUIRED = _REQUIRED,
) -> T | D:
    """
    Parse `data[key]` with `parse`, converting any problem into `InvalidHello`.
    """
    if key not in data:
        if default is _REQUIRED:
            raise InvalidHello(f"missing {key!r}")
        return default
    try:
        return parse(data[key])
    except (TypeError, ValueError) as e:
        raise InvalidHello(f"bad {key!r}: {e}") from None


def _parse_sack(value: object) -> SACK:
    if not isinstance(value, str):
        raise TypeError(f"{value!r} is not a str")
    return sack_from_string(value)


def _parse_stream_id(value: object) -> str:
    if not isinstance(value, str) or not 20 <= len(value) <= 30:
        raise ValueError(f"{value!r} is not a 20-30 character str")
    return value


def _parse_protocol_version(value: object) -> int:
    if value != 2:
        raise ValueError(f"unsupported protocol version {value!r}")
    return 2


def _non_neg_int_up_to(limit: int) -> Callable[[object], int]:
    return lambda value: ensure_non_neg_int_limit(value, limit)


def _parse_optional_transport_number(value: object) -> int | None:
    return None if value is None else ensure_non_neg_int_limit(value, MAX_SAFE_INT)


@dataclass(frozen=True, slots=True, kw_only=True)
class HelloFrame:
    """
    The first frame a client sends over every transport.
    """

    TYPE: ClassVar[str] = "H"

    transport_number: int
    stream_id: str
    streaming_response: bool
    # Seconds of S2C inactivity after which the server sends a heartbeat; 0
    # disables heartbeats.
    max_inactivity: int
    last_sack_seen_by_client: SACK
    protocol_version: int = 2
    # If false, the transport wants to attach to an existing stream.
    request_new_stream: bool = False
    # Does the client want to receive strings over this transport?
    wants_strings: bool = False
    # If the client wants strings, maybe the transport this one replaces.
    succeeds_transport: int | None = None
    http_format: HttpFormat | None = None
    need_padding_bytes: int = 0
    max_receive_bytes: int = MAX_SAFE_INT
    # In seconds; `None` means no limit.
    max_open_time: int | None = None
    sack: SACK | None = None

    def to_json_dict(self) -> dict[str, Any]:
        """
        Return the JSON object that this frame is encoded as.  (See
        `from_json_dict` for the wire names of the fields.)
        """
        data: dict[str, Any] = {
            "tnum": self.transport_number,
            "ver": self.protocol_version,
            "new": self.request_new_stream,
            "id": self.stream_id,
            "ming": self.streaming_response,
            "pad": self.need_padding_bytes,
            "maxb": self.max_receive_bytes,
            "maxia": self.max_inactivity,
            "seenack": sack_to_string(self.last_sack_seen_by_client),
        }
        # Optional fields are omitted rather than sent as `null`, because
        # `null` means something else (or is invalid) for them.
        if self.wants_strings:
            data["eeds"] = self.succeeds_transport
        if self.http_format is not None:
            data["format"] = int(self.http_format)
        if self.max_open_time is not None:
            data["maxt"] = self.max_open_time
        if self.sack is not None:
            data["sack"] = sack_to_string(self.sack)
        return data

    def encode(self) -> bytes:
        return encode_hello_json(self.to_json_dict())

    @classmethod
    def decode(cls, text: str) -> Self:
        """
        Decode `text`, which ends with "H".  Raises `InvalidHello` for
        anything other than a well-formed hello frame.
        """
        try:
            data = _strict_json_loads(text[:-1])
        except ValueError, RecursionError:
            # RecursionError is raised for very deeply nested JSON.
            raise InvalidHello("corrupt JSON") from None
        return cls.from_json_dict(data)

    @classmethod
    def from_json_dict(cls, data: object) -> Self:
        if not isinstance(data, dict):
            raise InvalidHello("hello is not a JSON object")
        if any(isinstance(v, str) and not v.isascii() for v in data.values()):
            raise InvalidHello("hello contains a non-ASCII string")

        return cls(
            transport_number=_parse_field(
                data, "tnum", _non_neg_int_up_to(MAX_SAFE_INT)
            ),
            protocol_version=_parse_field(data, "ver", _parse_protocol_version),
            stream_id=_parse_field(data, "id", _parse_stream_id),
            streaming_response=_parse_field(data, "ming", ensure_bool),
            max_inactivity=_parse_field(data, "maxia", _non_neg_int_up_to(600)),
            last_sack_seen_by_client=_parse_field(data, "seenack", _parse_sack),
            request_new_stream=_parse_field(data, "new", ensure_bool, default=False),
            # The *presence* of "eeds" means that the client wants strings.
            wants_strings="eeds" in data,
            succeeds_transport=_parse_field(
                data, "eeds", _parse_optional_transport_number, default=None
            ),
            http_format=_parse_field(data, "format", HttpFormat, default=None),
            need_padding_bytes=_parse_field(
                data, "pad", _non_neg_int_up_to(16 * 1024), default=0
            ),
            max_receive_bytes=_parse_field(
                data, "maxb", _non_neg_int_up_to(MAX_SAFE_INT), default=MAX_SAFE_INT
            ),
            max_open_time=_parse_field(
                data, "maxt", _non_neg_int_up_to(MAX_SAFE_INT), default=None
            ),
            sack=_parse_field(data, "sack", _parse_sack, default=None),
        )


def encode_hello_json(data: Mapping[str, Any]) -> bytes:
    """
    Encode a hello frame from a raw JSON object.  Tests use this to send
    invalid hello frames.
    """
    return (
        json.dumps(data, separators=(",", ":"), allow_nan=False).encode("ascii") + b"H"
    )


@dataclass(frozen=True, slots=True)
class StringFrame:
    """
    A Minerva string.  Restricted-string validation is done by the receiver,
    not here, to allow for a future extension that widens the allowed range
    mid-stream.
    """

    TYPE: ClassVar[str] = " "

    string: str

    def encode(self) -> bytes:
        return (self.string + self.TYPE).encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        return cls(text[:-1])


@dataclass(frozen=True, slots=True)
class CommentFrame:
    TYPE: ClassVar[str] = "^"

    comment: str

    def encode(self) -> bytes:
        return (self.comment + self.TYPE).encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        return cls(text[:-1])


@dataclass(frozen=True, slots=True)
class SeqNumFrame:
    """
    Sets the sequence number of the next `StringFrame`.
    """

    TYPE: ClassVar[str] = "N"

    seq_num: int

    def encode(self) -> bytes:
        return f"{self.seq_num}{self.TYPE}".encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        try:
            return cls(str_to_non_neg_limit(text[:-1], MAX_SAFE_INT))
        except ValueError:
            raise InvalidFrame("bad seqNum") from None


@dataclass(frozen=True, slots=True)
class SackFrame:
    TYPE: ClassVar[str] = "A"

    sack: SACK

    def encode(self) -> bytes:
        return (sack_to_string(self.sack) + self.TYPE).encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        try:
            return cls(sack_from_string(text[:-1]))
        except ValueError:
            raise InvalidFrame("bad sackList or ackNumber") from None


@dataclass(frozen=True, slots=True)
class StreamStatusFrame:
    """
    Tells the client which of its SACKs the server has seen most recently.
    """

    TYPE: ClassVar[str] = "T"

    last_sack_seen: SACK

    def encode(self) -> bytes:
        return (sack_to_string(self.last_sack_seen) + self.TYPE).encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        try:
            return cls(sack_from_string(text[:-1]))
        except ValueError:
            raise InvalidFrame("bad sackList or ackNumber") from None


@dataclass(frozen=True, slots=True)
class StreamCreatedFrame:
    TYPE: ClassVar[str] = "C"

    def encode(self) -> bytes:
        return self.TYPE.encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        if len(text) != 1:
            raise InvalidFrame("leading garbage")
        return cls()


@dataclass(frozen=True, slots=True)
class YouCloseItFrame:
    """
    Asks the client to close the (non-HTTP) transport.
    """

    TYPE: ClassVar[str] = "Y"

    def encode(self) -> bytes:
        return self.TYPE.encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        if len(text) != 1:
            raise InvalidFrame("leading garbage")
        return cls()


@dataclass(frozen=True, slots=True)
class ResetFrame:
    """
    The sender has given up on the stream.  A reset frame from the server
    implies a transport kill as well.
    """

    TYPE: ClassVar[str] = "!"

    # Why the stream reset: a restricted string of at most 255 characters.
    reason_string: str
    # Was the reset caused by the application (not Minerva internals)?
    application_level: bool

    def encode(self) -> bytes:
        level = "1" if self.application_level else "0"
        return f"{self.reason_string}|{level}{self.TYPE}".encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        reason_string, sep, level = text[:-1].rpartition("|")
        if not sep:
            raise InvalidFrame("no applicationLevel")
        match level:
            case "0":
                application_level = False
            case "1":
                application_level = True
            case _:
                raise InvalidFrame("bad applicationLevel")
        if len(reason_string) > 255 or not is_restricted_string(reason_string):
            raise InvalidFrame("reasonString too long or has illegal characters")
        return cls(reason_string, application_level)


class KillReason(StrEnum):
    # No such stream
    STREAM_ATTACH_FAILURE = "stream_attach_failure"
    # Peer acked strings that we never sent
    ACKED_UNSENT_STRINGS = "acked_unsent_strings"
    # Peer sent frames that we don't understand
    INVALID_FRAME_TYPE_OR_ARGUMENTS = "invalid_frame_type_or_arguments"
    # Peer sent data that could not even be decoded into frames
    FRAME_CORRUPTION = "frame_corruption"
    # Peer has caused our receive window to overflow
    RWIN_OVERFLOW = "rwin_overflow"


@dataclass(frozen=True, slots=True)
class TransportKillFrame:
    TYPE: ClassVar[str] = "K"

    reason: KillReason

    def encode(self) -> bytes:
        return (self.reason + self.TYPE).encode("ascii")

    @classmethod
    def decode(cls, text: str) -> Self:
        try:
            return cls(KillReason(text[:-1]))
        except ValueError:
            raise InvalidFrame(f"unknown kill reason {text[:-1]!r}") from None


type Frame = (
    HelloFrame
    | StringFrame
    | CommentFrame
    | SeqNumFrame
    | SackFrame
    | StreamStatusFrame
    | StreamCreatedFrame
    | YouCloseItFrame
    | ResetFrame
    | TransportKillFrame
)
type ClientFrame = HelloFrame | StringFrame | SeqNumFrame | SackFrame | ResetFrame
type ServerFrame = (
    StringFrame
    | CommentFrame
    | SeqNumFrame
    | SackFrame
    | StreamStatusFrame
    | StreamCreatedFrame
    | YouCloseItFrame
    | ResetFrame
    | TransportKillFrame
)

# Type character -> decoder.
_CLIENT_FRAME_DECODERS: Mapping[str, Callable[[str], ClientFrame]] = frozendict(
    {
        cls.TYPE: cls.decode
        for cls in (StringFrame, SackFrame, SeqNumFrame, HelloFrame, ResetFrame)
    }
)
_SERVER_FRAME_DECODERS: Mapping[str, Callable[[str], ServerFrame]] = frozendict(
    {
        cls.TYPE: cls.decode
        for cls in (
            StringFrame,
            SackFrame,
            SeqNumFrame,
            StreamStatusFrame,
            YouCloseItFrame,
            CommentFrame,
            StreamCreatedFrame,
            ResetFrame,
            TransportKillFrame,
        )
    }
)


def _decode[F](frame: bytes, decoders: Mapping[str, Callable[[str], F]]) -> F:
    try:
        text = frame.decode("ascii")
    except UnicodeDecodeError:
        raise InvalidFrame("frame contains non-ASCII bytes") from None
    if not text:
        raise InvalidFrame("0-length frame")
    try:
        decode = decoders[text[-1]]
    except KeyError:
        raise InvalidFrame(f"Invalid frame type {text[-1]!r}") from None
    return decode(text)


def decode_frame_from_client(frame: bytes) -> ClientFrame:
    """
    Decode a frame received from a Minerva client.  Raises `InvalidFrame`.
    """
    return _decode(frame, _CLIENT_FRAME_DECODERS)


def decode_frame_from_server(frame: bytes) -> ServerFrame:
    """
    Decode a frame received from a Minerva server.  Raises `InvalidFrame`.
    """
    return _decode(frame, _SERVER_FRAME_DECODERS)
