"""Repositorios — capa de acceso a datos con SQLAlchemy 2.0."""

from app.repositories.analysis import (
    AnalysisJobRepository,
    AnalysisResultRepository,
    ScrapedSourceRepository,
)
from app.repositories.base import BaseRepository
from app.repositories.business_policy import BusinessPolicyRepository
from app.repositories.calculation_factor import CalculationFactorRepository
from app.repositories.company import CompanyRepository
from app.repositories.notification import NotificationRepository
from app.repositories.product import ProductRepository

__all__ = [
    "BaseRepository",
    "AnalysisJobRepository",
    "AnalysisResultRepository",
    "ScrapedSourceRepository",
    "BusinessPolicyRepository",
    "CalculationFactorRepository",
    "CompanyRepository",
    "NotificationRepository",
    "ProductRepository",
]
