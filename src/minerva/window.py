"""
Send and receive windows for Minerva strings, analogous to TCP windows.

This module is private.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SACK:
    """
    A selective acknowledgement.

    `ack_number` is the highest sequence number up to which *everything* was
    received (`-1` if nothing was).  `sack_list` holds the sequence numbers
    above `ack_number` that were also received, in ascending order.
    """

    ack_number: int
    sack_list: tuple[int, ...] = ()


def total_size_of(s: str) -> int:
    """
    Estimate how much memory (in bytes) the string `s` consumes.
    """
    return 30 + len(s)


class Queue:
    """
    A send queue that assigns a monotonically increasing sequence number to
    each string, and keeps each string until it is SACKed.

    It keeps strings around because they may need to be re-sent over a new
    transport if the old one fails.  It also tracks how much memory the queued
    strings use, in case you want to do flow control.
    """

    def __init__(self) -> None:
        self._counter = -1
        # seqNum -> (string, size).  Strings are always appended with
        # increasing seqNums, so this dict is sorted by key.
        self._items: dict[int, tuple[str, int]] = {}
        self._size = 0

    def __repr__(self) -> str:
        return (
            f"<Queue at {id(self):#x} with {len(self)} item(s), "
            f"counter=#{self._counter}, size={self._size}>"
        )

    def __len__(self) -> int:
        return len(self._items)

    def append(self, item: str) -> None:
        size = total_size_of(item)
        self._counter += 1
        self._items[self._counter] = (item, size)
        self._size += size

    def extend(self, items: Iterable[str]) -> None:
        for item in items:
            self.append(item)

    def iter_items(self, start: int | None = None) -> Iterator[tuple[int, str]]:
        """
        Yield `(seq_num, string)` for every string in the queue, in order,
        skipping those with `seq_num < start`.
        """
        assert start is None or start >= 0, start
        for seq_num, (item, _size) in self._items.items():
            if start is None or seq_num >= start:
                yield seq_num, item

    def handle_sack(self, sack: SACK) -> bool:
        """
        Remove every string that `sack` acknowledges.

        Returns `True` for a "bad SACK": one that acknowledges a sequence
        number we never assigned.  As many strings as possible are removed
        even then.
        """
        ack_number = sack.ack_number
        assert ack_number >= -1, ack_number

        bad_sack = ack_number > self._counter or any(
            n > self._counter for n in sack.sack_list
        )

        for seq_num in list(self._items):
            if seq_num > ack_number:
                break
            self._remove(seq_num)
        for seq_num in sack.sack_list:
            if seq_num in self._items:
                self._remove(seq_num)

        # Possibly reduce memory use by dropping the old (resized) dict.
        if not self._items:
            self._items = {}

        return bad_sack

    def _remove(self, seq_num: int) -> None:
        _item, size = self._items.pop(seq_num)
        self._size -= size

    def get_max_consumption(self) -> int:
        """
        Return the maximum possible memory consumption of the queued strings.
        """
        return self._size


class Incoming:
    """
    A receive window.  It accepts numbered strings in order (possibly with
    gaps), computes a SACK for them, and returns the strings that are now
    deliverable in order.

    It tracks how much memory the not-yet-deliverable strings use, and can
    refuse strings that would push it over an item-count or memory limit.
    This protects against a peer that never fills the gaps; it is the
    caller's job to act on `hit_limit`.
    """

    def __init__(self) -> None:
        self._last_ack = -1
        # seqNum -> (string, size) for strings received but not yet
        # deliverable, because there is a gap before them.
        self._cached: dict[int, tuple[str, int]] = {}
        self._size = 0

    def give(
        self,
        items: Iterable[tuple[int, str]],
        item_limit: int | None = None,
        size_limit: int | None = None,
    ) -> tuple[list[str], bool]:
        """
        Give new `(seq_num, string)` items, and get the deliverable strings.

        `items` should already be sorted by `seq_num`; unsorted items work,
        but are more likely to hit the limits.

        Returns `(deliverable_strings, hit_limit)`.  Once a limit is hit, the
        rest of `items` is dropped.
        """
        # TODO: maybe immediately reject items that have little chance of
        # delivery (seq_num far above last_ack + item_limit).
        deliverable: list[str] = []
        for seq_num, item in items:
            if seq_num < 0:
                raise ValueError(f"Sequence num must be 0 or above, was {seq_num!r}")

            if seq_num == self._last_ack + 1:
                deliverable.append(item)
                self._last_ack += 1
                while (
                    cached := self._cached.pop(self._last_ack + 1, None)
                ) is not None:
                    cached_item, cached_size = cached
                    deliverable.append(cached_item)
                    self._size -= cached_size
                    self._last_ack += 1
            elif seq_num > self._last_ack and seq_num not in self._cached:
                if item_limit is not None and len(self._cached) >= item_limit:
                    return deliverable, True
                size = total_size_of(item)
                if size_limit is not None and self._size + size > size_limit:
                    return deliverable, True
                self._cached[seq_num] = (item, size)
                self._size += size
            # else: already delivered or cached (a retransmission); ignore it.

        # Possibly reduce memory use by dropping the old (resized) dict.
        if not self._cached:
            self._cached = {}

        return deliverable, False

    def get_sack(self) -> SACK:
        """
        Return a SACK that describes which strings we have received.
        """
        return SACK(self._last_ack, tuple(sorted(self._cached)))

    def get_undeliverable_count(self) -> int:
        return len(self._cached)

    def get_max_consumption(self) -> int:
        """
        Return the maximum possible memory consumption of the undeliverable
        strings.
        """
        return self._size
