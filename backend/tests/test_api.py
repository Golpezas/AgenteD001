"""
Tests para API endpoints — verifica rutas HTTP.

Sigue TDD: estos tests describen el comportamiento esperado
de los endpoints antes de su implementación.
"""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.core.database import get_db


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


class TestHealthEndpoint:
    """Tests para GET /api/v1/health."""

    @pytest.mark.asyncio
    async def test_health_ok(self, client: AsyncClient, db_session: AsyncSession):
        """Debe retornar 200 con estado del sistema."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "version" in data
        assert "timestamp" in data


class TestCompaniesEndpoint:
    """Tests para CRUD de empresas."""

    CREATE_PAYLOAD = {
        "business_name": "API Test Corp",
        "cuit": "30-99999999-9",
        "email": "api@testcorp.com",
    }

    @pytest.mark.asyncio
    async def test_create_company(self, client: AsyncClient):
        """POST /api/v1/companies debe crear y retornar 201."""
        response = await client.post("/api/v1/companies", json=self.CREATE_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert data["business_name"] == "API Test Corp"
        assert "id" in data
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_company_missing_name(self, client: AsyncClient):
        """POST sin business_name debe retornar 422."""
        response = await client.post("/api/v1/companies", json={"cuit": "30-00000000-0"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_companies(self, client: AsyncClient):
        """GET /api/v1/companies debe retornar lista paginada."""
        # Crear algunas empresas
        for i in range(3):
            await client.post(
                "/api/v1/companies",
                json={"business_name": f"List Corp {i}", "cuit": f"30-{i:08d}-{i}"},
            )

        response = await client.get("/api/v1/companies?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["per_page"] == 2

    @pytest.mark.asyncio
    async def test_get_company_by_id(self, client: AsyncClient):
        """GET /api/v1/companies/{id} debe retornar la empresa."""
        create_resp = await client.post(
            "/api/v1/companies", json=self.CREATE_PAYLOAD
        )
        company_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/companies/{company_id}")
        assert response.status_code == 200
        assert response.json()["id"] == company_id

    @pytest.mark.asyncio
    async def test_get_company_not_found(self, client: AsyncClient):
        """GET /api/v1/companies/{id} con ID inexistente debe retornar 404."""
        response = await client.get(f"/api/v1/companies/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_company(self, client: AsyncClient):
        """PUT /api/v1/companies/{id} debe actualizar la empresa."""
        create_resp = await client.post(
            "/api/v1/companies", json=self.CREATE_PAYLOAD
        )
        company_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/companies/{company_id}",
            json={"business_name": "Updated Corp"},
        )
        assert response.status_code == 200
        assert response.json()["business_name"] == "Updated Corp"

    @pytest.mark.asyncio
    async def test_delete_company(self, client: AsyncClient):
        """DELETE /api/v1/companies/{id} debe hacer soft delete."""
        create_resp = await client.post(
            "/api/v1/companies", json=self.CREATE_PAYLOAD
        )
        company_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/companies/{company_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False


class TestProductsEndpoint:
    """Tests para CRUD de productos."""

    CREATE_PAYLOAD = {
        "code": "API-PROD-001",
        "name": "Producto API Test",
        "family": "Testing",
    }

    @pytest.mark.asyncio
    async def test_create_product(self, client: AsyncClient):
        """POST /api/v1/products debe crear y retornar 201."""
        response = await client.post("/api/v1/products", json=self.CREATE_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Producto API Test"
        assert "id" in data
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_products(self, client: AsyncClient):
        """GET /api/v1/products debe retornar lista paginada."""
        for i in range(3):
            await client.post(
                "/api/v1/products",
                json={"code": f"LST-{i:03d}", "name": f"Product {i}"},
            )

        response = await client.get("/api/v1/products?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, client: AsyncClient):
        """GET /api/v1/products/{id} debe retornar el producto."""
        create_resp = await client.post(
            "/api/v1/products", json=self.CREATE_PAYLOAD
        )
        product_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["id"] == product_id

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient):
        """GET /api/v1/products/{id} inexistente debe retornar 404."""
        response = await client.get(f"/api/v1/products/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product(self, client: AsyncClient):
        """PUT /api/v1/products/{id} debe actualizar."""
        create_resp = await client.post(
            "/api/v1/products", json=self.CREATE_PAYLOAD
        )
        product_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/products/{product_id}",
            json={"name": "Updated Product"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Product"

    @pytest.mark.asyncio
    async def test_delete_product(self, client: AsyncClient):
        """DELETE /api/v1/products/{id} debe hacer soft delete."""
        create_resp = await client.post(
            "/api/v1/products", json=self.CREATE_PAYLOAD
        )
        product_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False
