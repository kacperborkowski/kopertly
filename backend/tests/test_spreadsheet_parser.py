from decimal import Decimal
from io import BytesIO

import pytest

from app.importers.spreadsheet import MonthlyValue, SpreadsheetError, parse_spreadsheet
from tests.spreadsheets import MONTHS
from tests.spreadsheets import make_xlsx as _xlsx


def test_parses_month_values_per_label() -> None:
    source = _xlsx(
        {
            "2025": [
                [None, *MONTHS, None],
                ["Przychody", 1000, 1100.5, *[None] * 10, 2100.5],
                ["Spożywcze"],
                ["Jedzenie do domu", 1897.76, None, 12.345],
            ]
        }
    )

    result = parse_spreadsheet(source)

    assert result.sheets == ["2025"]
    assert result.values == [
        MonthlyValue("Przychody", "2025-01", Decimal("1000.00")),
        MonthlyValue("Przychody", "2025-02", Decimal("1100.50")),
        MonthlyValue("Jedzenie do domu", "2025-01", Decimal("1897.76")),
        MonthlyValue("Jedzenie do domu", "2025-03", Decimal("12.35")),
    ]
    assert result.warnings == []


def test_ignores_non_year_sheets_and_reads_all_years() -> None:
    source = _xlsx(
        {
            "Planowanie": [["Przychód", 5000]],
            "2024": [[None, *MONTHS], ["Paliwo", 100]],
            "2025": [[None, *MONTHS], ["Paliwo", None, 200]],
        }
    )

    result = parse_spreadsheet(source)

    assert result.sheets == ["2024", "2025"]
    assert [(v.month, v.amount) for v in result.values] == [
        ("2024-01", Decimal("100.00")),
        ("2025-02", Decimal("200.00")),
    ]


def test_skips_zero_and_keeps_negative_values() -> None:
    source = _xlsx({"2025": [[None, *MONTHS], ["Suma", 0, -851.76]]})

    result = parse_spreadsheet(source)

    assert result.values == [MonthlyValue("Suma", "2025-02", Decimal("-851.76"))]


def test_normalizes_label_whitespace() -> None:
    source = _xlsx({"2025": [[None, *MONTHS], ["  Koty   :) ", 50]]})

    assert parse_spreadsheet(source).values[0].label == "Koty :)"


def test_warns_about_values_without_label() -> None:
    source = _xlsx({"2025": [[None, *MONTHS], [None, None, None, 2000]]})

    result = parse_spreadsheet(source)

    assert result.values == []
    assert result.warnings == ["Arkusz 2025, wiersz 2: liczby bez nazwy, pominięte"]


def test_warns_about_text_values() -> None:
    source = _xlsx({"2025": [[None, *MONTHS], ["Paliwo", "dużo", 100]]})

    result = parse_spreadsheet(source)

    assert len(result.values) == 1
    assert "„dużo”" in result.warnings[0]


def test_warns_about_year_sheet_without_month_header() -> None:
    source = _xlsx(
        {
            "2024": [["Coś zupełnie innego"]],
            "2025": [[None, *MONTHS], ["Paliwo", 100]],
        }
    )

    result = parse_spreadsheet(source)

    assert result.sheets == ["2025"]
    assert "2024" in result.warnings[0]


def test_rejects_workbook_without_year_sheets() -> None:
    with pytest.raises(SpreadsheetError):
        parse_spreadsheet(_xlsx({"Arkusz1": [["a", 1]]}))


def test_rejects_file_that_is_not_xlsx() -> None:
    with pytest.raises(SpreadsheetError):
        parse_spreadsheet(BytesIO(b"Data;Kwota\n2025-01-01;10"))


def test_treats_whitespace_only_cells_as_empty() -> None:
    source = _xlsx({"2025": [[None, *MONTHS], ["Lekarz", "   ", 100], [None, "  "]]})

    result = parse_spreadsheet(source)

    assert [v.month for v in result.values] == ["2025-02"]
    assert result.warnings == []


def test_repeated_label_in_sheet_gets_section_prefix() -> None:
    source = _xlsx(
        {
            "2020": [
                [None, *MONTHS],
                ["Rachunki (mieszkanie)"],
                ["Inne", 100],
                ["Dom"],
                ["Chemia", 30],
                ["Inne", 50],
            ],
            "2019": [
                [None, *MONTHS],
                ["Rachunki (mieszkanie)"],
                ["Inne", 90],
            ],
            "2021": [
                [None, *MONTHS],
                ["Rachunki"],
                ["Czynsz", 10],
            ],
        }
    )

    result = parse_spreadsheet(source)

    assert [(v.label, v.month) for v in result.values] == [
        ("Rachunki (mieszkanie) / Inne", "2020-01"),
        ("Chemia", "2020-01"),
        ("Dom / Inne", "2020-01"),
        ("Rachunki (mieszkanie) / Inne", "2019-01"),
        ("Czynsz", "2021-01"),
    ]


def test_rows_without_values_are_section_headers() -> None:
    source = _xlsx({"2025": [[None, *MONTHS], ["Spożywcze"], ["Jedzenie", 10]]})

    assert [v.label for v in parse_spreadsheet(source).values] == ["Jedzenie"]
