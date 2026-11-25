"""Punkt wejścia aplikacji: tu tworzymy obiekt FastAPI i rejestrujemy endpointy."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import text

from app.config import get_settings
from app.db import SessionDep, create_db_and_tables
from app.routers import budgets, categories, expenses

settings = get_settings()


# `lifespan` to kod uruchamiany przy starcie i zamknięciu serwera.
# Wszystko przed `yield` dzieje się przy starcie, a wszystko po nim przy zamknięciu.
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    yield


# `app` to cała nasza aplikacja webowa. Serwer (uvicorn) szuka właśnie tej zmiennej.
app = FastAPI(title=settings.app_name, version="0.0.0", lifespan=lifespan)

# Dołączamy endpointy z osobnych plików (routerów).
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(budgets.router)


# Dekorator `@app.get(...)` mówi FastAPI: „gdy przyjdzie żądanie GET na /health,
# wywołaj funkcję poniżej”. To, co funkcja zwróci (słownik), FastAPI zamieni na JSON.
@app.get("/health")
def health(session: SessionDep) -> dict[str, str]:
    """Sprawdza, czy serwer działa i czy baza danych odpowiada."""
    # `SELECT 1` to najprostsze możliwe zapytanie: jeśli baza odpowie,
    # połączenie działa. Gdyby nie działało, FastAPI zwróci błąd 500.
    session.exec(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
