# Kopertly

A budgeting app based on the envelope method. Each category is an "envelope"
with a planned amount for the month, and every expense takes money out of it.
You always see how much is left in each envelope.

## Features

| Feature | Status |
|---|---|
| **Categories:** user-defined envelopes with a name and color | ✅ API |
| **Expenses:** add, edit, delete, filter by month and category | ✅ API |
| **Budget:** monthly income and planned amount per envelope, copy last month's plan | ✅ API |
| **Plan vs actual:** how much is planned, spent and left in each envelope | ✅ API |
| **Spreadsheet import:** monthly totals from an `.xlsx` file (one sheet per year) | ✅ API |
| **Web app:** budget, expenses with a chart, settings | planned |
| **Receipt scanning:** take a photo of a receipt and let AI read the items | planned |
| **Bring your own AI:** connect OpenAI, Claude, Gemini or a local Ollama | planned |
| **Chat:** talk with AI about your spending and budget | planned |

## Tech stack

| Part | Technologies |
|---|---|
| Backend | Python 3.13, [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/), SQLite, pydantic-settings, openpyxl |
| Frontend | React, Vite, TypeScript *(planned)* |
| AI | [LiteLLM](https://docs.litellm.ai/) for multiple providers *(planned)* |
| Tooling | [uv](https://docs.astral.sh/uv/), pytest, [ruff](https://docs.astral.sh/ruff/), GitHub Actions |

## Project structure

```
kopertly/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app
│   │   ├── config.py      # settings (.env)
│   │   ├── db.py          # database engine and session
│   │   ├── models/        # database tables and API schemas
│   │   ├── routers/       # API endpoints
│   │   └── importers/     # spreadsheet import
│   └── tests/
└── frontend/              # React app (planned)
```

## Getting started

### Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/), which also installs the right Python version
- Node.js 22 LTS (for the frontend, once it exists)

### Run the backend

```bash
cd backend
uv run fastapi dev app/main.py
```

- API: <http://localhost:8000>
- Interactive API docs: <http://localhost:8000/docs>

On the first run, uv downloads Python 3.13 and installs the dependencies.
The SQLite database (`kopertly.db`) is created automatically in `backend/`.

### Configuration

Settings are read from environment variables or a `backend/.env` file.
To customize them, copy the example file:

```bash
cd backend
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `KOPERTLY_APP_NAME` | `Kopertly API` | name shown in the API docs |
| `KOPERTLY_DATABASE_URL` | `sqlite:///./kopertly.db` | database location |

### Tests and linting

```bash
cd backend
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
