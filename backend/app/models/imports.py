from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import model_validator
from sqlmodel import SQLModel

from app.models.category import CategoryName


class ImportAction(StrEnum):
    CATEGORY = "category"
    INCOME = "income"
    SKIP = "skip"


class ImportTarget(SQLModel):
    action: ImportAction
    category_id: int | None = None
    name: CategoryName | None = None

    @model_validator(mode="after")
    def check_category_reference(self) -> Self:
        has_id = self.category_id is not None
        has_name = self.name is not None
        if self.action == ImportAction.CATEGORY and has_id == has_name:
            raise ValueError("Dla kategorii podaj dokładnie jedno: category_id albo name")
        if self.action != ImportAction.CATEGORY and (has_id or has_name):
            raise ValueError("category_id i name podaje się tylko dla action=category")
        return self


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


class ImportResult(SQLModel):
    categories_created: list[str]
    expenses_created: int
    expenses_already_imported: int
    budgets_with_income: int
    skipped_labels: list[str]
    warnings: list[str]
