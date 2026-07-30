"""
Tests para el modelo Notification — verifica creación y atributos.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class TestNotificationModel:
    """Suite de tests para el modelo Notification."""

    @pytest.mark.asyncio
    async def test_create_notification(self, db_session: AsyncSession):
        """Debe crear una notificación con todos los campos obligatorios."""
        notif = Notification(
            type="system",
            category="product",
            title="Producto creado",
            description="Se ha creado el producto BAL002",
            severity="info",
            resource_type="product",
            resource_id=str(uuid.uuid4()),
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        assert notif.id is not None
        assert isinstance(notif.id, uuid.UUID)
        assert notif.type == "system"
        assert notif.category == "product"
        assert notif.title == "Producto creado"
        assert notif.description == "Se ha creado el producto BAL002"
        assert notif.severity == "info"
        assert notif.resource_type == "product"
        assert notif.is_read is False
        assert notif.is_dismissed is False
        assert notif.read_at is None
        assert notif.is_active is True
        assert isinstance(notif.created_at, datetime)
        assert isinstance(notif.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_notification_default_read_false(self, db_session: AsyncSession):
        """Una notificación nueva debe tener is_read=False por defecto."""
        notif = Notification(
            type="business",
            category="commercial",
            title="Alerta comercial",
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        assert notif.is_read is False
        assert notif.is_dismissed is False
        assert notif.read_at is None
        assert notif.is_active is True

    @pytest.mark.asyncio
    async def test_notification_type_business(self, db_session: AsyncSession):
        """Debe crear notificación de tipo business correctamente."""
        notif = Notification(
            type="business",
            category="commercial",
            title="Precios próximos a vencer",
            description="3 productos tienen precios por vencer en menos de 5 días",
            severity="warning",
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        assert notif.type == "business"
        assert notif.severity == "warning"

    @pytest.mark.asyncio
    async def test_notification_type_manual(self, db_session: AsyncSession):
        """Debe crear notificación de tipo manual correctamente."""
        notif = Notification(
            type="manual",
            category="general",
            title="Aviso importante",
            description="Mantenimiento programado para el sábado",
            severity="info",
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        assert notif.type == "manual"

    @pytest.mark.asyncio
    async def test_notification_nullable_fields(self, db_session: AsyncSession):
        """Los campos description, resource_type, resource_id deben ser nullables."""
        notif = Notification(
            type="system",
            category="test",
            title="Notificación sin detalles",
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        assert notif.description is None
        assert notif.resource_type is None
        assert notif.resource_id is None

    @pytest.mark.asyncio
    async def test_notification_mark_as_read(self, db_session: AsyncSession):
        """Debe poder marcarse como leída con timestamp."""
        notif = Notification(
            type="system",
            category="test",
            title="Notificación para leer",
        )
        db_session.add(notif)
        await db_session.commit()

        # Marcar como leída
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(notif)

        assert notif.is_read is True
        assert notif.read_at is not None

    @pytest.mark.asyncio
    async def test_notification_soft_delete(self, db_session: AsyncSession):
        """Debe soportar soft delete (is_active=False)."""
        notif = Notification(
            type="system",
            category="test",
            title="Notificación a eliminar",
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        assert notif.is_active is True

        notif.is_active = False
        await db_session.commit()
        await db_session.refresh(notif)

        assert notif.is_active is False
