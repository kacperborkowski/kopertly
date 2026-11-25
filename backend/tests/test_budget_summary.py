import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def categories(make_category) -> dict[str, dict]:
    return {
        "food": make_category("Jedzenie", "#4CAF50"),
        "transport": make_category("Transport", "#2196F3"),
        "fun": make_category("Rozrywka", "#FF9800"),
        "unused": make_category("Zwierzęta", "#795548"),
    }


@pytest.fixture
def november(client: TestClient, categories: dict[str, dict], make_expense) -> None:
    food, transport, fun = categories["food"], categories["transport"], categories["fun"]
    client.put(
        "/budgets/2026-11",
        json={
            "income": "5000",
            "allocations": [
                {"category_id": food["id"], "amount": "1200"},
                {"category_id": transport["id"], "amount": "300"},
            ],
        },
    )
    make_expense(food["id"], amount="0.10", spent_on="2026-11-01")
    make_expense(food["id"], amount="0.20", spent_on="2026-11-30")
    make_expense(food["id"], amount="999.70", spent_on="2026-11-15")
    make_expense(transport["id"], amount="350", spent_on="2026-11-10")
    make_expense(fun["id"], amount="80", spent_on="2026-11-20")
    make_expense(food["id"], amount="500", spent_on="2026-10-31")
    make_expense(food["id"], amount="500", spent_on="2026-12-01")


def test_summary_totals(client: TestClient, november: None) -> None:
    summary = client.get("/budgets/2026-11/summary").json()

    assert summary["month"] == "2026-11"
    assert summary["has_budget"] is True
    assert summary["income"] == "5000.00"
    assert summary["planned_total"] == "1500.00"
    assert summary["spent_total"] == "1430.00"
    assert summary["remaining_total"] == "70.00"
    assert summary["unallocated"] == "3500.00"


def test_summary_per_category(
    client: TestClient, categories: dict[str, dict], november: None
) -> None:
    rows = client.get("/budgets/2026-11/summary").json()["categories"]

    assert rows == [
        {
            "category_id": categories["food"]["id"],
            "name": "Jedzenie",
            "color": "#4CAF50",
            "planned": "1200.00",
            "spent": "1000.00",
            "remaining": "200.00",
        },
        {
            "category_id": categories["fun"]["id"],
            "name": "Rozrywka",
            "color": "#FF9800",
            "planned": "0.00",
            "spent": "80.00",
            "remaining": "-80.00",
        },
        {
            "category_id": categories["transport"]["id"],
            "name": "Transport",
            "color": "#2196F3",
            "planned": "300.00",
            "spent": "350.00",
            "remaining": "-50.00",
        },
    ]


def test_summary_without_budget_shows_spending(
    client: TestClient, categories: dict[str, dict], make_expense
) -> None:
    make_expense(categories["food"]["id"], amount="42.50", spent_on="2026-11-05")

    summary = client.get("/budgets/2026-11/summary").json()

    assert summary["has_budget"] is False
    assert summary["income"] == "0.00"
    assert summary["spent_total"] == "42.50"
    assert summary["unallocated"] == "0.00"
    assert [row["remaining"] for row in summary["categories"]] == ["-42.50"]


def test_summary_of_empty_month(client: TestClient) -> None:
    summary = client.get("/budgets/2026-11/summary").json()

    assert summary["has_budget"] is False
    assert summary["categories"] == []
    assert summary["spent_total"] == "0.00"


def test_summary_invalid_month_returns_422(client: TestClient) -> None:
    assert client.get("/budgets/2026-13/summary").status_code == 422
