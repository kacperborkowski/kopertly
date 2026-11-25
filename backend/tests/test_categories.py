from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import BudgetAllocation, MonthlyBudget


def test_create_category(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "Jedzenie", "color": "#4CAF50"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Jedzenie", "color": "#4CAF50"}


def test_create_category_uses_default_color_and_strips_name(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "  Transport  "})

    assert response.status_code == 201
    assert response.json()["name"] == "Transport"
    assert response.json()["color"] == "#9E9E9E"


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 51},
        {"name": "Dom", "color": "red"},
        {"name": "Dom", "color": "#12345"},
        {"color": "#4CAF50"},
    ],
)
def test_create_category_rejects_invalid_data(client: TestClient, payload: dict) -> None:
    assert client.post("/categories", json=payload).status_code == 422


@pytest.mark.parametrize("duplicate", ["Jedzenie", "jedzenie", " JEDZENIE "])
def test_create_category_rejects_duplicate_name(
    client: TestClient, make_category, duplicate: str
) -> None:
    make_category("Jedzenie")

    response = client.post("/categories", json={"name": duplicate})

    assert response.status_code == 409


def test_list_categories_sorted_by_name(client: TestClient, make_category) -> None:
    make_category("Transport")
    make_category("Dom")
    make_category("Jedzenie")

    names = [category["name"] for category in client.get("/categories").json()]

    assert names == ["Dom", "Jedzenie", "Transport"]


def test_get_category(client: TestClient, make_category) -> None:
    category = make_category()

    response = client.get(f"/categories/{category['id']}")

    assert response.status_code == 200
    assert response.json() == category


def test_get_missing_category_returns_404(client: TestClient) -> None:
    assert client.get("/categories/99").status_code == 404


def test_update_only_color(client: TestClient, make_category) -> None:
    category = make_category("Jedzenie", "#4CAF50")

    response = client.patch(f"/categories/{category['id']}", json={"color": "#FF0000"})

    assert response.status_code == 200
    assert response.json() == {**category, "color": "#FF0000"}


def test_update_name_case_of_same_category(client: TestClient, make_category) -> None:
    category = make_category("Jedzenie")

    response = client.patch(f"/categories/{category['id']}", json={"name": "JEDZENIE"})

    assert response.status_code == 200
    assert response.json()["name"] == "JEDZENIE"


def test_update_name_taken_by_other_category(client: TestClient, make_category) -> None:
    category = make_category("Jedzenie")
    make_category("Transport")

    response = client.patch(f"/categories/{category['id']}", json={"name": "transport"})

    assert response.status_code == 409


def test_update_ignores_null_name(client: TestClient, make_category) -> None:
    category = make_category("Jedzenie")

    response = client.patch(f"/categories/{category['id']}", json={"name": None})

    assert response.status_code == 200
    assert response.json()["name"] == "Jedzenie"


def test_update_rejects_invalid_color(client: TestClient, make_category) -> None:
    category = make_category()

    response = client.patch(f"/categories/{category['id']}", json={"color": "red"})

    assert response.status_code == 422


def test_update_missing_category_returns_404(client: TestClient) -> None:
    assert client.patch("/categories/99", json={"color": "#FF0000"}).status_code == 404


def test_delete_category(client: TestClient, make_category) -> None:
    category = make_category()

    assert client.delete(f"/categories/{category['id']}").status_code == 204
    assert client.get(f"/categories/{category['id']}").status_code == 404


def test_delete_missing_category_returns_404(client: TestClient) -> None:
    assert client.delete("/categories/99").status_code == 404


def test_delete_category_with_expenses_returns_409(
    client: TestClient, make_category, make_expense
) -> None:
    category = make_category("Jedzenie")
    make_expense(category["id"])
    make_expense(category["id"])

    response = client.delete(f"/categories/{category['id']}")

    assert response.status_code == 409
    assert "(2)" in response.json()["detail"]
    assert client.get(f"/categories/{category['id']}").status_code == 200


def test_delete_category_removes_its_budget_allocations(
    client: TestClient, session: Session, make_category
) -> None:
    category = make_category("Jedzenie")
    budget = MonthlyBudget(month="2026-11", income=Decimal("5000"))
    session.add(budget)
    session.commit()
    session.add(
        BudgetAllocation(budget_id=budget.id, category_id=category["id"], amount=Decimal("1200"))
    )
    session.commit()

    response = client.delete(f"/categories/{category['id']}")

    assert response.status_code == 204
    assert session.exec(select(BudgetAllocation)).all() == []
    assert session.get(MonthlyBudget, budget.id) is not None


def _allocate(session: Session, month: str, category_id: int, amount: str) -> None:
    budget = session.exec(select(MonthlyBudget).where(MonthlyBudget.month == month)).first()
    if budget is None:
        budget = MonthlyBudget(month=month)
        session.add(budget)
        session.commit()
    session.add(
        BudgetAllocation(budget_id=budget.id, category_id=category_id, amount=Decimal(amount))
    )
    session.commit()


def _allocations(session: Session) -> list[tuple[str, int, Decimal]]:
    rows = session.exec(
        select(MonthlyBudget.month, BudgetAllocation.category_id, BudgetAllocation.amount)
        .join(MonthlyBudget)
        .order_by(MonthlyBudget.month, BudgetAllocation.category_id)
    ).all()
    return [tuple(row) for row in rows]


def test_delete_category_with_expenses_suggests_move_to(
    client: TestClient, make_category, make_expense
) -> None:
    category = make_category("Jedzenie")
    make_expense(category["id"])

    response = client.delete(f"/categories/{category['id']}")

    assert response.status_code == 409
    assert "move_to" in response.json()["detail"]


def test_delete_category_moves_expenses(client: TestClient, make_category, make_expense) -> None:
    old = make_category("Jedzenie")
    new = make_category("Zakupy")
    first = make_expense(old["id"], amount="10")
    second = make_expense(old["id"], amount="20")

    response = client.delete(f"/categories/{old['id']}", params={"move_to": new["id"]})

    assert response.status_code == 204
    assert client.get(f"/categories/{old['id']}").status_code == 404
    for expense in (first, second):
        assert client.get(f"/expenses/{expense['id']}").json()["category_id"] == new["id"]


def test_delete_category_moves_allocations_and_sums_duplicates(
    client: TestClient, session: Session, make_category
) -> None:
    old = make_category("Jedzenie")
    new = make_category("Zakupy")
    _allocate(session, "2026-10", old["id"], "500")
    _allocate(session, "2026-11", old["id"], "1200")
    _allocate(session, "2026-11", new["id"], "300")

    response = client.delete(f"/categories/{old['id']}", params={"move_to": new["id"]})

    assert response.status_code == 204
    session.expire_all()
    assert _allocations(session) == [
        ("2026-10", new["id"], Decimal("500")),
        ("2026-11", new["id"], Decimal("1500")),
    ]


def test_delete_empty_category_with_move_to(client: TestClient, make_category) -> None:
    old = make_category("Jedzenie")
    new = make_category("Zakupy")

    response = client.delete(f"/categories/{old['id']}", params={"move_to": new["id"]})

    assert response.status_code == 204


def test_delete_category_move_to_itself_returns_422(
    client: TestClient, make_category, make_expense
) -> None:
    category = make_category("Jedzenie")
    make_expense(category["id"])

    response = client.delete(f"/categories/{category['id']}", params={"move_to": category["id"]})

    assert response.status_code == 422
    assert client.get(f"/categories/{category['id']}").status_code == 200


def test_delete_category_move_to_missing_returns_422(
    client: TestClient, make_category, make_expense
) -> None:
    category = make_category("Jedzenie")
    expense = make_expense(category["id"])

    response = client.delete(f"/categories/{category['id']}", params={"move_to": 99})

    assert response.status_code == 422
    assert client.get(f"/expenses/{expense['id']}").json()["category_id"] == category["id"]


def test_delete_missing_category_with_move_to_returns_404(
    client: TestClient, make_category
) -> None:
    target = make_category("Zakupy")

    assert client.delete("/categories/99", params={"move_to": target["id"]}).status_code == 404
