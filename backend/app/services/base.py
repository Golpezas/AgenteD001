"""
Servicio base genérico — lógica de negocio con inyección de repositorio.

Los servicios encapsulan la lógica de negocio y operan
a través del repositorio correspondiente.
"""

from typing import Any, Dict, Generic, Optional, TypeVar

from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType]):
    """Servicio genérico con operaciones CRUD básicas."""

    def __init__(self, repository: BaseRepository[ModelType]):
        self.repository = repository

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Crea una nueva entidad."""
        return await self.repository.create(data)

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Obtiene una entidad por su ID."""
        return await self.repository.get_by_id(id)

    async def get_all(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Obtiene una lista paginada de entidades."""
        return await self.repository.get_all(
            page=page,
            per_page=per_page,
            filters=filters,
        )

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[ModelType]:
        """Actualiza una entidad existente."""
        return await self.repository.update(id, data)

    async def deactivate(self, id: Any) -> Optional[ModelType]:
        """Desactiva (soft delete) una entidad."""
        return await self.repository.soft_delete(id)
