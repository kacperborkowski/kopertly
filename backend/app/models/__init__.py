"""Wszystkie modele bazy danych.

Import tutaj sprawia, że `from app.models import Category` działa, a przy okazji
SQLModel „widzi” każdy model i wie, jakie tabele utworzyć.
"""

from app.models.category import Category, CategoryBase

# `__all__` to lista nazw eksportowanych przez ten moduł.
__all__ = ["Category", "CategoryBase"]
