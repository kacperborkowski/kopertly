from datetime import date

import pytest

from app.months import month_range, previous_month


@pytest.mark.parametrize(
    ("month", "expected"),
    [
        ("2026-11", (date(2026, 11, 1), date(2026, 12, 1))),
        ("2026-12", (date(2026, 12, 1), date(2027, 1, 1))),
    ],
)
def test_month_range(month: str, expected: tuple[date, date]) -> None:
    assert month_range(month) == expected


@pytest.mark.parametrize(
    ("month", "expected"),
    [("2026-11", "2026-10"), ("2026-10", "2026-09"), ("2027-01", "2026-12")],
)
def test_previous_month(month: str, expected: str) -> None:
    assert previous_month(month) == expected
