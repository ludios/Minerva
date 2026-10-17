import contextlib
import json
import string
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from minerva.frames import (
    MAX_SAFE_INT,
    ClientFrame,
    CommentFrame,
    HelloFrame,
    HttpFormat,
    InvalidFrame,
    InvalidHello,
    KillReason,
    ResetFrame,
    SackFrame,
    SeqNumFrame,
    ServerFrame,
    StreamCreatedFrame,
    StreamStatusFrame,
    StringFrame,
    TransportKillFrame,
    YouCloseItFrame,
    decode_frame_from_client,
    decode_frame_from_server,
    encode_hello_json,
    is_restricted_string,
    sack_from_string,
    sack_to_string,
)
from minerva.window import SACK
from tests.helpers import make_hello

# --- Strategies ---------------------------------------------------------------

restricted_text = st.text(
    alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E)
)
seq_nums = st.integers(min_value=0, max_value=MAX_SAFE_INT)
sacks = st.builds(
    SACK,
    st.integers(min_value=-1, max_value=MAX_SAFE_INT),
    st.lists(seq_nums, unique=True).map(lambda xs: tuple(sorted(xs))),
)


@st.composite
def hello_frames(draw: st.DrawFn) -> HelloFrame:
    wants_strings = draw(st.booleans())
    return HelloFrame(
        transport_number=draw(seq_nums),
        stream_id=draw(st.text(alphabet=string.printable, min_size=20, max_size=30)),
        streaming_response=draw(st.booleans()),
        max_inactivity=draw(st.integers(min_value=0, max_value=600)),
        last_sack_seen_by_client=draw(sacks),
        request_new_stream=draw(st.booleans()),
        wants_strings=wants_strings,
        succeeds_transport=draw(st.none() | seq_nums) if wants_strings else None,
        http_format=draw(st.none() | st.sampled_from(HttpFormat)),
        need_padding_bytes=draw(st.integers(min_value=0, max_value=16 * 1024)),
        max_receive_bytes=draw(seq_nums),
        max_open_time=draw(st.none() | seq_nums),
        sack=draw(st.none() | sacks),
    )


common_frames = st.one_of(
    st.builds(StringFrame, restricted_text),
    st.builds(SeqNumFrame, seq_nums),
    st.builds(SackFrame, sacks),
    st.builds(
        ResetFrame, restricted_text.filter(lambda s: len(s) <= 255), st.booleans()
    ),
)
client_frames: st.SearchStrategy[ClientFrame] = common_frames | hello_frames()
server_frames: st.SearchStrategy[ServerFrame] = common_frames | st.one_of(
    st.builds(CommentFrame, restricted_text),
    st.builds(StreamStatusFrame, sacks),
    st.just(StreamCreatedFrame()),
    st.just(YouCloseItFrame()),
    st.builds(TransportKillFrame, st.sampled_from(KillReason)),
)

json_values = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    # Mostly realistic strings, sometimes SACK-like ones.
    | st.text()
    | st.from_regex(r"\A[0-9,]*\|-?[0-9]+\Z"),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=5,
)
HELLO_KEYS = make_hello(wants_strings=True, sack=SACK(-1)).to_json_dict().keys()


# --- Properties -----------------------------------------------------------------


@given(st.text())
def test_is_restricted_string(s: str) -> None:
    assert is_restricted_string(s) == all(" " <= c <= "~" for c in s)


@given(sacks)
def test_sack_string_roundtrip(sack: SACK) -> None:
    assert sack_from_string(sack_to_string(sack)) == sack


@given(client_frames)
def test_client_frame_roundtrip(frame: ClientFrame) -> None:
    assert decode_frame_from_client(frame.encode()) == frame


@given(server_frames)
def test_server_frame_roundtrip(frame: ServerFrame) -> None:
    assert decode_frame_from_server(frame.encode()) == frame


frame_like_bytes = st.binary() | st.builds(
    lambda body, type_char: body.encode("ascii") + type_char,
    restricted_text,
    st.sampled_from([bytes([c]) for c in b' ^NATCY!KH"?']),
)


@given(frame_like_bytes)
def test_decoding_only_raises_invalid_frame(data: bytes) -> None:
    """
    No matter what a peer sends, decoding either works or raises
    `InvalidFrame` -- any other exception would escape the transport.
    """
    for decode in (decode_frame_from_client, decode_frame_from_server):
        with contextlib.suppress(InvalidFrame):
            decode(data)


@given(st.dictionaries(st.sampled_from(sorted(HELLO_KEYS)), json_values))
def test_hello_decoding_only_raises_invalid_hello(data: dict[str, Any]) -> None:
    with contextlib.suppress(InvalidHello):
        HelloFrame.decode(encode_hello_json(data).decode("ascii"))


# --- HelloFrame -----------------------------------------------------------------

DELETE = sentinel("DELETE")


def hello_json(**overrides: object) -> str:
    """
    The text of a valid hello frame, with keys of its JSON object replaced (or
    deleted with `DELETE`).
    """
    data = make_hello().to_json_dict()
    for key, value in overrides.items():
        if value is DELETE:
            data.pop(key, None)
        else:
            data[key] = value
    return encode_hello_json(data).decode("ascii")


GENERIC_BAD: list[object] = [
    -(2**65),
    -1,
    -0.5,
    0.5,
    2**53 + 1,
    "",
    [],
    ["something"],
    {},
    True,
    False,
    None,
]
BAD_HELLO_VALUES: dict[str, list[object]] = {
    "tnum": [DELETE, *GENERIC_BAD],
    "ver": [DELETE, 0, 1, "1", 1.001, *GENERIC_BAD],
    "id": [
        DELETE,
        "",
        "\x00",
        "x",
        "쳌" * 25,
        "쳌" * 8,
        "\x80" * 25,
        "x" * 19,  # below the limit
        "x" * 31,  # over the limit
        "x" * 3000,
        *GENERIC_BAD,
    ],
    "format": [4, 1, 0, *GENERIC_BAD],
    "ming": [2, 3, *(v for v in GENERIC_BAD if v is not True and v is not False)],
    "maxb": GENERIC_BAD,
    "maxt": GENERIC_BAD,
    "maxia": [DELETE, None, 0.5, 1.5, 601],
    "pad": [16 * 1024 + 1, *GENERIC_BAD],
    "sack": ["", "|", "|-2", "-2|-1", 4],
    "seenack": [DELETE, "", "|", "|-2", "-2|-1", 4],
}


class TestHelloFrame:
    def test_decode(self) -> None:
        assert HelloFrame.decode(hello_json()) == HelloFrame(
            transport_number=0,
            request_new_stream=True,
            protocol_version=2,
            stream_id="x" * 26,
            streaming_response=True,
            max_receive_bytes=2**30,
            max_open_time=2**30,
            max_inactivity=0,
            need_padding_bytes=0,
            http_format=None,
            sack=None,
            last_sack_seen_by_client=SACK(-1, ()),
        )

    def test_encode(self) -> None:
        hello = make_hello(max_open_time=None)
        assert hello.encode() == (
            b'{"tnum":0,"ver":2,"new":true,"id":"xxxxxxxxxxxxxxxxxxxxxxxxxx","ming":true,'
            b'"pad":0,"maxb":1073741824,"maxia":0,"seenack":"|-1"}H'
        )

    def test_numbers_may_be_integral_floats(self) -> None:
        hello = HelloFrame.decode(hello_json(tnum=3.0, maxia=1.0, new=1, ming=0))
        assert hello.transport_number == 3
        assert type(hello.transport_number) is int
        assert hello.max_inactivity == 1
        assert hello.request_new_stream is True
        assert hello.streaming_response is False

    @pytest.mark.parametrize(
        ("eeds", "wants_strings", "succeeds_transport"),
        [(DELETE, False, None), (None, True, None), (3, True, 3)],
    )
    def test_succeeds_transport(
        self, eeds: object, wants_strings: bool, succeeds_transport: int | None
    ) -> None:
        """
        The *presence* of "eeds" means that the client wants strings; its value
        is the transport that this one may succeed.
        """
        hello = HelloFrame.decode(hello_json(eeds=eeds))
        assert hello.wants_strings is wants_strings
        assert hello.succeeds_transport == succeeds_transport

    @pytest.mark.parametrize(
        "eeds", [-1, -(2**32), -0.5, 2**53 + 1, "4", True, False, [], {}]
    )
    def test_bad_succeeds_transport(self, eeds: object) -> None:
        with pytest.raises(InvalidHello):
            HelloFrame.decode(hello_json(eeds=eeds))

    @pytest.mark.parametrize(
        "text",
        [
            '{"":' * 20000 + "1" + "}" * 20000,
            "[" * 20000 + "1" + "]" * 20000,
            # Deep enough to raise RecursionError inside the json module.
            "[" * 500_000 + "1" + "]" * 500_000,
        ],
    )
    def test_too_much_nesting(self, text: str) -> None:
        with pytest.raises(InvalidHello):
            HelloFrame.decode(text + "H")

    def test_trailing_garbage(self) -> None:
        with pytest.raises(InvalidHello):
            HelloFrame.decode(hello_json()[:-1] + "xH")

    def test_leading_whitespace(self) -> None:
        with pytest.raises(InvalidHello):
            HelloFrame.decode(" " + hello_json())

    @pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
    def test_nan_and_infinity(self, constant: str) -> None:
        text = hello_json().replace('"tnum":0', f'"tnum":{constant}')
        with pytest.raises(InvalidHello):
            HelloFrame.decode(text)

    def test_huge_float(self) -> None:
        """
        `1e999` is valid JSON that decodes to `inf`; it must not escape as an
        `OverflowError` (it did in the Python 2 version).
        """
        text = hello_json().replace('"tnum":0', '"tnum":1e999')
        with pytest.raises(InvalidHello):
            HelloFrame.decode(text)

    @pytest.mark.parametrize("hello", ["[]H", '"hi"H', "1H", "nullH", "H"])
    def test_not_an_object(self, hello: str) -> None:
        with pytest.raises(InvalidHello):
            HelloFrame.decode(hello)

    def test_non_ascii_string_for_unknown_key(self) -> None:
        with pytest.raises(InvalidHello):
            HelloFrame.decode(hello_json(unknown="\N{SNOWMAN}"))

    @pytest.mark.parametrize(
        ("key", "value"), [(k, v) for k, vs in BAD_HELLO_VALUES.items() for v in vs]
    )
    def test_invalid_values(self, key: str, value: object) -> None:
        with pytest.raises(InvalidHello):
            HelloFrame.decode(hello_json(**{key: value}))

    def test_encode_decode_equality(self) -> None:
        hello = make_hello(
            http_format=HttpFormat.XHR,
            max_inactivity=1,
            sack=SACK(-1, ()),
            wants_strings=True,
            succeeds_transport=5,
        )
        assert HelloFrame.decode(hello.encode().decode()) == hello


# --- The other frames -----------------------------------------------------------


class TestEquality:
    def test_same_fields_different_types(self) -> None:
        assert StringFrame("x") != CommentFrame("x")
        assert SackFrame(SACK(2, ())) != StreamStatusFrame(SACK(2, ()))
        assert StreamCreatedFrame() != YouCloseItFrame()
        assert StreamCreatedFrame() != ()

    def test_fields(self) -> None:
        assert StringFrame("Hello") == StringFrame("Hello")
        assert StringFrame("Hello") != StringFrame("Hello2")
        assert SeqNumFrame(2) != SeqNumFrame(3)
        assert SackFrame(SACK(2, (1,))) != SackFrame(SACK(3, (2,)))
        assert ResetFrame("why", True) != ResetFrame("why", False)
        assert ResetFrame("why2", True) != ResetFrame("why", True)
        assert TransportKillFrame(
            KillReason.STREAM_ATTACH_FAILURE
        ) != TransportKillFrame(KillReason.ACKED_UNSENT_STRINGS)


def test_repr() -> None:
    assert (
        repr(SackFrame(SACK(2, (1, 4))))
        == "SackFrame(sack=SACK(ack_number=2, sack_list=(1, 4)))"
    )


class TestStringFrame:
    def test_decode_does_not_validate(self) -> None:
        """
        Restricted-string validation is the receiver's job.
        """
        assert StringFrame.decode("\x00unchecked\ttext ") == StringFrame(
            "\x00unchecked\ttext"
        )

    def test_encode(self) -> None:
        assert StringFrame("hello").encode() == b"hello "


class TestCommentFrame:
    def test_decode(self) -> None:
        assert CommentFrame.decode("\x00unchecked\ttext^") == CommentFrame(
            "\x00unchecked\ttext"
        )

    def test_encode(self) -> None:
        assert CommentFrame(";)]}").encode() == b";)]}^"


class TestSeqNumFrame:
    @pytest.mark.parametrize("seq_num", [0, 1, 2**32, 2**53])
    def test_decode(self, seq_num: int) -> None:
        assert SeqNumFrame.decode(f"{seq_num}N") == SeqNumFrame(seq_num)

    @pytest.mark.parametrize(
        "text", ["-1N", f"{-(2**53)}N", f"{2**53 + 1}N", " ", "00N", "0" * 1024]
    )
    def test_decode_failed(self, text: str) -> None:
        with pytest.raises(InvalidFrame):
            SeqNumFrame.decode(text)

    def test_encode(self) -> None:
        assert SeqNumFrame(2).encode() == b"2N"
        assert SeqNumFrame(0).encode() == b"0N"
        assert SeqNumFrame(2**53).encode() == b"%dN" % 2**53


class TestSackFrame:
    @pytest.mark.parametrize("ack_number", [-1, 0, 1, 2**53])
    def test_decode(self, ack_number: int) -> None:
        assert SackFrame.decode(f"1,4|{ack_number}A") == SackFrame(
            SACK(ack_number, (1, 4))
        )

    def test_decode_no_sack_numbers(self) -> None:
        assert SackFrame.decode(f"|{2**53}A") == SackFrame(SACK(2**53, ()))

    @pytest.mark.parametrize("bad_num", [2**53 + 1, -2, -1.01, 0.5, 1.5])
    def test_bad_ack_number(self, bad_num: object) -> None:
        with pytest.raises(InvalidFrame):
            SackFrame.decode(f"1,4|{bad_num}A")

    @pytest.mark.parametrize("bad_num", [2**53 + 1, -1, 0.5, 1.5])
    def test_bad_sack_number(self, bad_num: object) -> None:
        with pytest.raises(InvalidFrame):
            SackFrame.decode(f"1,{bad_num}|4A")

    @pytest.mark.parametrize("text", ["||4A", "", " ", "|", "1,,2|4A", ",|4A"])
    def test_malformed(self, text: str) -> None:
        with pytest.raises(InvalidFrame):
            SackFrame.decode(text)

    def test_encode(self) -> None:
        assert SackFrame(SACK(2, (1, 4))).encode() == b"1,4|2A"
        assert SackFrame(SACK(2, (4,))).encode() == b"4|2A"
        assert SackFrame(SACK(2, ())).encode() == b"|2A"


class TestStreamStatusFrame:
    """
    StreamStatusFrame is encoded just like SackFrame, so it needs fewer tests.
    """

    def test_decode(self) -> None:
        assert StreamStatusFrame.decode("1,4|2T") == StreamStatusFrame(SACK(2, (1, 4)))

    def test_encode(self) -> None:
        assert StreamStatusFrame(SACK(2, (1, 4))).encode() == b"1,4|2T"


@pytest.mark.parametrize("frame_type", [StreamCreatedFrame, YouCloseItFrame])
class TestArgumentlessFrames:
    def test_decode(
        self, frame_type: type[StreamCreatedFrame | YouCloseItFrame]
    ) -> None:
        assert frame_type.decode(frame_type.TYPE) == frame_type()

    def test_leading_garbage(
        self, frame_type: type[StreamCreatedFrame | YouCloseItFrame]
    ) -> None:
        with pytest.raises(InvalidFrame):
            frame_type.decode("extra stuff" + frame_type.TYPE)

    def test_encode(
        self, frame_type: type[StreamCreatedFrame | YouCloseItFrame]
    ) -> None:
        assert frame_type().encode() == frame_type.TYPE.encode()


class TestResetFrame:
    def test_encode(self) -> None:
        assert ResetFrame("the reason", False).encode() == b"the reason|0!"
        assert ResetFrame("the reason", True).encode() == b"the reason|1!"

    @pytest.mark.parametrize("application_level", [True, False])
    @pytest.mark.parametrize("reason", ["the reason", "the | | reason", "", "|", "||"])
    def test_decode(self, reason: str, application_level: bool) -> None:
        text = f"{reason}|{int(application_level)}!"
        assert ResetFrame.decode(text) == ResetFrame(reason, application_level)

    @pytest.mark.parametrize(
        "text",
        [
            "\x7freason|0!",  # illegal character
            "x" * 256 + "|0!",  # too long
            "reason|2!",  # bad applicationLevel
            "reason!",  # no applicationLevel; raised ValueError in the Python 2 version
        ],
    )
    def test_decode_failed(self, text: str) -> None:
        with pytest.raises(InvalidFrame):
            ResetFrame.decode(text)


class TestTransportKillFrame:
    def test_encode(self) -> None:
        assert (
            TransportKillFrame(KillReason.FRAME_CORRUPTION).encode()
            == b"frame_corruptionK"
        )

    @pytest.mark.parametrize("reason", KillReason)
    def test_decode(self, reason: KillReason) -> None:
        assert TransportKillFrame.decode(reason + "K") == TransportKillFrame(reason)

    def test_decode_failed(self) -> None:
        with pytest.raises(InvalidFrame):
            TransportKillFrame.decode("not_a_reasonK")


# --- Dispatch -------------------------------------------------------------------


class TestDecodeFrame:
    @pytest.mark.parametrize(
        ("data", "frame"),
        [
            (b"hi ", StringFrame("hi")),
            (b"|1A", SackFrame(SACK(1))),
            (b"7N", SeqNumFrame(7)),
            (b"why|1!", ResetFrame("why", True)),
            (make_hello().encode(), make_hello()),
        ],
    )
    def test_from_client(self, data: bytes, frame: ClientFrame) -> None:
        assert decode_frame_from_client(data) == frame

    @pytest.mark.parametrize(
        ("data", "frame"),
        [
            (b"hi ", StringFrame("hi")),
            (b"|1A", SackFrame(SACK(1))),
            (b"7N", SeqNumFrame(7)),
            (b"|1T", StreamStatusFrame(SACK(1))),
            (b"Y", YouCloseItFrame()),
            (b"beat^", CommentFrame("beat")),
            (b"C", StreamCreatedFrame()),
            (b"why|1!", ResetFrame("why", True)),
            (b"rwin_overflowK", TransportKillFrame(KillReason.RWIN_OVERFLOW)),
        ],
    )
    def test_from_server(self, data: bytes, frame: ServerFrame) -> None:
        assert decode_frame_from_server(data) == frame

    @pytest.mark.parametrize("data", [b"", b"?", b"x?", b"\xff ", b"caf\xc3\xa9 "])
    def test_invalid(self, data: bytes) -> None:
        with pytest.raises(InvalidFrame):
            decode_frame_from_client(data)
        with pytest.raises(InvalidFrame):
            decode_frame_from_server(data)

    @pytest.mark.parametrize("data", [b"beat^", b"C", b"Y", b"|1T", b"rwin_overflowK"])
    def test_server_only_frames_from_client(self, data: bytes) -> None:
        with pytest.raises(InvalidFrame):
            decode_frame_from_client(data)

    def test_hello_from_server(self) -> None:
        with pytest.raises(InvalidFrame):
            decode_frame_from_server(make_hello().encode())


def test_hello_json_is_compact() -> None:
    assert b" " not in encode_hello_json({"a": [1, 2], "b": {"c": None}})
    assert json.loads(encode_hello_json({"a": 1})[:-1]) == {"a": 1}
