"""Ustawienia aplikacji w jednym miejscu.

Wartości są czytane (w tej kolejności, pierwsza znaleziona wygrywa):
1. ze zmiennych środowiskowych, np. `KOPERTLY_DATABASE_URL=...`,
2. z pliku `.env` w folderze `backend/`,
3. z wartości domyślnych zapisanych poniżej.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# Klasa dziedziczy po `BaseSettings` (zapis `class A(B)` oznacza „A dziedziczy po B”).
# Dzięki temu każde pole poniżej pydantic-settings automatycznie wypełni
# wartością ze środowiska i sprawdzi, czy ma właściwy typ.
class Settings(BaseSettings):
    # `nazwa: typ = wartość_domyślna`: pole z podpowiedzią typu i wartością domyślną.
    app_name: str = "Kopertly API"

    # Adres bazy danych. `sqlite:///./kopertly.db` to plik kopertly.db
    # w folderze, z którego uruchamiasz serwer (czyli `backend/`).
    database_url: str = "sqlite:///./kopertly.db"

    # Konfiguracja samego mechanizmu ustawień:
    # - env_prefix: zmienne muszą zaczynać się od KOPERTLY_, żeby nie kolidować
    #   z innymi programami (np. KOPERTLY_APP_NAME ustawia pole app_name),
    # - env_file: skąd czytać plik .env,
    # - extra="ignore": nieznane zmienne w .env nie powodują błędu.
    model_config = SettingsConfigDict(
        env_prefix="KOPERTLY_",
        env_file=".env",
        extra="ignore",
    )


# `@lru_cache` zapamiętuje wynik funkcji: ustawienia wczytujemy raz,
# a każde kolejne wywołanie `get_settings()` zwraca ten sam obiekt.
@lru_cache
def get_settings() -> Settings:
    return Settings()
