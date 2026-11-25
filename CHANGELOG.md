# Changelog

Wszystkie istotne zmiany w projekcie Kopertly są opisane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/),
a numeracja wersji na [Semantic Versioning](https://semver.org/lang/pl/).

## [Unreleased]

### Added

- README z opisem aplikacji i `.gitignore`
- Zasady wersjonowania i ten plik CHANGELOG
- Backend: projekt FastAPI zarządzany przez uv, endpoint `GET /health`
- Backend: konfiguracja przez pydantic-settings (plik `.env`, zmienne `KOPERTLY_*`)
- Backend: połączenie z bazą SQLite przez SQLModel; `GET /health` sprawdza też bazę
- Backend: model `Category` (koperta): unikalna nazwa i kolor HEX
- Backend: endpointy `/categories` (tworzenie, lista, podgląd, edycja, usuwanie)
- Backend: model `Expense` (kwota, data, kategoria, sklep, opis); włączone klucze obce w SQLite
- Backend: usunięcie kategorii z wydatkami zwraca 409 zamiast błędu serwera
- Backend: `POST /expenses` i `GET /expenses` z filtrami `month` (RRRR-MM) i `category_id`
- Backend: podgląd, edycja i usuwanie wydatku (`GET`, `PATCH`, `DELETE /expenses/{id}`)
