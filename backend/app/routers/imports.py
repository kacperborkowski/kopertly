from decimal import Decimal
from io import BytesIO

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import TypeAdapter, ValidationError
from sqlmodel import select

from app.db import SessionDep
from app.importers.apply import ImportMappingError, apply_import
from app.importers.spreadsheet import (
    MonthlyValue,
    ParsedSpreadsheet,
    SpreadsheetError,
    parse_spreadsheet,
)
from app.models import (
    Category,
    ImportAction,
    ImportPreview,
    ImportResult,
    ImportRowPreview,
    ImportTarget,
)

router = APIRouter(prefix="/imports", tags=["Import"])

MAX_FILE_SIZE = 10 * 1024 * 1024
SKIP_LABELS = {
    "suma",
    "podsumowanie",
    "przychody netto",
    "ile udało się zaoszczędzić",
    "stan rzeczywisty",
}
INCOME_LABELS = {"przychody", "przychód"}

MappingAdapter = TypeAdapter(dict[str, ImportTarget])


def read_upload(file: UploadFile) -> ParsedSpreadsheet:
    content = file.file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, "Plik jest za duży (limit 10 MB)"
        )
    try:
        return parse_spreadsheet(BytesIO(content))
    except SpreadsheetError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error


def group_by_label(values: list[MonthlyValue]) -> dict[str, list[MonthlyValue]]:
    groups: dict[str, list[MonthlyValue]] = {}
    for value in values:
        groups.setdefault(value.label, []).append(value)
    return groups


def _suggest(label: str, categories_by_name: dict[str, Category]) -> ImportTarget:
    normalized = label.lower()
    if normalized in SKIP_LABELS:
        return ImportTarget(action=ImportAction.SKIP)
    if normalized in INCOME_LABELS:
        return ImportTarget(action=ImportAction.INCOME)
    category = categories_by_name.get(normalized)
    if category is not None:
        return ImportTarget(action=ImportAction.CATEGORY, category_id=category.id)
    return ImportTarget(action=ImportAction.CATEGORY, name=label[:50])


@router.post("/spreadsheet/preview", response_model=ImportPreview)
def preview_spreadsheet(file: UploadFile, session: SessionDep) -> ImportPreview:
    parsed = read_upload(file)
    categories_by_name = {
        category.name.lower(): category for category in session.exec(select(Category))
    }
    rows = []
    for label, values in group_by_label(parsed.values).items():
        months = sorted(value.month for value in values)
        rows.append(
            ImportRowPreview(
                label=label,
                cells=len(values),
                negative_cells=sum(1 for value in values if value.amount < 0),
                total=sum((value.amount for value in values), Decimal("0.00")),
                first_month=months[0],
                last_month=months[-1],
                suggestion=_suggest(label, categories_by_name),
            )
        )
    all_months = sorted(value.month for value in parsed.values) or [""]
    return ImportPreview(
        sheets=parsed.sheets,
        first_month=all_months[0],
        last_month=all_months[-1],
        rows=rows,
        warnings=parsed.warnings,
    )


@router.post("/spreadsheet", response_model=ImportResult)
def import_spreadsheet(
    file: UploadFile,
    mapping: Annotated[str, Form(examples=['{"Paliwo": {"action": "category", "name": "Paliwo"}}'])],
    session: SessionDep,
) -> ImportResult:
    try:
        targets = MappingAdapter.validate_json(mapping)
    except ValidationError as error:
        raise RequestValidationError(
            [{**e, "loc": ("body", "mapping", *e["loc"])} for e in error.errors(include_url=False)]
        ) from error
    parsed = read_upload(file)
    try:
        result = apply_import(session, parsed.values, targets)
    except ImportMappingError as error:
        session.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    result.warnings = parsed.warnings + result.warnings
    return result
