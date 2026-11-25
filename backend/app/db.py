"""Połączenie z bazą danych (SQLite przez SQLModel)."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()


# Silnik (engine) to obiekt, który zarządza połączeniami z bazą.
# Tworzymy go raz, na całą aplikację.
#
# `check_same_thread=False`: SQLite domyślnie pozwala używać połączenia tylko
# w wątku, który je utworzył. FastAPI obsługuje żądania w wielu wątkach,
# więc wyłączamy to ograniczenie (każde żądanie i tak dostaje własną sesję).
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(database_url: str, **kwargs) -> Engine:
    new_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        **kwargs,
    )
    event.listen(new_engine, "connect", _enable_sqlite_foreign_keys)
    return new_engine


engine = make_engine(settings.database_url)


def create_db_and_tables(bind: Engine = engine) -> None:
    """Tworzy tabele dla wszystkich modeli, których jeszcze nie ma w bazie.

    Uwaga: `create_all` tylko tworzy brakujące tabele. Nie zmienia tabel, które
    już istnieją (np. gdy dodamy nowe pole do modelu). Na tym etapie wystarczy
    wtedy usunąć plik kopertly.db; później dodamy do tego narzędzie (migracje).
    """
    # SQLModel zna tylko modele, które zostały zaimportowane. Import wewnątrz
    # funkcji gwarantuje, że wszystkie modele są załadowane, zanim utworzymy tabele.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(bind)


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
