"""
Tests para API de BusinessPolicies — GET /api/v1/business-policies.

Usa el mismo patrón httpx.AsyncClient + ASGITransport que test_api.py.
"""

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.core.database import get_db
from app.models.business_policy import BusinessPolicy
from app.services.business_policy import BusinessPolicyService


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


class TestBusinessPoliciesAPI:
    """Tests para endpoints de políticas comerciales."""

    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient):
        """GET /api/v1/business-policies debe retornar lista vacía."""
        response = await client.get("/api/v1/business-policies")
        assert response.status_code == 200
        data = response.json()
        assert data == {"items": [], "total": 0, "page": 1, "per_page": 10}

    @pytest.mark.asyncio
    async def test_list_with_data(self, client: AsyncClient, db_session: AsyncSession):
        """Debe retornar políticas existentes."""
        service = BusinessPolicyService(db_session)
        await service.create({"name": "Policy One", "policy_type": "discount"})

        response = await client.get("/api/v1/business-policies")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_pagination(self, client: AsyncClient, db_session: AsyncSession):
        """Debe paginar correctamente."""
        service = BusinessPolicyService(db_session)
        for i in range(5):
            await service.create({"name": f"Policy {i}", "policy_type": "policy"})

        response = await client.get("/api/v1/business-policies?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_filter_by_policy_type(self, client: AsyncClient, db_session: AsyncSession):
        """Debe filtrar por policy_type."""
        service = BusinessPolicyService(db_session)
        await service.create({"name": "Discount A", "policy_type": "discount"})
        await service.create({"name": "Discount B", "policy_type": "discount"})
        await service.create({"name": "Benefit A", "policy_type": "benefit"})

        response = await client.get("/api/v1/business-policies?policy_type=benefit")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["policy_type"] == "benefit"

    @pytest.mark.asyncio
    async def test_get_by_id(self, client: AsyncClient, db_session: AsyncSession):
        """GET /api/v1/business-policies/{id} debe retornar la política."""
        service = BusinessPolicyService(db_session)
        created = await service.create({"name": "Get By ID", "policy_type": "policy"})

        response = await client.get(f"/api/v1/business-policies/{created.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get By ID"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, client: AsyncClient):
        """ID inexistente debe retornar 404."""
        import uuid
        response = await client.get(f"/api/v1/business-policies/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_active_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """GET /api/v1/business-policies/active debe retornar solo vigentes."""
        service = BusinessPolicyService(db_session)
        today = date.today()

        await service.create({"name": "Always Active", "policy_type": "policy"})
        await service.create({
            "name": "Expired",
            "policy_type": "discount",
            "effective_from": today - timedelta(days=60),
            "effective_to": today - timedelta(days=1),
        })
        await service.create({
            "name": "Future",
            "policy_type": "benefit",
            "effective_from": today + timedelta(days=10),
        })
        inactive = BusinessPolicy(
            name="Inactive", policy_type="policy", is_active=False,
        )
        db_session.add(inactive)
        await db_session.commit()

        response = await client.get("/api/v1/business-policies/active")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert "Always Active" in names
        assert "Expired" not in names
        assert "Future" not in names
        assert "Inactive" not in names

    @pytest.mark.asyncio
    async def test_active_pagination(self, client: AsyncClient, db_session: AsyncSession):
        """/active debe paginar."""
        service = BusinessPolicyService(db_session)
        for i in range(5):
            await service.create({"name": f"Active {i}", "policy_type": "policy"})

        response = await client.get("/api/v1/business-policies/active?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
