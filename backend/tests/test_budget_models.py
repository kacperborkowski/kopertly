from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import (
    BudgetAllocation,
    Category,
    MonthlyBudget,
    MonthlyBudgetBase,
)


@pytest.fixture
def budget(session: Session) -> MonthlyBudget:
    budget = MonthlyBudget(month="2026-11", income=Decimal("5000"))
    session.add(budget)
    session.commit()
    return budget


@pytest.fixture
def category(session: Session) -> Category:
    category = Category(name="Jedzenie")
    session.add(category)
    session.commit()
    return category


@pytest.mark.parametrize(
    "data",
    [
        {"month": "2026-13"},
        {"month": "listopad"},
        {"month": "2026-11", "income": "-1"},
        {"month": "2026-11", "income": "1.005"},
    ],
)
def test_monthly_budget_rejects_invalid_data(data: dict) -> None:
    with pytest.raises(ValidationError):
        MonthlyBudgetBase.model_validate(data)


def test_monthly_budget_income_defaults_to_zero() -> None:
    assert MonthlyBudgetBase.model_validate({"month": "2026-11"}).income == 0


def test_month_is_unique(session: Session, budget: MonthlyBudget) -> None:
    session.add(MonthlyBudget(month="2026-11"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_category_allocated_once_per_budget(
    session: Session, budget: MonthlyBudget, category: Category
) -> None:
    session.add(
        BudgetAllocation(budget_id=budget.id, category_id=category.id, amount=Decimal("100"))
    )
    session.commit()
    session.add(
        BudgetAllocation(budget_id=budget.id, category_id=category.id, amount=Decimal("200"))
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_allocation_requires_existing_category(session: Session, budget: MonthlyBudget) -> None:
    session.add(BudgetAllocation(budget_id=budget.id, category_id=99, amount=Decimal("100")))

    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_budget_removes_allocations(
    session: Session, budget: MonthlyBudget, category: Category
) -> None:
    session.add(
        BudgetAllocation(budget_id=budget.id, category_id=category.id, amount=Decimal("100"))
    )
    session.commit()

    session.delete(budget)
    session.commit()

    assert session.exec(select(BudgetAllocation)).all() == []
