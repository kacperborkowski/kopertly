# Kopertly

Aplikacja do planowania budżetu metodą kopertową. Każda kategoria to „koperta”
z zaplanowaną kwotą, a wydatki ją opróżniają.

## Funkcje (plan)

- **Budżet:** planowanie miesięcznego budżetu w podziale na kategorie
- **Wydatki:** ręczne wpisywanie albo zdjęcie paragonu, który interpretuje AI, plus wykres wydatków
- **Kategorie:** użytkownik sam definiuje swoje kategorie
- **Własne AI:** użytkownik podpina własnego dostawcę (OpenAI, Claude, Gemini albo lokalną Ollamę)
- **Czat:** rozmowa z AI o wydatkach i realizacji budżetu

## Stack

| Część    | Technologie                          |
|----------|--------------------------------------|
| Frontend | React, Vite, TypeScript              |
| Backend  | Python, FastAPI, SQLModel, SQLite    |
| AI       | LiteLLM (wielu dostawców)            |

## Struktura

```
kopertly/
├── backend/    # API w Pythonie (FastAPI)
└── frontend/   # aplikacja React
```

## Wymagania

- Python 3.13+
- [uv](https://docs.astral.sh/uv/), menedżer pakietów Pythona
- Node.js 22 LTS
- Git

## Wersjonowanie

Projekt stosuje [Semantic Versioning](https://semver.org/lang/pl/) w formacie
`MAJOR.MINOR.PATCH`:

- **MAJOR:** zmiany niezgodne wstecz (np. API lub bazy danych)
- **MINOR:** nowe funkcje
- **PATCH:** poprawki błędów

Dopóki aplikacja jest w budowie, wersje zaczynają się od `0.`. Każdy ukończony
etap planu to nowa wersja `MINOR` (etap 1 to `0.1.0`, etap 2 to `0.2.0` itd.).
Wersja `1.0.0` to pierwsza pełna wersja ze wszystkimi funkcjami z planu.

Przy każdym wydaniu:

1. W [CHANGELOG.md](CHANGELOG.md) przenosimy wpisy z `Unreleased` do sekcji
   nowej wersji.
2. Ustawiamy ten sam numer wersji w `backend/pyproject.toml`
   i `frontend/package.json`.
3. Oznaczamy commit tagiem Git, np. `git tag -a v0.1.0 -m "v0.1.0"`.

Komunikaty commitów piszemy według [Conventional Commits](https://www.conventionalcommits.org/),
dzięki czemu łatwo ustalić, który numer wersji podnieść.
