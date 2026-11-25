# Kopertly

A budgeting app based on the envelope method. Each category is an "envelope"
with a planned amount, and expenses empty it.

## Features (planned)

- **Budget:** plan a monthly budget split into categories
- **Expenses:** enter them manually or snap a receipt photo that AI reads, plus a spending chart
- **Categories:** users define their own categories
- **Bring your own AI:** users connect their own provider (OpenAI, Claude, Gemini or a local Ollama)
- **Chat:** talk with AI about your spending and how well you stick to the budget

## Stack

| Part     | Technologies                         |
|----------|--------------------------------------|
| Frontend | React, Vite, TypeScript              |
| Backend  | Python, FastAPI, SQLModel, SQLite    |
| AI       | LiteLLM (multiple providers)         |

## Structure

```
kopertly/
├── backend/    # Python API (FastAPI)
└── frontend/   # React app
```

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/), a Python package manager
- Node.js 22 LTS
- Git

## Getting started

### Backend

```bash
cd backend
uv run fastapi dev app/main.py
```

The API runs at <http://localhost:8000>, with interactive docs at
<http://localhost:8000/docs>. On the first run, uv downloads the right Python
version and installs the dependencies.

Tests:

```bash
cd backend
uv run pytest
```

Linting and formatting ([ruff](https://docs.astral.sh/ruff/)):

```bash
cd backend
uv run ruff check .
uv run ruff format .
```

## Versioning

The project follows [Semantic Versioning](https://semver.org/) in the
`MAJOR.MINOR.PATCH` format:

- **MAJOR:** backward-incompatible changes (e.g. to the API or the database)
- **MINOR:** new features
- **PATCH:** bug fixes

While the app is under construction, versions start with `0.`. Each completed
stage of the plan is a new `MINOR` version (stage 1 is `0.1.0`, stage 2 is
`0.2.0`, and so on). Version `1.0.0` is the first complete release with every
planned feature.

For each release:

1. In [CHANGELOG.md](CHANGELOG.md), move the entries from `Unreleased` into a
   section for the new version.
2. Set the same version number in `backend/pyproject.toml` and
   `frontend/package.json`.
3. Tag the commit in Git, e.g. `git tag -a v0.1.0 -m "v0.1.0"`.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/),
which makes it easy to decide which version number to bump.
