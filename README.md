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
