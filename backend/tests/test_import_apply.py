import json
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from tests.spreadsheets import MONTHS, make_xlsx


def _workbook() -> BytesIO:
    return make_xlsx(
        {
            "2025": [
                [None, *MONTHS],
                ["Przychody", 5000, 5100.50],
                ["Spożywcze"],
                ["Jedzenie do domu", 1000.10, 900.20],
                ["Koty :)", None, 150],
                ["Suma", 100, -50],
            ],
            "2024": [
                [None, *MONTHS],
                ["Jedzenie do domu", *[None] * 11, 800],
                ["Kot :)", *[None] * 11, 120],
                ["Weterynarz", *[None] * 11, -30],
            ],
        }
    )


MAPPING = {
    "Przychody": {"action": "income"},
    "Jedzenie do domu": {"action": "category", "name": "Jedzenie do domu"},
    "Koty :)": {"action": "category", "name": "Koty :)"},
    "Kot :)": {"action": "category", "name": "koty :)"},
    "Weterynarz": {"action": "category", "name": "Koty :)"},
    "Suma": {"action": "skip"},
}


def _import(client: TestClient, mapping: dict | str = MAPPING, content: BytesIO | None = None):
    return client.post(
        "/imports/spreadsheet",
        files={"file": ("Wydatki.xlsx", content or _workbook())},
        data={"mapping": mapping if isinstance(mapping, str) else json.dumps(mapping)},
    )


def test_import_creates_categories_expenses_and_income(client: TestClient) -> None:
    response = _import(client)

    assert response.status_code == 200
    assert response.json() == {
        "categories_created": ["Jedzenie do domu", "Koty :)"],
        "expenses_created": 5,
        "expenses_already_imported": 0,
        "budgets_with_income": 2,
        "skipped_labels": ["Suma"],
        "warnings": ["„Weterynarz”, 2024-12: kwota ujemna (-30.00), pominięta"],
    }


def test_imported_expenses_are_dated_last_day_of_month(client: TestClient) -> None:
    _import(client)
    categories = {c["name"]: c["id"] for c in client.get("/categories").json()}

    expenses = client.get("/expenses", params={"category_id": categories["Koty :)"]}).json()

    assert [(e["spent_on"], e["amount"], e["description"]) for e in expenses] == [
        ("2025-02-28", "150.00", "Import z arkusza: Koty :)"),
        ("2024-12-31", "120.00", "Import z arkusza: Kot :)"),
    ]


def test_imported_income_appears_in_budget(client: TestClient) -> None:
    _import(client)

    january = client.get("/budgets/2025-01").json()
    february = client.get("/budgets/2025-02/summary").json()

    assert january == {"month": "2025-01", "income": "5000.00", "allocations": []}
    assert february["income"] == "5100.50"
    assert february["spent_total"] == "1050.20"


def test_import_into_existing_category_by_id(client: TestClient, make_category) -> None:
    food = make_category("Jedzenie")
    mapping = {**MAPPING, "Jedzenie do domu": {"action": "category", "category_id": food["id"]}}

    result = _import(client, mapping).json()

    assert result["categories_created"] == ["Koty :)"]
    assert len(client.get("/expenses", params={"category_id": food["id"]}).json()) == 3


def test_import_reuses_existing_category_by_name(client: TestClient, make_category) -> None:
    make_category("KOTY :)")

    result = _import(client).json()

    assert result["categories_created"] == ["Jedzenie do domu"]


def test_reimport_does_not_duplicate(client: TestClient) -> None:
    _import(client)

    second = _import(client).json()

    assert second["expenses_created"] == 0
    assert second["expenses_already_imported"] == 5
    assert second["categories_created"] == []
    assert len(client.get("/expenses").json()) == 5


def test_reimport_with_new_month_adds_only_new_values(client: TestClient) -> None:
    _import(client)
    newer = make_xlsx({"2025": [[None, *MONTHS], ["Jedzenie do domu", 1000.10, 900.20, 700]]})

    result = _import(client, {"Jedzenie do domu": MAPPING["Jedzenie do domu"]}, newer).json()

    assert result["expenses_created"] == 1
    assert result["expenses_already_imported"] == 2


def test_reimport_overwrites_income(client: TestClient) -> None:
    client.put("/budgets/2025-01", json={"income": "1.00"})

    _import(client)

    assert client.get("/budgets/2025-01").json()["income"] == "5000.00"


def test_import_keeps_existing_budget_allocations(client: TestClient, make_category) -> None:
    fuel = make_category("Paliwo")
    plan = {"income": "1.00", "allocations": [{"category_id": fuel["id"], "amount": "300.00"}]}
    client.put("/budgets/2025-01", json=plan)

    _import(client)

    assert client.get("/budgets/2025-01").json()["allocations"] == plan["allocations"]


def test_import_requires_mapping_for_every_label(client: TestClient) -> None:
    mapping = {k: v for k, v in MAPPING.items() if k != "Kot :)"}

    response = _import(client, mapping)

    assert response.status_code == 422
    assert "Kot :)" in response.json()["detail"]
    assert client.get("/categories").json() == []


def test_import_ignores_extra_labels_in_mapping(client: TestClient) -> None:
    mapping = {**MAPPING, "Nie ma mnie w pliku": {"action": "skip"}}

    assert _import(client, mapping).status_code == 200


def test_import_rejects_missing_category_id_without_changes(client: TestClient) -> None:
    mapping = {**MAPPING, "Suma": {"action": "category", "category_id": 99}}

    response = _import(client, mapping)

    assert response.status_code == 422
    assert client.get("/categories").json() == []
    assert client.get("/expenses").json() == []


@pytest.mark.parametrize(
    "target",
    [
        {"action": "category"},
        {"action": "category", "category_id": 1, "name": "Paliwo"},
        {"action": "skip", "name": "Paliwo"},
        {"action": "income", "category_id": 1},
        {"action": "category", "name": "   "},
        {"action": "usuń"},
    ],
)
def test_import_rejects_invalid_target(client: TestClient, target: dict) -> None:
    response = _import(client, {**MAPPING, "Suma": target})

    assert response.status_code == 422


def test_import_rejects_mapping_that_is_not_json(client: TestClient) -> None:
    response = _import(client, "to nie json")

    assert response.status_code == 422


def test_import_rejects_non_xlsx(client: TestClient) -> None:
    response = _import(client, MAPPING, BytesIO(b"Data;Kwota"))

    assert response.status_code == 422


def test_import_sums_repeated_label_in_same_month(client: TestClient) -> None:
    content = make_xlsx(
        {
            "2025": [[None, *MONTHS], ["Paliwo", 100]],
            "2025 ": [[None, *MONTHS], ["Paliwo", 50]],
        }
    )

    result = _import(client, {"Paliwo": {"action": "category", "name": "Paliwo"}}, content).json()

    assert result["expenses_created"] == 1
    assert client.get("/expenses").json()[0]["amount"] == "150.00"
