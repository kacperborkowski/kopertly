"""Punkt wejścia aplikacji: tu tworzymy obiekt FastAPI i rejestrujemy endpointy."""

import tomllib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlmodel import text

from app.config import get_settings
from app.db import SessionDep, create_db_and_tables
from app.routers import budgets, categories, expenses, imports

settings = get_settings()

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"
VERSION = tomllib.loads(PYPROJECT.read_text())["project"]["version"]


# `lifespan` to kod uruchamiany przy starcie i zamknięciu serwera.
# Wszystko przed `yield` dzieje się przy starcie, a wszystko po nim przy zamknięciu.
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    yield


# `app` to cała nasza aplikacja webowa. Serwer (uvicorn) szuka właśnie tej zmiennej.
app = FastAPI(title=settings.app_name, version=VERSION, lifespan=lifespan)

# Dołączamy endpointy z osobnych plików (routerów).
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(budgets.router)
app.include_router(imports.router)


# Dekorator `@app.get(...)` mówi FastAPI: „gdy przyjdzie żądanie GET na /health,
# wywołaj funkcję poniżej”. To, co funkcja zwróci (słownik), FastAPI zamieni na JSON.
@app.get("/health")
def health(session: SessionDep) -> dict[str, str]:
    """Sprawdza, czy serwer działa i czy baza danych odpowiada."""
    # `SELECT 1` to najprostsze możliwe zapytanie: jeśli baza odpowie,
    # połączenie działa. Gdyby nie działało, FastAPI zwróci błąd 500.
    session.exec(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
