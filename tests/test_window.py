import pytest
from hypothesis import given
from hypothesis import strategies as st

from minerva.window import SACK, Incoming, Queue, total_size_of


class TestQueue:
    def test_repr(self) -> None:
        q = Queue()
        assert repr(q) == f"<Queue at {id(q):#x} with 0 item(s), counter=#-1, size=0>"

        q.extend(["a", "b"])
        size = total_size_of("a") * 2
        assert (
            repr(q) == f"<Queue at {id(q):#x} with 2 item(s), counter=#1, size={size}>"
        )

        q.handle_sack(SACK(0, ()))
        size = total_size_of("a")
        assert (
            repr(q) == f"<Queue at {id(q):#x} with 1 item(s), counter=#1, size={size}>"
        )

    def test_max_consumption(self) -> None:
        """
        The size of the Queue increases when we extend or append to it, and
        decreases when a SACK removes items.
        """
        q = Queue()
        assert q.get_max_consumption() == 0
        q.extend(["a", "b"])
        assert q.get_max_consumption() == total_size_of("a") * 2
        q.handle_sack(SACK(0, ()))
        assert q.get_max_consumption() == total_size_of("a")
        # A strange-looking SACK, but it exercises the sack_list code.
        q.handle_sack(SACK(0, (1,)))
        assert q.get_max_consumption() == 0
        q.handle_sack(SACK(1, ()))
        assert q.get_max_consumption() == 0
        q.append("cc")
        assert q.get_max_consumption() == total_size_of("cc")

    def test_iter_empty_queue(self) -> None:
        assert list(Queue().iter_items(start=0)) == []

    @pytest.mark.parametrize(
        ("start", "expected"),
        [
            (None, [(0, "zero"), (1, "one"), (2, "two")]),
            (0, [(0, "zero"), (1, "one"), (2, "two")]),
            (1, [(1, "one"), (2, "two")]),
            (3, []),
        ],
    )
    def test_iter_items(
        self, start: int | None, expected: list[tuple[int, str]]
    ) -> None:
        q = Queue()
        q.append("zero")
        q.extend(["one", "two"])
        assert list(q.iter_items(start=start)) == expected
        # iter_items is idempotent
        assert list(q.iter_items(start=start)) == expected

    def test_sack_only_ack_number(self) -> None:
        q = Queue()
        q.extend(["zero", "one", "two"])
        assert q.handle_sack(SACK(0, ())) is False
        assert list(q.iter_items()) == [(1, "one"), (2, "two")]
        # Removing again is idempotent
        assert q.handle_sack(SACK(0, ())) is False
        assert list(q.iter_items()) == [(1, "one"), (2, "two")]

    def test_ack_number_too_high_on_empty_queue(self) -> None:
        assert Queue().handle_sack(SACK(0, ())) is True

    def test_ack_number_too_high(self) -> None:
        q = Queue()
        q.append("zero")
        assert q.handle_sack(SACK(1, ())) is True
        # Items were still removed, despite it being a bad SACK
        assert list(q.iter_items()) == []

    def test_sack_number_too_high(self) -> None:
        q = Queue()
        q.extend(["zero", "one", "two", "three"])
        assert q.handle_sack(SACK(0, (2, 5))) is True
        # Items were still removed, despite it being a bad SACK
        assert list(q.iter_items()) == [(1, "one"), (3, "three")]

    def test_sack_to_higher_num(self) -> None:
        q = Queue()
        q.extend(str(n) for n in range(11))
        assert q.handle_sack(SACK(1, ())) is False
        assert q.handle_sack(SACK(3, ())) is False
        assert list(q.iter_items(start=4)) == [(n, str(n)) for n in range(4, 11)]

    def test_noop_sack(self) -> None:
        q = Queue()
        q.extend(["zero", "one", "two"])
        assert q.handle_sack(SACK(-1, ())) is False
        assert list(q.iter_items()) == [(0, "zero"), (1, "one"), (2, "two")]

    def test_sack_removes_selectively(self) -> None:
        q = Queue()
        q.extend(["zero", "one", "two", "three"])
        assert q.handle_sack(SACK(-1, (1,))) is False
        assert list(q.iter_items()) == [(0, "zero"), (2, "two"), (3, "three")]
        assert q.handle_sack(SACK(0, (3,))) is False
        assert list(q.iter_items()) == [(2, "two")]
        q.append("four")
        assert list(q.iter_items()) == [(2, "two"), (4, "four")]
        # A very strange SACK (it should have been SACK(4, ())), but legal.
        assert q.handle_sack(SACK(0, (2, 4))) is False
        assert list(q.iter_items()) == []
        q.append("five")
        assert list(q.iter_items()) == [(5, "five")]

    def test_ack_and_sack_numbers_both_remove(self) -> None:
        """
        Covers a wrong-variable-in-loop bug we once had.
        """
        q = Queue()
        q.extend(["zero", "one", "two", "three", "four"])
        assert q.handle_sack(SACK(0, (1, 3))) is False
        assert list(q.iter_items()) == [(2, "two"), (4, "four")]

    @given(
        n=st.integers(min_value=0, max_value=50),
        ack_number=st.integers(min_value=-1, max_value=60),
        sack_list=st.lists(st.integers(min_value=0, max_value=60), unique=True).map(
            lambda xs: tuple(sorted(xs))
        ),
    )
    def test_sack_property(
        self, n: int, ack_number: int, sack_list: tuple[int, ...]
    ) -> None:
        q = Queue()
        q.extend(f"s{i}" for i in range(n))
        bad = q.handle_sack(SACK(ack_number, sack_list))

        expected = [
            (i, f"s{i}") for i in range(n) if i > ack_number and i not in sack_list
        ]
        assert list(q.iter_items()) == expected
        assert len(q) == len(expected)
        assert q.get_max_consumption() == sum(total_size_of(s) for _, s in expected)
        assert bad == (ack_number >= n or any(s >= n for s in sack_list))


class TestIncoming:
    def test_sack_no_items(self) -> None:
        assert Incoming().get_sack() == SACK(-1, ())

    def test_three_items(self) -> None:
        i = Incoming()
        assert i.give([(0, "string0"), (1, "string1"), (2, "string2")]) == (
            ["string0", "string1", "string2"],
            False,
        )
        assert i.get_sack() == SACK(2, ())

    @pytest.mark.parametrize(
        ("given_nums", "expected_sack"),
        [
            ([0, 1, 3], SACK(1, (3,))),
            ([0, 1, 4], SACK(1, (4,))),
            ([0, 1, 4, 6], SACK(1, (4, 6))),
            # The sack_list is sorted numerically, not as strings.
            ([0, 1, 4, 10], SACK(1, (4, 10))),
        ],
    )
    def test_items_missing(self, given_nums: list[int], expected_sack: SACK) -> None:
        i = Incoming()
        assert i.give([(n, f"string{n}") for n in given_nums]) == (
            ["string0", "string1"],
            False,
        )
        assert i.get_sack() == expected_sack

    def test_two_ranges_missing_then_fill(self) -> None:
        i = Incoming()
        i.give([(0, "string0"), (1, "string1"), (4, "string4"), (6, "string6")])
        assert i.get_sack() == SACK(1, (4, 6))
        assert i.give([(2, "string2"), (3, "string3"), (5, "string5")]) == (
            ["string2", "string3", "string4", "string5", "string6"],
            False,
        )
        assert i.get_sack() == SACK(6, ())

    def test_out_of_order(self) -> None:
        i = Incoming()
        # string0 missing
        assert i.give([(1, "string1"), (2, "string2")]) == ([], False)
        assert i.get_sack() == SACK(-1, (1, 2))
        # finally deliver it
        assert i.give([(0, "string0")]) == (["string0", "string1", "string2"], False)
        # make sure it still works
        assert i.give([(3, "string3")]) == (["string3"], False)
        assert i.get_sack() == SACK(3, ())

    def test_out_of_order_in_one_call(self) -> None:
        """
        Unsorted items in one `give` call work too (but in production they
        are more likely to hit the limits).
        """
        i = Incoming()
        assert i.give([(1, "string1"), (0, "string0")]) == (
            ["string0", "string1"],
            False,
        )
        assert i.get_sack() == SACK(1, ())

    @pytest.mark.parametrize("seq_num", [-1, -2])
    def test_negative_sequence_num(self, seq_num: int) -> None:
        with pytest.raises(ValueError):
            Incoming().give([(seq_num, "string")])

    def test_undeliverable_count(self) -> None:
        i = Incoming()
        assert i.get_undeliverable_count() == 0
        i.give([(1, "string1")])
        assert i.get_undeliverable_count() == 1
        i.give([(2, "string2")])
        assert i.get_undeliverable_count() == 2
        i.give([(0, "string0")])
        assert i.get_undeliverable_count() == 0

    def test_items_given_twice(self) -> None:
        """
        An already-delivered item is ignored, and does not take up space.
        """
        i = Incoming()
        i.give([(0, "string0"), (1, "string1")])
        for again in ([0], [1], [0, 1], [0, 1, 2]):
            i.give([(n, f"string{n}") for n in again])
            assert i.get_undeliverable_count() == 0

    def test_item_limit(self) -> None:
        i = Incoming()
        for n in (1, 2, 3):
            assert i.give([(n, f"string{n}")], item_limit=3) == ([], False)
        for n in (4, 5):
            assert i.give([(n, f"string{n}")], item_limit=3) == ([], True)

        # The items we kept giving it past the limit were dropped.
        assert i.give([(0, "string0")], item_limit=3) == (
            ["string0", "string1", "string2", "string3"],
            False,
        )
        assert i.get_undeliverable_count() == 0
        assert i.get_max_consumption() == 0

    def test_size_limit(self) -> None:
        size_limit = total_size_of("string1") * 3
        i = Incoming()
        for n in (1, 2, 3):
            assert i.give([(n, f"string{n}")], size_limit=size_limit) == ([], False)
        for n in (4, 5):
            assert i.give([(n, f"string{n}")], size_limit=size_limit) == ([], True)

        # The items we kept giving it past the limit were dropped.
        assert i.give([(0, "string0")], size_limit=size_limit) == (
            ["string0", "string1", "string2", "string3"],
            False,
        )
        assert i.get_undeliverable_count() == 0
        assert i.get_max_consumption() == 0

    def test_max_consumption(self) -> None:
        i = Incoming()
        assert i.get_max_consumption() == 0
        i.give([(1, "string1"), (2, "string2"), (3, "string3")])
        assert i.get_max_consumption() == total_size_of("string1") * 3
        i.give([(4, "string4"), (5, "string5"), (6, "string6")])
        assert i.get_max_consumption() == total_size_of("string1") * 6

    @given(st.permutations(range(30)), st.integers(min_value=1, max_value=30))
    def test_any_order_delivers_everything_in_order(
        self, order: list[int], chunk_size: int
    ) -> None:
        i = Incoming()
        delivered: list[str] = []
        for at in range(0, len(order), chunk_size):
            chunk = order[at : at + chunk_size]
            strings, hit_limit = i.give([(n, f"s{n}") for n in chunk])
            assert not hit_limit
            delivered.extend(strings)
        assert delivered == [f"s{n}" for n in range(30)]
        assert i.get_sack() == SACK(29, ())
        assert i.get_max_consumption() == 0

    @given(st.sets(st.integers(min_value=0, max_value=40)))
    def test_sack_describes_received_set(self, received: set[int]) -> None:
        i = Incoming()
        i.give((n, "x") for n in sorted(received))
        ack_number = -1
        while ack_number + 1 in received:
            ack_number += 1
        assert i.get_sack() == SACK(
            ack_number, tuple(sorted(n for n in received if n > ack_number))
        )


@given(
    strings=st.lists(
        st.text(alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E))
    ),
    data=st.data(),
)
def test_queue_and_incoming_over_a_lossy_channel(
    strings: list[str], data: st.DataObject
) -> None:
    """
    However the channel drops, duplicates, and reorders strings, retransmitting
    whatever is un-SACKed eventually delivers everything exactly once, in order.
    """
    sender = Queue()
    sender.extend(strings)
    receiver = Incoming()
    delivered: list[str] = []

    while len(sender):
        in_flight = list(sender.iter_items())
        # Lose some (but, to guarantee progress, never all) and duplicate some.
        survivors = data.draw(st.lists(st.sampled_from(in_flight), min_size=1))
        received, hit_limit = receiver.give(survivors)
        assert not hit_limit
        delivered.extend(received)
        assert sender.handle_sack(receiver.get_sack()) is False

    assert delivered == strings
