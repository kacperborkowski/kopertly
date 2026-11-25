"""Model kategorii, czyli „koperty” w budżecie."""

from typing import Annotated

from pydantic import StringConstraints
from sqlmodel import Field, SQLModel

# Typ „kolor HEX”: tekst, który musi pasować do wyrażenia regularnego:
# „#” i dokładnie 6 znaków 0-9 / a-f / A-F, np. „#4CAF50”.
# `Annotated[typ, ograniczenia]` dokleja do zwykłego typu dodatkowe reguły walidacji.
HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]


# Klasa bazowa ze wspólnymi polami. Bez `table=True`, więc to NIE jest tabela,
# tylko opis danych. Wykorzystamy ją w następnym kroku także do walidacji
# danych przychodzących z API (np. przy tworzeniu kategorii).
class CategoryBase(SQLModel):
    # Nazwa koperty, np. „Jedzenie”. Unikalna: nie może być dwóch „Jedzenie”.
    name: str = Field(min_length=1, max_length=50, unique=True, index=True)

    # Kolor w formacie HEX, np. „#4CAF50”. Przyda się w wykresach i interfejsie.
    color: HexColor = "#9E9E9E"


# `table=True` oznacza: ta klasa to tabela w bazie danych (nazwa tabeli: „category”).
# Dziedziczy pola `name` i `color` z `CategoryBase` i dodaje klucz główny `id`.
class Category(CategoryBase, table=True):
    # `int | None`: przed zapisem do bazy obiekt nie ma jeszcze id (None),
    # baza nada je sama przy zapisie (kolejne liczby: 1, 2, 3...).
    id: int | None = Field(default=None, primary_key=True)
