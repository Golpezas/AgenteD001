"""
Servicio de Notification — lógica de negocio para notificaciones.

Inyectado como dependencia en servicios CRUD para registrar
eventos de sistema, y utilizado por el scheduler para crear
alertas comerciales.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification import NotificationRepository
from app.services.base import BaseService

logger = logging.getLogger("uvicorn")


class NotificationService(BaseService[Notification]):
    """Servicio para operaciones de negocio con notificaciones."""

    def __init__(self, session: AsyncSession):
        repository = NotificationRepository(session)
        super().__init__(repository)
        self.notification_repo = repository

    async def create_notification(
        self,
        type: str,
        category: str,
        title: str,
        description: str | None = None,
        severity: str = "info",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> Notification | None:
        """
        Crea una notificación con manejo de errores (fire-and-forget).

        Retorna la Notification creada o None si ocurre un error
        (para no interrumpir el flujo del servicio que la invoca).
        """
        try:
            data = {
                "type": type,
                "category": category,
                "title": title,
                "description": description,
                "severity": severity,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "is_read": False,
                "is_dismissed": False,
            }
            return await self.repository.create(data)
        except Exception as e:
            logger.error(f"Error creando notificación: {e}")
            return None

    async def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """Marca una notificación como leída."""
        return await self.notification_repo.mark_as_read(notification_id)

    async def mark_as_dismissed(self, notification_id: UUID) -> Optional[Notification]:
        """Marca una notificación como descartada."""
        return await self.repository.update(notification_id, {"is_dismissed": True})

    async def mark_all_read(self) -> int:
        """Marca todas las notificaciones activas no leídas como leídas."""
        return await self.notification_repo.mark_all_read()

    async def get_unread_count(self) -> int:
        """Retorna el conteo de notificaciones no leídas."""
        return await self.notification_repo.get_unread_count()

    async def force_commercial_check(self) -> int:
        """
        Ejecuta verificación comercial manual.

        Simula las reglas de negocio del scheduler para generar
        notificaciones business bajo demanda.
        """
        count = 0
        # En PR 1 esto es un stub — la lógica real de negocio se integrará
        # en PR 3 cuando se inyecte en servicios CRUD.
        logger.info("Verificación comercial forzada ejecutada (stub)")
        return count
