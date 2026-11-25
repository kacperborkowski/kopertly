"""Wszystkie modele bazy danych.

Import tutaj sprawia, że `from app.models import Category` działa, a przy okazji
SQLModel „widzi” każdy model i wie, jakie tabele utworzyć.
"""

from app.models.budget import (
    MONTH_PATTERN,
    BudgetAllocation,
    BudgetAllocationBase,
    BudgetPublic,
    BudgetSummary,
    BudgetUpsert,
    CategorySummary,
    MonthlyBudget,
    MonthlyBudgetBase,
)
from app.models.category import (
    Category,
    CategoryBase,
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
)
from app.models.expense import (
    Expense,
    ExpenseBase,
    ExpenseCreate,
    ExpensePublic,
    ExpenseUpdate,
)

# `__all__` to lista nazw eksportowanych przez ten moduł.
__all__ = [
    "MONTH_PATTERN",
    "BudgetAllocation",
    "BudgetAllocationBase",
    "BudgetPublic",
    "BudgetSummary",
    "BudgetUpsert",
    "CategorySummary",
    "Category",
    "CategoryBase",
    "CategoryCreate",
    "CategoryPublic",
    "CategoryUpdate",
    "Expense",
    "ExpenseBase",
    "ExpenseCreate",
    "ExpensePublic",
    "ExpenseUpdate",
    "MonthlyBudget",
    "MonthlyBudgetBase",
]
