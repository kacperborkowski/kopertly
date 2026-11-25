from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import Session, col, select

from app.db import SessionDep
from app.models import (
    MONTH_PATTERN,
    Category,
    Expense,
    ExpenseCreate,
    ExpensePublic,
    ExpenseUpdate,
)
from app.months import month_range

router = APIRouter(prefix="/expenses", tags=["Wydatki"])

MonthParam = Annotated[
    str | None,
    Query(pattern=MONTH_PATTERN, examples=["2026-11"]),
]


REQUIRED_FIELDS = ("amount", "spent_on", "category_id")


def _get_or_404(session: Session, expense_id: int) -> Expense:
    expense = session.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nie ma takiego wydatku")
    return expense


def _ensure_category_exists(session: Session, category_id: int) -> None:
    if session.get(Category, category_id) is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Nie ma kategorii o id {category_id}",
        )


@router.post("", response_model=ExpensePublic, status_code=status.HTTP_201_CREATED)
def create_expense(data: ExpenseCreate, session: SessionDep) -> Expense:
    _ensure_category_exists(session, data.category_id)
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
        start, end = month_range(month)
        query = query.where(Expense.spent_on >= start, Expense.spent_on < end)
    if category_id is not None:
        query = query.where(Expense.category_id == category_id)
    query = query.order_by(col(Expense.spent_on).desc(), col(Expense.id).desc())
    return list(session.exec(query).all())


@router.get("/{expense_id}", response_model=ExpensePublic)
def get_expense(expense_id: int, session: SessionDep) -> Expense:
    return _get_or_404(session, expense_id)


@router.patch("/{expense_id}", response_model=ExpensePublic)
def update_expense(expense_id: int, data: ExpenseUpdate, session: SessionDep) -> Expense:
    expense = _get_or_404(session, expense_id)
    changes = {
        field: value
        for field, value in data.model_dump(exclude_unset=True).items()
        if value is not None or field not in REQUIRED_FIELDS
    }
    if "category_id" in changes:
        _ensure_category_exists(session, changes["category_id"])
    expense.sqlmodel_update(changes)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, session: SessionDep) -> None:
    expense = _get_or_404(session, expense_id)
    session.delete(expense)
    session.commit()
