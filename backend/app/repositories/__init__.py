"""Repositorios — capa de acceso a datos con SQLAlchemy 2.0."""

from app.repositories.base import BaseRepository
from app.repositories.company import CompanyRepository
from app.repositories.product import ProductRepository

__all__ = [
    "BaseRepository",
    "CompanyRepository",
    "ProductRepository",
]
