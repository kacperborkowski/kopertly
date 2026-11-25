"""Endpointy kategorii (kopert): tworzenie, lista, podgląd, edycja, usuwanie.

To klasyczny CRUD: Create, Read, Update, Delete.
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, func, select

from app.db import SessionDep
from app.models import (
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


def _ensure_name_free(
    session: Session, name: str, exclude_id: int | None = None
) -> None:
    """Przerywa żądanie błędem 409, jeśli kategoria o tej nazwie już istnieje.

    Porównujemy bez względu na wielkość liter, więc „jedzenie” i „Jedzenie”
    to ta sama koperta. `exclude_id` pomija edytowaną kategorię, żeby przy
    zmianie samego koloru nie zgłaszać konfliktu z nią samą.
    """
    query = select(Category).where(func.lower(Category.name) == name.lower())
    if exclude_id is not None:
        query = query.where(Category.id != exclude_id)
    if session.exec(query).first() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Kategoria „{name}” już istnieje"
        )


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
def update_category(
    category_id: int, data: CategoryUpdate, session: SessionDep
) -> Category:
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
def delete_category(category_id: int, session: SessionDep) -> None:
    """Usuwa kategorię. Kod 204 oznacza „udało się, brak treści w odpowiedzi”."""
    category = _get_or_404(session, category_id)
    expense_count = session.exec(
        select(func.count()).where(Expense.category_id == category_id)
    ).one()
    if expense_count > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Kategoria „{category.name}” ma wydatki ({expense_count}), "
            "nie można jej usunąć",
        )
    session.delete(category)
    session.commit()
