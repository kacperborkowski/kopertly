from datetime import date
from decimal import Decimal

from sqlmodel import Field, SQLModel


class ExpenseBase(SQLModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    spent_on: date = Field(index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    shop: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class Expense(ExpenseBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
