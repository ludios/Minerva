"""
Ready-made `StringProtocol`s: one that dispatches to a subprotocol chosen by
the client, and one that adapts a `QANProtocol`.
"""

import logging
from collections.abc import Mapping

from twisted.python.failure import Failure

from minerva.interfaces import QANProtocol, StringFactory, StringProtocol
from minerva.qan import (
    InvalidQANFrame,
    QANFrame,
    QANHelper,
    qan_frame_to_string,
    string_to_qan_frame,
)
from minerva.stream import ServerStream

logger = logging.getLogger(__name__)


def _log_failure(message: str, failure: Failure) -> None:
    exception = failure.value
    assert exception is not None
    logger.error(
        "%s",
        message,
        exc_info=(type(exception), exception, failure.getTracebackObject()),
    )


class SubprotocolFactory:
    """
    Builds protocols that pass strings on to a subprotocol, chosen by the
    client with a first string of the form `subprotocol:<name>`.
    """

    def __init__(self, subfactories: Mapping[str, StringFactory]) -> None:
        self._subfactories = subfactories

    def get_subfactory(self, name: str) -> StringFactory | None:
        return self._subfactories.get(name)

    def build_protocol(self) -> SubprotocolProtocol:
        return SubprotocolProtocol(self)


class SubprotocolProtocol:
    def __init__(self, factory: SubprotocolFactory) -> None:
        self.factory = factory
        self.stream: ServerStream | None = None
        self._child: StringProtocol | None = None

    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream

    def string_received(self, s: str) -> None:
        if self._child is not None:
            self._child.string_received(s)
            return

        assert self.stream is not None
        name = s.removeprefix("subprotocol:")
        if name == s:
            self.stream.reset("no subprotocol; send a subprotocol:... string first")
        elif (subfactory := self.factory.get_subfactory(name)) is None:
            self.stream.reset("unknown subprotocol")
        else:
            self._child = subfactory.build_protocol()
            self._child.stream_started(self.stream)

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        logger.info("Stream reset: %r, %r", reason_string, application_level)
        self.stream = None
        if self._child is not None:
            self._child.stream_reset(reason_string, application_level)


class QANProtocolWrapper:
    """
    A `StringProtocol` that makes your `QANProtocol` work.
    """

    def __init__(self, qan_protocol: QANProtocol, validate_bodies: bool = True) -> None:
        """
        If `validate_bodies`, check that the bodies of the questions and
        answers you send are restricted strings.  Turn this off only if you're
        sure your application gets that right.
        """
        self.qan_protocol = qan_protocol
        self._validate_bodies = validate_bodies
        self.stream: ServerStream | None = None
        self.qan_helper: QANHelper | None = None

    def _send_qan_frame(self, frame: QANFrame) -> None:
        assert self.stream is not None
        self.stream.send_string(
            qan_frame_to_string(frame), validate=self._validate_bodies
        )

    def _fatal_error(self, reason: str) -> None:
        assert self.stream is not None
        self.stream.reset(f"QANHelper said: {reason}")

    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream
        self.qan_helper = QANHelper(
            self.qan_protocol.body_received,
            _log_failure,
            self._send_qan_frame,
            self._fatal_error,
        )
        self.qan_protocol.stream_started(stream, self.qan_helper)

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        assert self.qan_helper is not None
        self.qan_helper.fail_all(
            f"Stream reset application_level={application_level!r}, "
            f"reason: {reason_string}"
        )
        self.qan_protocol.stream_reset(reason_string, application_level)

    def string_received(self, s: str) -> None:
        assert self.stream is not None
        assert self.qan_helper is not None
        try:
            frame = string_to_qan_frame(s)
        except InvalidQANFrame:
            self.stream.reset("Bad QAN frame.  Did peer send a non-QAN string?")
        else:
            self.qan_helper.handle_qan_frame(frame)
