from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status
from sqlmodel import Session, col, select

from app.db import SessionDep
from app.models import (
    MONTH_PATTERN,
    BudgetAllocation,
    BudgetAllocationBase,
    BudgetPublic,
    BudgetUpsert,
    Category,
    MonthlyBudget,
)
from app.months import previous_month

router = APIRouter(prefix="/budgets", tags=["Budżet"])

MonthPath = Annotated[str, Path(pattern=MONTH_PATTERN, examples=["2026-11"])]


def _find_budget(session: Session, month: str) -> MonthlyBudget | None:
    return session.exec(select(MonthlyBudget).where(MonthlyBudget.month == month)).first()


def _get_or_404(session: Session, month: str) -> MonthlyBudget:
    budget = _find_budget(session, month)
    if budget is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Nie ma budżetu na {month}")
    return budget


def _allocations_of(session: Session, budget: MonthlyBudget) -> list[BudgetAllocation]:
    return list(
        session.exec(
            select(BudgetAllocation)
            .where(BudgetAllocation.budget_id == budget.id)
            .order_by(col(BudgetAllocation.category_id))
        ).all()
    )


def _to_public(session: Session, budget: MonthlyBudget) -> BudgetPublic:
    allocations = [
        BudgetAllocationBase(category_id=a.category_id, amount=a.amount)
        for a in _allocations_of(session, budget)
    ]
    return BudgetPublic(month=budget.month, income=budget.income, allocations=allocations)


def _validate_allocations(session: Session, allocations: list[BudgetAllocationBase]) -> None:
    category_ids = [allocation.category_id for allocation in allocations]
    duplicates = sorted({cid for cid in category_ids if category_ids.count(cid) > 1})
    if duplicates:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Kategoria może wystąpić w planie tylko raz (powtórzone id: {duplicates})",
        )
    existing = set(
        session.exec(select(Category.id).where(col(Category.id).in_(category_ids))).all()
    )
    missing = sorted(set(category_ids) - existing)
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Nie ma kategorii o id {missing}",
        )


@router.get("/{month}", response_model=BudgetPublic)
def get_budget(month: MonthPath, session: SessionDep) -> BudgetPublic:
    return _to_public(session, _get_or_404(session, month))


@router.put("/{month}", response_model=BudgetPublic)
def save_budget(month: MonthPath, data: BudgetUpsert, session: SessionDep) -> BudgetPublic:
    _validate_allocations(session, data.allocations)
    budget = _find_budget(session, month) or MonthlyBudget(month=month)
    budget.income = data.income
    session.add(budget)
    session.flush()
    for allocation in _allocations_of(session, budget):
        session.delete(allocation)
    session.flush()
    for allocation in data.allocations:
        session.add(
            BudgetAllocation(
                budget_id=budget.id,
                category_id=allocation.category_id,
                amount=allocation.amount,
            )
        )
    session.commit()
    session.refresh(budget)
    return _to_public(session, budget)


@router.post(
    "/{month}/copy-previous",
    response_model=BudgetPublic,
    status_code=status.HTTP_201_CREATED,
)
def copy_previous_budget(month: MonthPath, session: SessionDep) -> BudgetPublic:
    if _find_budget(session, month) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Budżet na {month} już istnieje",
        )
    source = _get_or_404(session, previous_month(month))
    budget = MonthlyBudget(month=month, income=source.income)
    session.add(budget)
    session.flush()
    for allocation in _allocations_of(session, source):
        session.add(
            BudgetAllocation(
                budget_id=budget.id,
                category_id=allocation.category_id,
                amount=allocation.amount,
            )
        )
    session.commit()
    session.refresh(budget)
    return _to_public(session, budget)


@router.delete("/{month}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(month: MonthPath, session: SessionDep) -> None:
    session.delete(_get_or_404(session, month))
    session.commit()
