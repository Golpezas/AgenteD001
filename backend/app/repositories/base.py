"""
Repositorio base genérico — CRUD con SQLAlchemy 2.0 asíncrono.

Define operaciones comunes para todos los repositorios.
"""

from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Repositorio genérico con operaciones CRUD básicas."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Crea una nueva instancia del modelo."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Obtiene una instancia por su ID primario."""
        return await self.session.get(self.model, id)

    async def get_all(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene una lista paginada de instancias activas.

        Retorna un dict con items, total, page y per_page.
        """
        query = select(self.model)

        # Filtros
        if filters:
            for key, value in filters.items():
                column = getattr(self.model, key, None)
                if column is not None:
                    query = query.where(column == value)

        # Filtro soft delete por defecto
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active.is_(True))

        # Orden por defecto descendente por created_at
        if order_by is not None:
            query = query.order_by(order_by)
        elif hasattr(self.model, "created_at"):
            query = query.order_by(self.model.created_at.desc())

        # Total antes de paginar
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Paginación
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[ModelType]:
        """Actualiza una instancia existente. Retorna None si no existe."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def soft_delete(self, id: Any) -> Optional[ModelType]:
        """Marca is_active=False. Retorna None si no existe."""
        if not hasattr(self.model, "is_active"):
            raise AttributeError(f"{self.model.__name__} does not support soft delete")

        return await self.update(id, {"is_active": False})
