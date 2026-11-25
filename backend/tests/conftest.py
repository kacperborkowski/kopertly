from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from app.db import create_db_and_tables, get_session, make_engine
from app.main import app


@pytest.fixture
def session() -> Generator[Session]:
    test_engine = make_engine("sqlite://", poolclass=StaticPool)
    create_db_and_tables(test_engine)
    with Session(test_engine) as test_session:
        yield test_session
    test_engine.dispose()


@pytest.fixture
def client(session: Session) -> Generator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_category(client: TestClient):
    def _make(name: str = "Jedzenie", color: str = "#4CAF50") -> dict:
        response = client.post("/categories", json={"name": name, "color": color})
        assert response.status_code == 201
        return response.json()

    return _make


@pytest.fixture
def make_expense(client: TestClient):
    def _make(category_id: int, amount: str = "10.00", spent_on: str = "2026-11-15", **extra) -> dict:
        payload = {"amount": amount, "spent_on": spent_on, "category_id": category_id, **extra}
        response = client.post("/expenses", json=payload)
        assert response.status_code == 201
        return response.json()

    return _make
