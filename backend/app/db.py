"""Połączenie z bazą danych (SQLite przez SQLModel)."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()

# Silnik (engine) to obiekt, który zarządza połączeniami z bazą.
# Tworzymy go raz, na całą aplikację.
#
# `check_same_thread=False`: SQLite domyślnie pozwala używać połączenia tylko
# w wątku, który je utworzył. FastAPI obsługuje żądania w wielu wątkach,
# więc wyłączamy to ograniczenie (każde żądanie i tak dostaje własną sesję).
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """Tworzy tabele dla wszystkich modeli, których jeszcze nie ma w bazie.

    SQLModel zna tylko modele, które zostały już zaimportowane, więc w kolejnych
    krokach będziemy importować tu moduły z modelami (Category, Expense...).
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    """Daje sesję bazy danych na czas jednego żądania HTTP.

    `yield` zamiast `return` robi z funkcji generator: FastAPI dostaje sesję,
    obsługuje żądanie, a po jego zakończeniu wraca tutaj i blok `with`
    zamyka sesję. Dzięki temu nie musimy pamiętać o jej zamykaniu.
    """
    with Session(engine) as session:
        yield session


# Skrót do użycia w endpointach: zamiast pisać za każdym razem
# `session: Session = Depends(get_session)` napiszemy `session: SessionDep`.
# `Depends` to mechanizm FastAPI „wstrzykiwania zależności”: FastAPI samo
# wywoła `get_session()` i przekaże wynik do funkcji endpointu.
SessionDep = Annotated[Session, Depends(get_session)]
