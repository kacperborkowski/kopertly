import pytest
from fastapi.testclient import TestClient


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
