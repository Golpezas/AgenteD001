"""
Tests para NotificationService — lógica de negocio de notificaciones.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notification import NotificationService


class TestNotificationService:
    """Suite de tests para NotificationService."""

    @pytest.mark.asyncio
    async def test_create_notification_system(self, db_session: AsyncSession):
        """Debe crear una notificación tipo system."""
        service = NotificationService(db_session)
        notif = await service.create_notification(
            type="system",
            category="product",
            title="Producto BAL002 creado",
            description="El producto ha sido creado exitosamente",
            severity="info",
            resource_type="product",
            resource_id=str(uuid.uuid4()),
        )

        assert notif is not None
        assert notif.type == "system"
        assert notif.category == "product"
        assert notif.title == "Producto BAL002 creado"
        assert notif.severity == "info"
        assert notif.is_read is False
        assert notif.is_active is True

    @pytest.mark.asyncio
    async def test_create_notification_business(self, db_session: AsyncSession):
        """Debe crear una notificación tipo business."""
        service = NotificationService(db_session)
        notif = await service.create_notification(
            type="business",
            category="commercial",
            title="Precios próximos a vencer",
            severity="warning",
        )

        assert notif is not None
        assert notif.type == "business"
        assert notif.severity == "warning"

    @pytest.mark.asyncio
    async def test_create_notification_minimal(self, db_session: AsyncSession):
        """Debe crear notificación solo con campos obligatorios."""
        service = NotificationService(db_session)
        notif = await service.create_notification(
            type="system",
            category="test",
            title="Mínima",
        )

        assert notif is not None
        assert notif.title == "Mínima"
        assert notif.description is None
        assert notif.resource_type is None
        assert notif.resource_id is None

    @pytest.mark.asyncio
    async def test_mark_as_read(self, db_session: AsyncSession):
        """Debe marcar una notificación como leída."""
        service = NotificationService(db_session)
        created = await service.create_notification(
            type="system", category="test", title="Para leer",
        )
        assert created is not None
        assert created.is_read is False

        marked = await service.mark_as_read(created.id)
        assert marked is not None
        assert marked.is_read is True
        assert marked.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, db_session: AsyncSession):
        """Debe retornar None si la notificación no existe."""
        service = NotificationService(db_session)
        result = await service.mark_as_read(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_as_dismissed(self, db_session: AsyncSession):
        """Debe marcar una notificación como descartada."""
        service = NotificationService(db_session)
        created = await service.create_notification(
            type="system", category="test", title="Descartar",
        )
        assert created is not None
        assert created.is_dismissed is False

        dismissed = await service.mark_as_dismissed(created.id)
        assert dismissed is not None
        assert dismissed.is_dismissed is True

    @pytest.mark.asyncio
    async def test_mark_all_read(self, db_session: AsyncSession):
        """Debe marcar todas las no leídas como leídas."""
        service = NotificationService(db_session)
        for i in range(3):
            await service.create_notification(
                type="system", category="test", title=f"No leída {i}",
            )

        updated = await service.mark_all_read()
        assert updated == 3

        count = await service.get_unread_count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_unread_count(self, db_session: AsyncSession):
        """Debe retornar el conteo de no leídas."""
        service = NotificationService(db_session)
        for i in range(5):
            await service.create_notification(
                type="system", category="test", title=f"Notif {i}",
            )

        count = await service.get_unread_count()
        assert count == 5

        # Marcar 2 como leídas
        result = await service.notification_repo.get_all(page=1, per_page=10)
        for item in result["items"][:2]:
            await service.mark_as_read(item.id)

        count = await service.get_unread_count()
        assert count == 3

    @pytest.mark.asyncio
    async def test_force_commercial_check_stub(self, db_session: AsyncSession):
        """El stub de force_commercial_check debe ejecutarse sin error."""
        service = NotificationService(db_session)
        created = await service.force_commercial_check()
        assert created == 0  # Stub retorna 0

    @pytest.mark.asyncio
    async def test_create_notification_all_types(self, db_session: AsyncSession):
        """Debe crear notificaciones de todos los tipos."""
        service = NotificationService(db_session)
        for t in ("system", "business", "manual"):
            notif = await service.create_notification(
                type=t, category="test", title=f"Tipo {t}",
            )
            assert notif is not None
            assert notif.type == t
