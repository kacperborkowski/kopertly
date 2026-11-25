"""Punkt wejścia aplikacji: tu tworzymy obiekt FastAPI i rejestrujemy endpointy."""

from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

# `app` to cała nasza aplikacja webowa. Serwer (uvicorn) szuka właśnie tej zmiennej.
app = FastAPI(title=settings.app_name, version="0.0.0")


# Dekorator `@app.get(...)` mówi FastAPI: „gdy przyjdzie żądanie GET na /health,
# wywołaj funkcję poniżej”. To, co funkcja zwróci (słownik), FastAPI zamieni na JSON.
@app.get("/health")
def health() -> dict[str, str]:
    """Prosty test, czy serwer działa."""
    return {"status": "ok"}
