from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlmodel import Session, col, select

from app.importers.spreadsheet import MonthlyValue
from app.models import (
    Category,
    Expense,
    ImportAction,
    ImportResult,
    ImportTarget,
    MonthlyBudget,
)
from app.months import month_range

DESCRIPTION_PREFIX = "Import z arkusza: "


class ImportMappingError(ValueError):
    pass


def import_description(label: str) -> str:
    return f"{DESCRIPTION_PREFIX}{label}"


def last_day_of_month(month: str) -> date:
    _, next_month_start = month_range(month)
    return next_month_start - timedelta(days=1)


def apply_import(
    session: Session,
    values: list[MonthlyValue],
    mapping: dict[str, ImportTarget],
) -> ImportResult:
    labels = list(dict.fromkeys(value.label for value in values))
    missing = [label for label in labels if label not in mapping]
    if missing:
        raise ImportMappingError(f"Brak przypisania dla wierszy: {missing}")

    resolver = _CategoryResolver(session)
    targets = {label: resolver.resolve(mapping[label]) for label in labels}

    result = ImportResult(
        categories_created=[],
        expenses_created=0,
        expenses_already_imported=0,
        budgets_with_income=0,
        skipped_labels=[label for label in labels if mapping[label].action == ImportAction.SKIP],
        warnings=[],
    )
    already_imported = _imported_keys(session)
    income: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for value in _sum_repeated_cells(values):
        action = mapping[value.label].action
        if action == ImportAction.SKIP:
            continue
        if value.amount < 0:
            result.warnings.append(
                f"„{value.label}”, {value.month}: kwota ujemna ({value.amount}), pominięta"
            )
            continue
        if action == ImportAction.INCOME:
            income[value.month] += value.amount
            continue
        spent_on = last_day_of_month(value.month)
        description = import_description(value.label)
        if (spent_on, description) in already_imported:
            result.expenses_already_imported += 1
            continue
        session.add(
            Expense(
                amount=value.amount,
                spent_on=spent_on,
                category_id=targets[value.label],
                description=description,
            )
        )
        already_imported.add((spent_on, description))
        result.expenses_created += 1

    for month, amount in income.items():
        budget = session.exec(select(MonthlyBudget).where(MonthlyBudget.month == month)).first()
        if budget is None:
            budget = MonthlyBudget(month=month)
        budget.income = amount
        session.add(budget)
        result.budgets_with_income += 1

    result.categories_created = resolver.created
    session.commit()
    return result


def _sum_repeated_cells(values: list[MonthlyValue]) -> list[MonthlyValue]:
    totals: dict[tuple[str, str], Decimal] = {}
    for value in values:
        key = (value.label, value.month)
        totals[key] = totals.get(key, Decimal("0.00")) + value.amount
    return [
        MonthlyValue(label=label, month=month, amount=amount)
        for (label, month), amount in totals.items()
    ]


def _imported_keys(session: Session) -> set[tuple[date, str]]:
    rows = session.exec(
        select(Expense.spent_on, Expense.description).where(
            col(Expense.description).startswith(DESCRIPTION_PREFIX)
        )
    ).all()
    return {(spent_on, description) for spent_on, description in rows if description}


class _CategoryResolver:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.by_id = {category.id: category for category in session.exec(select(Category))}
        self.by_name = {category.name.lower(): category for category in self.by_id.values()}
        self.created: list[str] = []

    def resolve(self, target: ImportTarget) -> int | None:
        if target.action != ImportAction.CATEGORY:
            return None
        if target.category_id is not None:
            if target.category_id not in self.by_id:
                raise ImportMappingError(f"Nie ma kategorii o id {target.category_id}")
            return target.category_id
        assert target.name is not None
        existing = self.by_name.get(target.name.lower())
        if existing is not None:
            return existing.id
        category = Category(name=target.name)
        self.session.add(category)
        self.session.flush()
        self.by_id[category.id] = category
        self.by_name[category.name.lower()] = category
        self.created.append(category.name)
        return category.id
