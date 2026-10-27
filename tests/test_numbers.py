from __future__ import annotations

import pytest

from claimcheck.numbers import parse_stated_number


@pytest.mark.parametrize(
    ("text", "value", "precision"),
    [
        ("$1.4 billion", 1.4e9, 0.05e9),
        ("$1.4B", 1.4e9, 0.05e9),
        ("1.4bn", 1.4e9, 0.05e9),
        ("$700 million", 700e6, 0.5e6),
        ("$48.385B", 48.385e9, 0.0005e9),
        ("$62,360 million", 62_360e6, 0.5e6),
        ("22%", 22.0, 0.5),
        ("22.5 percent", 22.5, 0.05),
        ("$1.05", 1.05, 0.005),
        ("$1 trillion", 1e12, 0.5e12),
        ("1.2T", 1.2e12, 0.05e12),
        ("500 thousand", 500e3, 0.5e3),
        ("2.5k", 2.5e3, 0.05e3),
        ("$1.05M", 1.05e6, 0.005e6),
        ("loss of $2B", 2e9, 0.5e9),
        ("up 22%", 22.0, 0.5),
        ("about 48.385B", 48.385e9, 0.0005e9),
        ("1.00", 1.0, 0.005),
        ("0.5%", 0.5, 0.05),
        ("10 million", 10e6, 0.5e6),
        ("3,200", 3200.0, 0.5),
        ("0.25", 0.25, 0.005),
        ("- $2B", 2e9, 0.5e9),
    ],
)
def test_parse_stated_number(text: str, value: float, precision: float) -> None:
    parsed = parse_stated_number(text)
    assert parsed is not None
    assert parsed.value == pytest.approx(value)
    assert parsed.precision == pytest.approx(precision)


@pytest.mark.parametrize("text", ["no number", "", "percent", "N/A"])
def test_unparsable_number_returns_none(text: str) -> None:
    assert parse_stated_number(text) is None
