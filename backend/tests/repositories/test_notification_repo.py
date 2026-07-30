"""
Tests para NotificationRepository — CRUD y filtros específicos.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification import NotificationRepository


class TestNotificationRepository:
    """Suite de tests para NotificationRepository."""

    @pytest.mark.asyncio
    async def test_create_notification(self, db_session: AsyncSession):
        """Debe crear una notificación y retornarla con ID asignado."""
        repo = NotificationRepository(db_session)
        notif = await repo.create({
            "type": "system",
            "category": "product",
            "title": "Producto creado",
            "description": "Nuevo producto agregado",
            "severity": "info",
        })

        assert notif.id is not None
        assert isinstance(notif.id, uuid.UUID)
        assert notif.type == "system"
        assert notif.title == "Producto creado"
        assert notif.is_read is False
        assert notif.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Debe obtener una notificación por su ID."""
        repo = NotificationRepository(db_session)
        created = await repo.create({
            "type": "business",
            "category": "commercial",
            "title": "Alerta de prueba",
        })

        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.title == "Alerta de prueba"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Debe retornar None si la notificación no existe."""
        repo = NotificationRepository(db_session)
        found = await repo.get_by_id(uuid.uuid4())
        assert found is None

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        """Debe retornar notificaciones paginadas."""
        repo = NotificationRepository(db_session)
        for i in range(5):
            await repo.create({
                "type": "system",
                "category": "test",
                "title": f"Notificación {i}",
            })

        result = await repo.get_all(page=1, per_page=3)
        assert len(result["items"]) == 3
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["per_page"] == 3

    @pytest.mark.asyncio
    async def test_filter_by_type(self, db_session: AsyncSession):
        """Debe filtrar notificaciones por type."""
        repo = NotificationRepository(db_session)
        await repo.create({"type": "system", "category": "a", "title": "Sistema 1"})
        await repo.create({"type": "business", "category": "b", "title": "Negocio 1"})
        await repo.create({"type": "system", "category": "a", "title": "Sistema 2"})

        result = await repo.get_all(
            page=1,
            per_page=10,
            filters={"type": "system"},
        )
        assert len(result["items"]) == 2
        assert all(n.type == "system" for n in result["items"])

    @pytest.mark.asyncio
    async def test_filter_by_category(self, db_session: AsyncSession):
        """Debe filtrar notificaciones por categoría."""
        repo = NotificationRepository(db_session)
        await repo.create({"type": "system", "category": "product", "title": "Prod 1"})
        await repo.create({"type": "system", "category": "company", "title": "Comp 1"})
        await repo.create({"type": "system", "category": "product", "title": "Prod 2"})

        result = await repo.get_all(
            page=1,
            per_page=10,
            filters={"category": "product"},
        )
        assert len(result["items"]) == 2
        assert all(n.category == "product" for n in result["items"])

    @pytest.mark.asyncio
    async def test_filter_by_is_read(self, db_session: AsyncSession):
        """Debe filtrar notificaciones por estado de lectura."""
        repo = NotificationRepository(db_session)
        n1 = await repo.create({"type": "system", "category": "test", "title": "No leída"})
        await repo.create({"type": "system", "category": "test", "title": "Leída", "is_read": True})

        result = await repo.get_all(
            page=1,
            per_page=10,
            filters={"is_read": False},
        )
        assert len(result["items"]) == 1
        assert result["items"][0].id == n1.id

    @pytest.mark.asyncio
    async def test_filter_combined(self, db_session: AsyncSession):
        """Debe combinar múltiples filtros."""
        repo = NotificationRepository(db_session)
        await repo.create({
            "type": "system", "category": "product", "title": "Sist Prod",
            "is_read": False,
        })
        await repo.create({
            "type": "business", "category": "product", "title": "Bus Prod",
            "is_read": True,
        })
        await repo.create({
            "type": "system", "category": "company", "title": "Sist Comp",
            "is_read": False,
        })

        result = await repo.get_all(
            page=1,
            per_page=10,
            filters={"type": "system", "category": "product", "is_read": False},
        )
        assert len(result["items"]) == 1
        assert result["items"][0].title == "Sist Prod"

    @pytest.mark.asyncio
    async def test_get_unread_count(self, db_session: AsyncSession):
        """Debe retornar el conteo correcto de no leídas."""
        repo = NotificationRepository(db_session)
        await repo.create({"type": "system", "category": "test", "title": "No leída 1"})
        await repo.create({"type": "system", "category": "test", "title": "No leída 2"})
        await repo.create({
            "type": "system", "category": "test", "title": "Leída",
            "is_read": True,
        })

        count = await repo.get_unread_count()
        assert count == 2

    @pytest.mark.asyncio
    async def test_mark_as_read(self, db_session: AsyncSession):
        """Debe marcar una notificación como leída con timestamp."""
        repo = NotificationRepository(db_session)
        created = await repo.create({
            "type": "system", "category": "test", "title": "Para leer",
        })

        marked = await repo.mark_as_read(created.id)
        assert marked is not None
        assert marked.is_read is True
        assert marked.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, db_session: AsyncSession):
        """Debe retornar None al marcar una notificación inexistente."""
        repo = NotificationRepository(db_session)
        result = await repo.mark_as_read(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_all_read(self, db_session: AsyncSession):
        """Debe marcar todas las no leídas como leídas."""
        repo = NotificationRepository(db_session)
        for i in range(3):
            await repo.create({
                "type": "system", "category": "test", "title": f"No leída {i}",
            })
        await repo.create({
            "type": "system", "category": "test", "title": "Ya leída",
            "is_read": True,
        })

        updated = await repo.mark_all_read()
        assert updated == 3  # Solo las 3 no leídas

        # Verificar persistencia
        result = await repo.get_all(page=1, per_page=10, filters={"is_read": False})
        assert len(result["items"]) == 0

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session: AsyncSession):
        """Debe soportar soft delete y excluir de listados."""
        repo = NotificationRepository(db_session)
        created = await repo.create({
            "type": "system", "category": "test", "title": "A eliminar",
        })
        assert created.is_active is True

        deleted = await repo.soft_delete(created.id)
        assert deleted is not None
        assert deleted.is_active is False

        # No debe aparecer en listados por defecto
        result = await repo.get_all(page=1, per_page=10)
        ids = [n.id for n in result["items"]]
        assert created.id not in ids

    @pytest.mark.asyncio
    async def test_order_by_created_at_desc(self, db_session: AsyncSession):
        """Debe retornar notificaciones ordenadas por created_at DESC."""
        repo = NotificationRepository(db_session)
        n1 = await repo.create({"type": "system", "category": "test", "title": "Primera"})
        n2 = await repo.create({"type": "system", "category": "test", "title": "Segunda"})

        result = await repo.get_all(page=1, per_page=10)
        # Las dos notificaciones deben estar presentes
        assert len(result["items"]) == 2
        ids = [n.id for n in result["items"]]
        assert n1.id in ids
        assert n2.id in ids
