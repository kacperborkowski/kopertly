import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def category(make_category) -> dict:
    return make_category("Jedzenie")


def test_create_expense(client: TestClient, category: dict) -> None:
    payload = {
        "amount": "12.50",
        "spent_on": "2026-11-25",
        "category_id": category["id"],
        "shop": "Biedronka",
        "description": "zakupy",
    }

    response = client.post("/expenses", json=payload)

    assert response.status_code == 201
    assert response.json() == {**payload, "id": 1}


def test_create_expense_accepts_number_amount(client: TestClient, category: dict) -> None:
    response = client.post(
        "/expenses",
        json={"amount": 12.5, "spent_on": "2026-11-25", "category_id": category["id"]},
    )

    assert response.status_code == 201
    assert response.json()["amount"] == "12.50"


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": "0"},
        {"amount": "-5"},
        {"amount": "12.555"},
        {"amount": "abc"},
        {"spent_on": "25.11.2026"},
        {"shop": "x" * 101},
        {"description": "x" * 256},
    ],
)
def test_create_expense_rejects_invalid_data(
    client: TestClient, category: dict, changes: dict
) -> None:
    payload = {"amount": "10", "spent_on": "2026-11-25", "category_id": category["id"]}

    response = client.post("/expenses", json={**payload, **changes})

    assert response.status_code == 422


def test_create_expense_rejects_missing_category(client: TestClient) -> None:
    response = client.post(
        "/expenses", json={"amount": "10", "spent_on": "2026-11-25", "category_id": 99}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Nie ma kategorii o id 99"


def test_list_expenses_newest_first(client: TestClient, category: dict, make_expense) -> None:
    make_expense(category["id"], spent_on="2026-11-03")
    make_expense(category["id"], spent_on="2026-11-25")
    make_expense(category["id"], spent_on="2026-10-31")

    dates = [expense["spent_on"] for expense in client.get("/expenses").json()]

    assert dates == ["2026-11-25", "2026-11-03", "2026-10-31"]


def test_list_expenses_filtered_by_month(
    client: TestClient, category: dict, make_expense
) -> None:
    make_expense(category["id"], spent_on="2026-10-31")
    make_expense(category["id"], spent_on="2026-11-01")
    make_expense(category["id"], spent_on="2026-11-30")
    make_expense(category["id"], spent_on="2026-12-01")

    response = client.get("/expenses", params={"month": "2026-11"})

    assert [e["spent_on"] for e in response.json()] == ["2026-11-30", "2026-11-01"]


def test_list_expenses_filtered_by_december(
    client: TestClient, category: dict, make_expense
) -> None:
    make_expense(category["id"], spent_on="2026-12-31")
    make_expense(category["id"], spent_on="2027-01-01")

    response = client.get("/expenses", params={"month": "2026-12"})

    assert [e["spent_on"] for e in response.json()] == ["2026-12-31"]


def test_list_expenses_filtered_by_category(
    client: TestClient, category: dict, make_category, make_expense
) -> None:
    transport = make_category("Transport")
    make_expense(category["id"], amount="10")
    make_expense(transport["id"], amount="20")

    response = client.get("/expenses", params={"category_id": transport["id"]})

    assert [e["amount"] for e in response.json()] == ["20.00"]


@pytest.mark.parametrize("month", ["2026-13", "2026-1", "listopad"])
def test_list_expenses_rejects_invalid_month(client: TestClient, month: str) -> None:
    assert client.get("/expenses", params={"month": month}).status_code == 422


def test_get_expense(client: TestClient, category: dict, make_expense) -> None:
    expense = make_expense(category["id"])

    response = client.get(f"/expenses/{expense['id']}")

    assert response.status_code == 200
    assert response.json() == expense


def test_get_missing_expense_returns_404(client: TestClient) -> None:
    assert client.get("/expenses/99").status_code == 404


def test_update_expense_fields(
    client: TestClient, category: dict, make_category, make_expense
) -> None:
    transport = make_category("Transport")
    expense = make_expense(category["id"], amount="12.50")
    changes = {"amount": "15.20", "spent_on": "2026-11-20", "category_id": transport["id"]}

    response = client.patch(f"/expenses/{expense['id']}", json=changes)

    assert response.status_code == 200
    assert response.json() == {**expense, **changes}


def test_update_expense_null_clears_optional_field(
    client: TestClient, category: dict, make_expense
) -> None:
    expense = make_expense(category["id"], shop="Biedronka")

    response = client.patch(f"/expenses/{expense['id']}", json={"shop": None})

    assert response.json()["shop"] is None


def test_update_expense_null_ignored_for_required_field(
    client: TestClient, category: dict, make_expense
) -> None:
    expense = make_expense(category["id"], amount="12.50")

    response = client.patch(f"/expenses/{expense['id']}", json={"amount": None})

    assert response.status_code == 200
    assert response.json()["amount"] == "12.50"


def test_update_expense_rejects_missing_category(
    client: TestClient, category: dict, make_expense
) -> None:
    expense = make_expense(category["id"])

    response = client.patch(f"/expenses/{expense['id']}", json={"category_id": 99})

    assert response.status_code == 422


def test_update_expense_rejects_invalid_amount(
    client: TestClient, category: dict, make_expense
) -> None:
    expense = make_expense(category["id"])

    response = client.patch(f"/expenses/{expense['id']}", json={"amount": "-1"})

    assert response.status_code == 422


def test_update_missing_expense_returns_404(client: TestClient) -> None:
    assert client.patch("/expenses/99", json={"amount": "1"}).status_code == 404


def test_delete_expense(client: TestClient, category: dict, make_expense) -> None:
    expense = make_expense(category["id"])

    assert client.delete(f"/expenses/{expense['id']}").status_code == 204
    assert client.get(f"/expenses/{expense['id']}").status_code == 404


def test_delete_missing_expense_returns_404(client: TestClient) -> None:
    assert client.delete("/expenses/99").status_code == 404
