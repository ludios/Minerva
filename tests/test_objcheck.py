import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from minerva.objcheck import (
    ensure_bool,
    ensure_int,
    ensure_non_neg_int,
    ensure_non_neg_int_limit,
    str_to_int_in_range,
    str_to_non_neg,
    str_to_non_neg_limit,
)

# Strings that `int()` accepts but a strict parser must not.
SLOPPY_NUMBERS = [
    "",
    "07",
    "08",
    "007",
    "-0",
    "+7",
    " 7",
    "7 ",
    "7\n",  # `$` in a regex would accept this one
    "1_000",
    "\N{ARABIC-INDIC DIGIT THREE}",  # `\d` in a str regex would accept this one
    "7e4",
    "7.0",
    "7.",
    "0.0",
    "7f",
    "0x7",
]


class TestStrToNonNeg:
    @pytest.mark.parametrize(("s", "expected"), [("0", 0), ("3", 3), ("12390", 12390)])
    def test_okay(self, s: str, expected: int) -> None:
        assert str_to_non_neg(s) == expected

    @pytest.mark.parametrize("s", [*SLOPPY_NUMBERS, "-7"])
    def test_rejects(self, s: str) -> None:
        with pytest.raises(ValueError):
            str_to_non_neg(s)

    @pytest.mark.parametrize("bad", [None, [], {}, b"1"])
    def test_type_errors(self, bad: object) -> None:
        with pytest.raises(TypeError):
            str_to_non_neg(bad)  # ty: ignore[invalid-argument-type]

    @given(st.integers(min_value=0))
    def test_roundtrip(self, n: int) -> None:
        assert str_to_non_neg(str(n)) == n

    @given(st.text())
    def test_only_canonical_strings_accepted(self, s: str) -> None:
        """
        Any string that is accepted is the canonical decimal form of the result.
        """
        try:
            n = str_to_non_neg(s)
        except ValueError:
            return
        assert str(n) == s


class TestStrToNonNegLimit:
    @pytest.mark.parametrize(
        ("s", "limit"),
        [
            ("0", 0),
            ("1", 1),
            ("9", 9),
            ("9", 10),
            *((str(2**e), 2**e) for e in (32, 53, 65)),
        ],
    )
    def test_within_limit(self, s: str, limit: int) -> None:
        assert str_to_non_neg_limit(s, limit) == int(s)

    @pytest.mark.parametrize(
        ("s", "limit"),
        [
            ("1", 0),
            ("9", 8),
            ("999999999999999999999", 8),
            (str(2**31), 2**31 - 1),
            (str(2**53 + 1), 2**53),
            (str(2**65 + 1), 2**65),
        ],
    )
    def test_outside_limit(self, s: str, limit: int) -> None:
        with pytest.raises(ValueError):
            str_to_non_neg_limit(s, limit)

    @pytest.mark.parametrize("s", SLOPPY_NUMBERS)
    def test_rejects_sloppy(self, s: str) -> None:
        with pytest.raises(ValueError):
            str_to_non_neg_limit(s, 2**128)

    @given(
        st.integers(min_value=0, max_value=2**70),
        st.integers(min_value=0, max_value=2**70),
    )
    def test_agrees_with_unlimited(self, n: int, limit: int) -> None:
        if n <= limit:
            assert str_to_non_neg_limit(str(n), limit) == n
        else:
            with pytest.raises(ValueError):
                str_to_non_neg_limit(str(n), limit)


class TestStrToIntInRange:
    @pytest.mark.parametrize(
        ("s", "lower", "upper", "expected"),
        [("3", 3, 3, 3), ("3", -3, 3, 3), ("-3", -3, 3, -3), ("0", 0, 0, 0)],
    )
    def test_within_range(self, s: str, lower: int, upper: int, expected: int) -> None:
        assert str_to_int_in_range(s, lower, upper) == expected

    @pytest.mark.parametrize("s", ["-4", "4"])
    def test_outside_range(self, s: str) -> None:
        with pytest.raises(ValueError):
            str_to_int_in_range(s, -3, 3)

    @pytest.mark.parametrize(
        "s", ["1.", "1.0", "1.5", "-0", "", "x", "-", "-01", "1\n"]
    )
    def test_bad_numbers(self, s: str) -> None:
        with pytest.raises(ValueError):
            str_to_int_in_range(s, -3, 3)

    @given(st.integers(), st.text())
    def test_only_canonical_strings_accepted(self, bound: int, s: str) -> None:
        try:
            n = str_to_int_in_range(s, -abs(bound), abs(bound))
        except ValueError:
            return
        assert str(n) == s
        assert abs(n) <= abs(bound)


class TestEnsureInt:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(0, 0), (-1, -1), (-1.0, -1), (-0.0, 0), (2.0, 2), (2 * 10**26, 2 * 10**26)],
    )
    def test_ensure_int(self, value: float, expected: int) -> None:
        result = ensure_int(value)
        assert result == expected
        assert type(result) is int

    @pytest.mark.parametrize("value", [0.5, -1.5, math.nan, math.inf, -math.inf])
    def test_value_errors(self, value: float) -> None:
        with pytest.raises(ValueError):
            ensure_int(value)

    @pytest.mark.parametrize("value", ["0", "-0", {}, [], True, False, None])
    def test_type_errors(self, value: object) -> None:
        with pytest.raises(TypeError):
            ensure_int(value)  # ty: ignore[invalid-argument-type]


class TestEnsureNonNegInt:
    @pytest.mark.parametrize(
        ("value", "expected"), [(0, 0), (-0, 0), (-0.0, 0), (2.0, 2)]
    )
    def test_ensure_non_neg_int(self, value: float, expected: int) -> None:
        result = ensure_non_neg_int(value)
        assert result == expected
        assert type(result) is int

    @pytest.mark.parametrize("value", [0.001, -1, -1.0, -2.0, -(10**29), math.inf])
    def test_value_errors(self, value: float) -> None:
        with pytest.raises(ValueError):
            ensure_non_neg_int(value)

    @pytest.mark.parametrize("value", ["0", "-0", "0.001", True, False, {}, [], None])
    def test_type_errors(self, value: object) -> None:
        with pytest.raises(TypeError):
            ensure_non_neg_int(value)


class TestEnsureNonNegIntLimit:
    def test_edge(self) -> None:
        assert ensure_non_neg_int_limit(2**31 - 1, 2**31 - 1) == 2**31 - 1

    @pytest.mark.parametrize("value", [2**31, 2**32])
    def test_too_high(self, value: int) -> None:
        with pytest.raises(ValueError):
            ensure_non_neg_int_limit(value, 2**31 - 1)

    @given(st.one_of(st.integers(), st.floats(), st.booleans(), st.none(), st.text()))
    def test_only_raises_type_or_value_error(self, value: object) -> None:
        """
        The hello-frame parser relies on this: anything else would escape it.
        """
        try:
            result = ensure_non_neg_int_limit(value, 2**53)
        except TypeError, ValueError:
            return
        assert type(result) is int
        assert 0 <= result <= 2**53


class TestEnsureBool:
    @pytest.mark.parametrize("value", [1, 1.0, True])
    def test_true(self, value: object) -> None:
        assert ensure_bool(value) is True

    @pytest.mark.parametrize("value", [0, 0.0, -0.0, False])
    def test_false(self, value: object) -> None:
        assert ensure_bool(value) is False

    @pytest.mark.parametrize(
        "value",
        [-0.5, -1.00001, 1.0001, 2, [], {}, set(), "1", None, math.nan, math.inf],
    )
    def test_value_error(self, value: object) -> None:
        with pytest.raises(ValueError):
            ensure_bool(value)
