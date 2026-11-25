from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select

from app.db import SessionDep
from app.models import Category, Expense, ExpenseCreate, ExpensePublic

router = APIRouter(prefix="/expenses", tags=["Wydatki"])

MonthParam = Annotated[
    str | None,
    Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2026-11"]),
]


def _month_range(month: str) -> tuple[date, date]:
    year, month_number = map(int, month.split("-"))
    start = date(year, month_number, 1)
    if month_number == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month_number + 1, 1)
    return start, end


@router.post("", response_model=ExpensePublic, status_code=status.HTTP_201_CREATED)
def create_expense(data: ExpenseCreate, session: SessionDep) -> Expense:
    if session.get(Category, data.category_id) is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Nie ma kategorii o id {data.category_id}",
        )
    expense = Expense.model_validate(data)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@router.get("", response_model=list[ExpensePublic])
def list_expenses(
    session: SessionDep,
    month: MonthParam = None,
    category_id: int | None = None,
) -> list[Expense]:
    query = select(Expense)
    if month is not None:
        start, end = _month_range(month)
        query = query.where(Expense.spent_on >= start, Expense.spent_on < end)
    if category_id is not None:
        query = query.where(Expense.category_id == category_id)
    query = query.order_by(col(Expense.spent_on).desc(), col(Expense.id).desc())
    return list(session.exec(query).all())
