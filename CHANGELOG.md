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
