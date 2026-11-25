import re
import zipfile
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import BinaryIO

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

MONTH_NAMES = {
    "styczeń": 1,
    "luty": 2,
    "marzec": 3,
    "kwiecień": 4,
    "maj": 5,
    "czerwiec": 6,
    "lipiec": 7,
    "sierpień": 8,
    "wrzesień": 9,
    "październik": 10,
    "listopad": 11,
    "grudzień": 12,
}

YEAR_SHEET = re.compile(r"^\d{4}$")
CENT = Decimal("0.01")


class SpreadsheetError(ValueError):
    pass


@dataclass(frozen=True)
class MonthlyValue:
    label: str
    month: str
    amount: Decimal


@dataclass
class ParsedSpreadsheet:
    sheets: list[str] = field(default_factory=list)
    values: list[MonthlyValue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_spreadsheet(source: BinaryIO) -> ParsedSpreadsheet:
    try:
        workbook = load_workbook(source, data_only=True, read_only=True)
    except (InvalidFileException, zipfile.BadZipFile, KeyError, OSError) as error:
        raise SpreadsheetError("Nie udało się odczytać pliku .xlsx") from error

    result = ParsedSpreadsheet()
    for sheet in workbook.worksheets:
        year = sheet.title.strip()
        if not YEAR_SHEET.match(year):
            continue
        _parse_year_sheet(year, list(sheet.iter_rows(values_only=True)), result)
    workbook.close()

    if not result.sheets:
        raise SpreadsheetError(
            "Nie znaleziono arkuszy lat (arkusz powinien nazywać się np. „2025”)"
        )
    return result


def _parse_year_sheet(year: str, rows: list[tuple], result: ParsedSpreadsheet) -> None:
    header_index, month_columns = _find_month_header(rows)
    if header_index is None:
        result.warnings.append(f"Arkusz {year}: brak wiersza z nazwami miesięcy, pominięty")
        return
    result.sheets.append(year)

    for row_index in range(header_index + 1, len(rows)):
        row = rows[row_index]
        label = _clean_label(row[0] if row else None)
        cells = [
            (month, _blank_to_none(row[column] if column < len(row) else None))
            for column, month in month_columns.items()
        ]
        if label is None:
            if any(value is not None for _, value in cells):
                result.warnings.append(
                    f"Arkusz {year}, wiersz {row_index + 1}: liczby bez nazwy, pominięte"
                )
            continue
        for month, value in cells:
            amount = _to_amount(value)
            if amount is None:
                if value is not None:
                    result.warnings.append(
                        f"Arkusz {year}, „{label}”, miesiąc {month}: "
                        f"wartość „{value}” to nie liczba, pominięta"
                    )
                continue
            if amount == 0:
                continue
            result.values.append(
                MonthlyValue(label=label, month=f"{year}-{month:02d}", amount=amount)
            )


def _find_month_header(rows: list[tuple]) -> tuple[int | None, dict[int, int]]:
    for index, row in enumerate(rows):
        month_columns = {
            column: MONTH_NAMES[name]
            for column, cell in enumerate(row)
            if isinstance(cell, str) and (name := cell.strip().lower()) in MONTH_NAMES
        }
        if month_columns:
            return index, month_columns
    return None, {}


def _blank_to_none(value: object) -> object:
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _clean_label(value: object) -> str | None:
    if value is None:
        return None
    label = " ".join(str(value).split())
    return label or None


def _to_amount(value: object) -> Decimal | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float | Decimal):
        return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    return None
