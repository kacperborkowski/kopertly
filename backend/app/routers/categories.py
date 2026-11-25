"""Endpointy kategorii (kopert): tworzenie, lista, podgląd, edycja, usuwanie.

To klasyczny CRUD: Create, Read, Update, Delete.
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, func, select

from app.db import SessionDep
from app.models import (
    BudgetAllocation,
    Category,
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
    Expense,
)

# Router to „mini-aplikacja” z grupą endpointów. W main.py dołączamy go do `app`.
# - prefix: każdy adres w tym pliku zaczyna się od /categories,
# - tags: grupa, pod którą endpointy pojawią się w /docs.
router = APIRouter(prefix="/categories", tags=["Kategorie"])


# --- Funkcje pomocnicze ------------------------------------------------------
# Nazwa zaczynająca się od `_` to w Pythonie umowny znak: „funkcja wewnętrzna,
# używana tylko w tym pliku”.


def _get_or_404(session: Session, category_id: int) -> Category:
    """Zwraca kategorię o podanym id albo przerywa żądanie błędem 404."""
    category = session.get(Category, category_id)
    if category is None:
        # `raise` przerywa funkcję. FastAPI zamieni HTTPException na odpowiedź
        # z kodem 404 i JSON-em {"detail": "..."}.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nie ma takiej kategorii")
    return category


def _ensure_name_free(session: Session, name: str, exclude_id: int | None = None) -> None:
    """Przerywa żądanie błędem 409, jeśli kategoria o tej nazwie już istnieje.

    Porównujemy bez względu na wielkość liter, więc „jedzenie” i „Jedzenie”
    to ta sama koperta. `exclude_id` pomija edytowaną kategorię, żeby przy
    zmianie samego koloru nie zgłaszać konfliktu z nią samą.
    """
    query = select(Category).where(func.lower(Category.name) == name.lower())
    if exclude_id is not None:
        query = query.where(Category.id != exclude_id)
    if session.exec(query).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Kategoria „{name}” już istnieje")


# --- Endpointy ---------------------------------------------------------------
# `response_model` mówi FastAPI, jaki kształt ma odpowiedź: tylko te pola trafią
# do JSON-a i to one pojawią się w dokumentacji.


@router.post("", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, session: SessionDep) -> Category:
    """Tworzy nową kategorię."""
    # `data` to już sprawdzone dane z treści żądania (FastAPI zwalidowało je
    # według CategoryCreate; przy błędzie samo zwraca kod 422).
    _ensure_name_free(session, data.name)
    category = Category.model_validate(data)
    session.add(category)  # dodaj do sesji (jeszcze nie w bazie)
    session.commit()  # zapisz w bazie
    session.refresh(category)  # odczytaj z bazy, żeby dostać nadane `id`
    return category


@router.get("", response_model=list[CategoryPublic])
def list_categories(session: SessionDep) -> list[Category]:
    """Zwraca wszystkie kategorie, posortowane alfabetycznie."""
    return list(session.exec(select(Category).order_by(Category.name)).all())


# `{category_id}` w adresie to parametr ścieżki, np. /categories/3.
# FastAPI sam zamieni „3” na liczbę, bo w funkcji jest `category_id: int`.
@router.get("/{category_id}", response_model=CategoryPublic)
def get_category(category_id: int, session: SessionDep) -> Category:
    """Zwraca jedną kategorię."""
    return _get_or_404(session, category_id)


@router.patch("/{category_id}", response_model=CategoryPublic)
def update_category(category_id: int, data: CategoryUpdate, session: SessionDep) -> Category:
    """Zmienia wybrane pola kategorii (np. tylko kolor)."""
    category = _get_or_404(session, category_id)
    # `exclude_none=True`: bierzemy tylko pola z wartością. Pominięte pola
    # (i wysłane jako null) zostają bez zmian, bo nazwa i kolor są wymagane.
    changes = data.model_dump(exclude_none=True)
    if "name" in changes:
        _ensure_name_free(session, changes["name"], exclude_id=category_id)
    category.sqlmodel_update(changes)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, session: SessionDep, move_to: int | None = None) -> None:
    """Usuwa kategorię. Kod 204 oznacza „udało się, brak treści w odpowiedzi”."""
    category = _get_or_404(session, category_id)
    if move_to is None:
        _ensure_no_expenses(session, category)
    else:
        target = _get_move_target(session, category_id, move_to)
        _move_expenses(session, category_id, target.id)
        _move_allocations(session, category_id, target.id)
    session.delete(category)
    session.commit()


def _ensure_no_expenses(session: Session, category: Category) -> None:
    expense_count = session.exec(
        select(func.count()).where(Expense.category_id == category.id)
    ).one()
    if expense_count > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Kategoria „{category.name}” ma wydatki ({expense_count}). "
            "Podaj w parametrze move_to kategorię, do której je przenieść",
        )


def _get_move_target(session: Session, category_id: int, move_to: int) -> Category:
    if move_to == category_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Nie można przenieść wydatków do usuwanej kategorii",
        )
    target = session.get(Category, move_to)
    if target is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Nie ma kategorii o id {move_to}",
        )
    return target


def _move_expenses(session: Session, source_id: int, target_id: int) -> None:
    expenses = session.exec(select(Expense).where(Expense.category_id == source_id))
    for expense in expenses:
        expense.category_id = target_id
        session.add(expense)


def _move_allocations(session: Session, source_id: int, target_id: int) -> None:
    allocations = session.exec(
        select(BudgetAllocation).where(BudgetAllocation.category_id == source_id)
    ).all()
    for allocation in allocations:
        existing = session.exec(
            select(BudgetAllocation).where(
                BudgetAllocation.budget_id == allocation.budget_id,
                BudgetAllocation.category_id == target_id,
            )
        ).first()
        if existing is None:
            allocation.category_id = target_id
            session.add(allocation)
        else:
            existing.amount += allocation.amount
            session.add(existing)
            session.delete(allocation)
    session.flush()
