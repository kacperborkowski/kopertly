from decimal import Decimal
from enum import StrEnum

from sqlmodel import SQLModel


class ImportAction(StrEnum):
    CATEGORY = "category"
    INCOME = "income"
    SKIP = "skip"


class ImportTarget(SQLModel):
    action: ImportAction
    category_id: int | None = None
    name: str | None = None


class ImportRowPreview(SQLModel):
    label: str
    cells: int
    negative_cells: int
    total: Decimal
    first_month: str
    last_month: str
    suggestion: ImportTarget


class ImportPreview(SQLModel):
    sheets: list[str]
    first_month: str
    last_month: str
    rows: list[ImportRowPreview]
    warnings: list[str]
