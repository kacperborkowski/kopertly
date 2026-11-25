from decimal import Decimal
from typing import Annotated

from pydantic import StringConstraints
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

Month = Annotated[str, StringConstraints(pattern=MONTH_PATTERN)]


class MonthlyBudgetBase(SQLModel):
    month: Month = Field(unique=True, index=True)
    income: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)


class MonthlyBudget(MonthlyBudgetBase, table=True):
    __tablename__ = "monthly_budget"

    id: int | None = Field(default=None, primary_key=True)


class BudgetAllocationBase(SQLModel):
    category_id: int = Field(foreign_key="category.id", ondelete="CASCADE", index=True)
    amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class BudgetAllocation(BudgetAllocationBase, table=True):
    __tablename__ = "budget_allocation"
    __table_args__ = (UniqueConstraint("budget_id", "category_id"),)

    id: int | None = Field(default=None, primary_key=True)
    budget_id: int = Field(foreign_key="monthly_budget.id", ondelete="CASCADE", index=True)


class BudgetUpsert(SQLModel):
    income: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    allocations: list[BudgetAllocationBase] = []


class BudgetPublic(SQLModel):
    month: str
    income: Decimal
    allocations: list[BudgetAllocationBase]


class CategorySummary(SQLModel):
    category_id: int
    name: str
    color: str
    planned: Decimal
    spent: Decimal
    remaining: Decimal


class BudgetSummary(SQLModel):
    month: str
    has_budget: bool
    income: Decimal
    planned_total: Decimal
    spent_total: Decimal
    remaining_total: Decimal
    unallocated: Decimal
    categories: list[CategorySummary]
