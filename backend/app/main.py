"""Punkt wejścia aplikacji: tu tworzymy obiekt FastAPI i rejestrujemy endpointy."""

from fastapi import FastAPI

# `app` to cała nasza aplikacja webowa. Serwer (uvicorn) szuka właśnie tej zmiennej.
app = FastAPI(title="Kopertly API", version="0.0.0")


# Dekorator `@app.get(...)` mówi FastAPI: „gdy przyjdzie żądanie GET na /health,
# wywołaj funkcję poniżej”. To, co funkcja zwróci (słownik), FastAPI zamieni na JSON.
@app.get("/health")
def health() -> dict[str, str]:
    """Prosty test, czy serwer działa."""
    return {"status": "ok"}
