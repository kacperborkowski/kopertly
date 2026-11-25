import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def categories(make_category) -> tuple[dict, dict]:
    return make_category("Jedzenie"), make_category("Transport")


def _plan(food: dict, transport: dict, income: str = "5000.00") -> dict:
    return {
        "income": income,
        "allocations": [
            {"category_id": food["id"], "amount": "1200.00"},
            {"category_id": transport["id"], "amount": "300.00"},
        ],
    }


def test_get_missing_budget_returns_404(client: TestClient) -> None:
    assert client.get("/budgets/2026-11").status_code == 404


@pytest.mark.parametrize("month", ["2026-13", "listopad"])
def test_invalid_month_returns_422(client: TestClient, month: str) -> None:
    assert client.get(f"/budgets/{month}").status_code == 422
    assert client.put(f"/budgets/{month}", json={}).status_code == 422


def test_save_new_budget(client: TestClient, categories: tuple[dict, dict]) -> None:
    plan = _plan(*categories)

    response = client.put("/budgets/2026-11", json=plan)

    assert response.status_code == 200
    assert response.json() == {"month": "2026-11", **plan}
    assert client.get("/budgets/2026-11").json() == response.json()


def test_save_budget_replaces_whole_plan(client: TestClient, categories: tuple[dict, dict]) -> None:
    food, transport = categories
    client.put("/budgets/2026-11", json=_plan(food, transport))
    new_plan = {
        "income": "6000.00",
        "allocations": [{"category_id": transport["id"], "amount": "400.00"}],
    }

    response = client.put("/budgets/2026-11", json=new_plan)

    assert response.json() == {"month": "2026-11", **new_plan}


def test_save_budget_with_defaults(client: TestClient) -> None:
    response = client.put("/budgets/2026-11", json={})

    assert response.json() == {"month": "2026-11", "income": "0.00", "allocations": []}


def test_save_budget_allows_zero_allocation(
    client: TestClient, categories: tuple[dict, dict]
) -> None:
    food, _ = categories

    response = client.put(
        "/budgets/2026-11", json={"allocations": [{"category_id": food["id"], "amount": "0"}]}
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "plan",
    [
        {"income": "-1"},
        {"allocations": [{"category_id": 1, "amount": "-1"}]},
        {"allocations": [{"category_id": 1, "amount": "1.005"}]},
        {"allocations": [{"amount": "100"}]},
    ],
)
def test_save_budget_rejects_invalid_data(
    client: TestClient, categories: tuple[dict, dict], plan: dict
) -> None:
    assert client.put("/budgets/2026-11", json=plan).status_code == 422


def test_save_budget_rejects_duplicate_category(
    client: TestClient, categories: tuple[dict, dict]
) -> None:
    food, _ = categories
    allocation = {"category_id": food["id"], "amount": "100"}

    response = client.put("/budgets/2026-11", json={"allocations": [allocation, allocation]})

    assert response.status_code == 422
    assert client.get("/budgets/2026-11").status_code == 404


def test_save_budget_rejects_missing_category(client: TestClient) -> None:
    response = client.put(
        "/budgets/2026-11", json={"allocations": [{"category_id": 99, "amount": "100"}]}
    )

    assert response.status_code == 422
    assert "99" in response.json()["detail"]


def test_copy_previous_month(client: TestClient, categories: tuple[dict, dict]) -> None:
    plan = _plan(*categories)
    client.put("/budgets/2026-10", json=plan)

    response = client.post("/budgets/2026-11/copy-previous")

    assert response.status_code == 201
    assert response.json() == {"month": "2026-11", **plan}
    assert client.get("/budgets/2026-10").json()["month"] == "2026-10"


def test_copy_previous_across_year(client: TestClient, categories: tuple[dict, dict]) -> None:
    client.put("/budgets/2026-12", json=_plan(*categories, income="7000.00"))

    response = client.post("/budgets/2027-01/copy-previous")

    assert response.status_code == 201
    assert response.json()["income"] == "7000.00"


def test_copy_previous_is_independent_copy(
    client: TestClient, categories: tuple[dict, dict]
) -> None:
    client.put("/budgets/2026-10", json=_plan(*categories))
    client.post("/budgets/2026-11/copy-previous")

    client.put("/budgets/2026-11", json={"income": "1.00"})

    assert client.get("/budgets/2026-10").json()["income"] == "5000.00"
    assert len(client.get("/budgets/2026-10").json()["allocations"]) == 2


def test_copy_previous_when_missing_returns_404(client: TestClient) -> None:
    response = client.post("/budgets/2026-11/copy-previous")

    assert response.status_code == 404
    assert "2026-10" in response.json()["detail"]


def test_copy_previous_when_target_exists_returns_409(
    client: TestClient, categories: tuple[dict, dict]
) -> None:
    client.put("/budgets/2026-10", json=_plan(*categories))
    client.put("/budgets/2026-11", json={"income": "1.00"})

    response = client.post("/budgets/2026-11/copy-previous")

    assert response.status_code == 409
    assert client.get("/budgets/2026-11").json()["income"] == "1.00"


def test_delete_budget(client: TestClient, categories: tuple[dict, dict]) -> None:
    client.put("/budgets/2026-11", json=_plan(*categories))

    assert client.delete("/budgets/2026-11").status_code == 204
    assert client.get("/budgets/2026-11").status_code == 404


def test_delete_missing_budget_returns_404(client: TestClient) -> None:
    assert client.delete("/budgets/2026-11").status_code == 404


def test_deleted_category_disappears_from_plan(
    client: TestClient, categories: tuple[dict, dict]
) -> None:
    food, transport = categories
    client.put("/budgets/2026-11", json=_plan(food, transport))

    client.delete(f"/categories/{transport['id']}")

    allocations = client.get("/budgets/2026-11").json()["allocations"]
    assert allocations == [{"category_id": food["id"], "amount": "1200.00"}]
