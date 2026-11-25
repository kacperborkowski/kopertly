from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from tests.spreadsheets import MONTHS, make_xlsx


@pytest.fixture
def workbook() -> BytesIO:
    return make_xlsx({
        "2025": [
            [None, *MONTHS],
            ["Przychody", 5000, 5100],
            ["Spożywcze"],
            ["Jedzenie do domu", 1000.10, 900.20],
            ["Koty :)", None, 150],
            ["Suma", 100, -50],
        ],
        "2024": [
            [None, *MONTHS],
            ["Jedzenie do domu", *[None] * 11, 800],
            ["Kot :)", *[None] * 11, 120],
        ],
    })


def _preview(client: TestClient, content: BytesIO, name: str = "Wydatki.xlsx"):
    return client.post("/imports/spreadsheet/preview", files={"file": (name, content)})


def test_preview_summarizes_rows(client: TestClient, workbook: BytesIO) -> None:
    response = _preview(client, workbook)

    assert response.status_code == 200
    preview = response.json()
    assert preview["sheets"] == ["2025", "2024"]
    assert preview["first_month"] == "2024-12"
    assert preview["last_month"] == "2025-02"
    food = next(row for row in preview["rows"] if row["label"] == "Jedzenie do domu")
    assert food == {
        "label": "Jedzenie do domu",
        "cells": 3,
        "negative_cells": 0,
        "total": "2700.30",
        "first_month": "2024-12",
        "last_month": "2025-02",
        "suggestion": {"action": "category", "category_id": None, "name": "Jedzenie do domu"},
    }


def test_preview_keeps_label_order_from_sheets(client: TestClient, workbook: BytesIO) -> None:
    labels = [row["label"] for row in _preview(client, workbook).json()["rows"]]

    assert labels == ["Przychody", "Jedzenie do domu", "Koty :)", "Suma", "Kot :)"]


def test_preview_suggestions(client: TestClient, workbook: BytesIO, make_category) -> None:
    cats = make_category("koty :)")

    rows = {row["label"]: row for row in _preview(client, workbook).json()["rows"]}

    assert rows["Przychody"]["suggestion"]["action"] == "income"
    assert rows["Suma"]["suggestion"]["action"] == "skip"
    assert rows["Suma"]["negative_cells"] == 1
    assert rows["Koty :)"]["suggestion"] == {
        "action": "category",
        "category_id": cats["id"],
        "name": None,
    }
    assert rows["Kot :)"]["suggestion"]["name"] == "Kot :)"


def test_preview_does_not_change_database(client: TestClient, workbook: BytesIO) -> None:
    _preview(client, workbook)

    assert client.get("/categories").json() == []
    assert client.get("/expenses").json() == []


def test_preview_returns_warnings(client: TestClient) -> None:
    content = make_xlsx({"2025": [[None, *MONTHS], ["Paliwo", 100], [None, 5]]})

    warnings = _preview(client, content).json()["warnings"]

    assert warnings == ["Arkusz 2025, wiersz 3: liczby bez nazwy, pominięte"]


def test_preview_rejects_non_xlsx(client: TestClient) -> None:
    response = _preview(client, BytesIO(b"Data;Kwota"), name="wydatki.csv")

    assert response.status_code == 422
    assert "xlsx" in response.json()["detail"]


def test_preview_rejects_workbook_without_years(client: TestClient) -> None:
    response = _preview(client, make_xlsx({"Arkusz1": [["a", 1]]}))

    assert response.status_code == 422


def test_preview_requires_file(client: TestClient) -> None:
    assert client.post("/imports/spreadsheet/preview").status_code == 422


def test_preview_rejects_too_large_file(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("app.routers.imports.MAX_FILE_SIZE", 100)
    response = _preview(client, BytesIO(b"x" * 101))

    assert response.status_code == 413
