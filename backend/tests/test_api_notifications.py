"""
Tests de integración para API de Notificaciones — verifica endpoints HTTP.

Cubre los escenarios:
- Listar paginado
- Filtrar por type, category, is_read
- Marcar como leída (individual y masivo)
- 404 en notificación inexistente
- Crear notificación manual
- Force commercial check
"""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.core.database import get_db
from app.models.notification import Notification


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Reemplaza la dependencia get_db con la sesión de test."""

    async def _get_db_override():
        yield db_session

    return _get_db_override


@pytest.fixture
async def client(override_get_db):
    """Cliente HTTP asíncrono contra la app real."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def seed_notifications(db_session: AsyncSession):
    """Crea notificaciones de prueba en la BD."""
    notifs = []
    for i in range(5):
        n = Notification(
            type="system",
            category="product",
            title=f"Notificación {i}",
            severity="info",
        )
        db_session.add(n)
        notifs.append(n)
    # Una business
    n_biz = Notification(
        type="business",
        category="commercial",
        title="Alerta comercial",
        severity="warning",
    )
    db_session.add(n_biz)
    notifs.append(n_biz)

    # Una ya leída
    n_read = Notification(
        type="system",
        category="test",
        title="Ya leída",
        severity="info",
        is_read=True,
    )
    db_session.add(n_read)
    notifs.append(n_read)

    await db_session.commit()
    for n in notifs:
        await db_session.refresh(n)
    return notifs


class TestNotificationsAPI:
    """Tests para endpoints de notificaciones."""

    @pytest.mark.asyncio
    async def test_list_notifications_paginated(
        self, client: AsyncClient, seed_notifications,
    ):
        """GET /api/v1/notifications?page=1&per_page=2 debe paginar."""
        response = await client.get(
            "/api/v1/notifications?page=1&per_page=2",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 7
        assert data["page"] == 1
        assert data["per_page"] == 2

    @pytest.mark.asyncio
    async def test_list_notifications_filter_by_type(
        self, client: AsyncClient, seed_notifications,
    ):
        """GET /api/v1/notifications?type=business debe filtrar."""
        response = await client.get("/api/v1/notifications?type=business")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["type"] == "business"

    @pytest.mark.asyncio
    async def test_list_notifications_filter_unread(
        self, client: AsyncClient, seed_notifications,
    ):
        """GET /api/v1/notifications?is_read=false debe filtrar no leídas."""
        response = await client.get("/api/v1/notifications?is_read=false")
        assert response.status_code == 200
        data = response.json()
        # 7 notificaciones, 1 leída → 6 no leídas
        assert len(data["items"]) == 6
        assert all(item["is_read"] is False for item in data["items"])

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self, client: AsyncClient, seed_notifications,
    ):
        """GET /api/v1/notifications/unread-count debe retornar conteo."""
        response = await client.get("/api/v1/notifications/unread-count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 6  # 7 total - 1 leída = 6

    @pytest.mark.asyncio
    async def test_mark_as_read(
        self, client: AsyncClient, seed_notifications,
    ):
        """PATCH /api/v1/notifications/{id}/read debe marcar como leída."""
        # Obtener una notificación no leída
        list_resp = await client.get(
            "/api/v1/notifications?is_read=false&per_page=1",
        )
        notif = list_resp.json()["items"][0]
        assert notif["is_read"] is False

        # Marcarla como leída
        response = await client.patch(
            f"/api/v1/notifications/{notif['id']}/read",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True
        assert data["read_at"] is not None

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, client: AsyncClient):
        """PATCH /api/v1/notifications/{id}/read con ID inexistente → 404."""
        fake_id = uuid.uuid4()
        response = await client.patch(f"/api/v1/notifications/{fake_id}/read")
        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_mark_all_read(
        self, client: AsyncClient, seed_notifications,
    ):
        """PATCH /api/v1/notifications/read-all debe marcar todas como leídas."""
        # Verificar que hay no leídas primero
        unread_resp = await client.get("/api/v1/notifications/unread-count")
        assert unread_resp.json()["count"] > 0

        # Marcar todas como leídas
        response = await client.patch("/api/v1/notifications/read-all")
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 6  # Las 6 no leídas

        # Verificar que ya no hay no leídas
        final_resp = await client.get("/api/v1/notifications/unread-count")
        assert final_resp.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_create_manual_notification(self, client: AsyncClient):
        """POST /api/v1/notifications debe crear notificación manual."""
        payload = {
            "type": "manual",
            "category": "general",
            "title": "Aviso de mantenimiento",
            "description": "El sistema estará en mantenimiento el sábado",
            "severity": "warning",
        }
        response = await client.post("/api/v1/notifications", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "manual"
        assert data["title"] == "Aviso de mantenimiento"
        assert data["severity"] == "warning"
        assert data["is_read"] is False
        assert "id" in data

    @pytest.mark.asyncio
    async def test_force_commercial_check(self, client: AsyncClient):
        """POST /api/v1/notifications/force-check debe ejecutarse sin error."""
        response = await client.post("/api/v1/notifications/force-check")
        assert response.status_code == 200
        data = response.json()
        assert "created" in data
        assert data["created"] == 0  # Stub

    @pytest.mark.asyncio
    async def test_list_default_per_page_20(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """GET /api/v1/notifications sin parámetros debe usar default 20 por página."""
        response = await client.get("/api/v1/notifications")
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 20
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_filter_by_category(
        self, client: AsyncClient, seed_notifications,
    ):
        """GET /api/v1/notifications?category=product debe filtrar."""
        response = await client.get("/api/v1/notifications?category=product")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5  # Todas las de category=product
        assert all(item["category"] == "product" for item in data["items"])

    @pytest.mark.asyncio
    async def test_response_format_validation(
        self, client: AsyncClient, seed_notifications,
    ):
        """La respuesta debe incluir todos los campos esperados."""
        response = await client.get(
            "/api/v1/notifications?per_page=1",
        )
        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]
        expected_fields = {
            "id", "type", "category", "title", "description",
            "severity", "resource_type", "resource_id",
            "is_read", "is_dismissed", "read_at",
            "is_active", "created_at", "updated_at",
        }
        assert expected_fields.issubset(set(item.keys()))
