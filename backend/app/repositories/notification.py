"""
Repositorio de Notification — operaciones CRUD con filtros específicos.
"""

from typing import Any, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Repositorio para el modelo Notification."""

    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)

    async def get_all(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene notificaciones paginadas con filtros por type, category, is_read.

        Incluye filtro soft delete por defecto (is_active=True).
        """
        query = select(self.model)

        # Filtros específicos
        if filters:
            for key, value in filters.items():
                if key == "is_read" and value is not None:
                    # is_read puede ser booleano — comparación directa
                    query = query.where(self.model.is_read.is_(value))
                else:
                    column = getattr(self.model, key, None)
                    if column is not None:
                        query = query.where(column == value)

        # Filtro soft delete por defecto
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active.is_(True))

        # Orden: por defecto created_at descendente
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

    async def get_unread_count(self) -> int:
        """Retorna la cantidad de notificaciones no leídas activas."""
        query = select(func.count()).where(
            self.model.is_read.is_(False),
            self.model.is_active.is_(True),
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def mark_all_read(self) -> int:
        """
        Marca todas las notificaciones no leídas como leídas.

        Retorna la cantidad de registros actualizados.
        """
        query = (
            select(self.model)
            .where(
                self.model.is_read.is_(False),
                self.model.is_active.is_(True),
            )
        )
        result = await self.session.execute(query)
        notifications = result.scalars().all()

        now = func.now()
        for notif in notifications:
            notif.is_read = True
            notif.read_at = now

        await self.session.commit()
        return len(notifications)

    async def mark_as_read(self, notification_id: Any) -> Optional[Notification]:
        """Marca una notificación como leída. Retorna None si no existe."""
        notif = await self.get_by_id(notification_id)
        if notif is None:
            return None

        notif.is_read = True
        notif.read_at = func.now()
        await self.session.commit()
        await self.session.refresh(notif)
        return notif
