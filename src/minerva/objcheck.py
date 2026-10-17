"""
Strict validation for values received over the wire.

This module is private.  If you need similar validation, copy the code and its
tests.

Peers should not get away with sloppy encodings that just happen to work with
today's server, so these are deliberately stricter than `int()`, which happily
accepts `" -0"`, `"1_000"`, `"٣"` (Arabic-Indic three), and so on.
"""

import re

# `[0-9]` rather than `\d`, which also matches non-ASCII digits in str
# patterns.  Use with `fullmatch`; `$` would also match before a trailing "\n".
# Neither pattern accepts "-0" or leading zeros.
_NON_NEG_INT = re.compile(r"0|[1-9][0-9]*")
_INT = re.compile(r"0|-?[1-9][0-9]*")


def str_to_non_neg(value: str) -> int:
    """
    Convert a strictly-formatted decimal string to a non-negative `int`.

    Raises `ValueError` if `value` is not of the form `0` or `[1-9][0-9]*`.
    """
    if not _NON_NEG_INT.fullmatch(value):
        raise ValueError(f"could not decode to non-negative integer: {value!r}")
    return int(value)


def str_to_non_neg_limit(value: str, limit: int) -> int:
    """
    Like `str_to_non_neg`, but also raise `ValueError` if the number is
    greater than `limit`.
    """
    # Reject absurdly long strings before parsing them.
    if len(value) > len(str(limit)):
        raise ValueError(f"{value!r} is too high; limit is {limit}")
    number = str_to_non_neg(value)
    if number > limit:
        raise ValueError(f"{value!r} is too high; limit is {limit}")
    return number


def str_to_int_in_range(value: str, lower: int, upper: int) -> int:
    """
    Convert a strictly-formatted decimal string to an `int` in the inclusive
    range [`lower`, `upper`].  Raises `ValueError` otherwise.
    """
    if not _INT.fullmatch(value):
        raise ValueError(f"value {value!r} does not look numeric")
    number = int(value)
    if not lower <= number <= upper:
        raise ValueError(f"value {value!r} not in range [{lower}, {upper}]")
    return number


def ensure_int(value: int | float) -> int:
    """
    Convert an integral `float` to the equal `int`; pass `int`s through.

    Raises `ValueError` if `value` has a fractional part, and `TypeError` for
    `bool`s (even though `int(True)` works) and non-numbers.
    """
    if isinstance(value, bool):
        raise TypeError("bools are not accepted as integers")
    if not isinstance(value, int | float):
        raise TypeError(f"{value!r} is not an int or float")
    # int() raises OverflowError for infinities and ValueError for NaN.
    try:
        inted = int(value)
    except OverflowError:
        raise ValueError(f"{value!r} cannot be converted to an integer") from None
    if inted != value:
        raise ValueError(f"{value!r} cannot be converted to an identical integer")
    return inted


def ensure_non_neg_int(value: object) -> int:
    """
    Return `value` as an `int` if it is a non-negative integer (or an integral
    `float`, as JSON decoders may produce).

    Raises `TypeError` for non-numbers and `bool`s, and `ValueError` for
    negative or non-integral numbers.
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{value!r} is not an int or float")
    if value < 0:
        raise ValueError(f"{value!r} is < 0")
    return ensure_int(value)


def ensure_non_neg_int_limit(value: object, limit: int) -> int:
    """
    Like `ensure_non_neg_int`, but also raise `ValueError` if the number is
    greater than `limit`.
    """
    number = ensure_non_neg_int(value)
    if number > limit:
        raise ValueError(f"{value!r} is > limit {limit!r}")
    return number


def ensure_bool(value: object) -> bool:
    """
    Convert `1`, `1.0`, and `True` to `True`, and `0`, `0.0`, `-0.0`, and
    `False` to `False`.  Raise `ValueError` for anything else.

    Useful for JSON from a peer that may send `0`/`1` for booleans, when you
    don't want to keep the numbers around.
    """
    # `isinstance` first, so that objects with a weird `__eq__` can't sneak in.
    if isinstance(value, int | float):
        if value == 1:
            return True
        if value == 0:
            return False
    raise ValueError(f"{value!r} is not bool-equivalent to True or False")
