"""
Schemas comunes — paginación y errores genéricos.

Define tipos reutilizables para respuestas paginadas
y formato de error uniforme.
"""

from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica."""

    items: List[T]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Formato uniforme para errores de validación."""

    detail: str

    model_config = {"from_attributes": True}
