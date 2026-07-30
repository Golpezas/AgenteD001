"""
Tests para PriceList, PriceListItem y PricingRule API endpoints.

NOTA: Todos los tests están marcados como skip porque los endpoints
CRUD para PriceList/PriceListItem/PricingRule aún no están implementados.
Cuando se implementen, remover el marker @pytest.mark.skip y estos tests
deberían funcionar contra los endpoints bajo /api/v1/price-lists,
/api/v1/price-list-items y /api/v1/pricing-rules siguiendo el mismo
patrón que TestCompaniesEndpoint / TestProductsEndpoint en test_api.py.
"""

import uuid
from datetime import date

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


# ──────────────────────────────────────────────
# PriceList CRUD
# ──────────────────────────────────────────────


@pytest.mark.skip(reason="PriceList API endpoints not yet implemented — POST /api/v1/price-lists, GET, PUT, DELETE")
class TestPriceListEndpoint:
    """Tests para CRUD de PriceList.

    Endpoints esperados:
      POST   /api/v1/price-lists
      GET    /api/v1/price-lists
      GET    /api/v1/price-lists/{id}
      PUT    /api/v1/price-lists/{id}
      DELETE /api/v1/price-lists/{id}
    """

    CREATE_PAYLOAD = {
        "name": "Lista Standard Test",
        "description": "Lista de precios para testing",
    }

    @pytest.mark.asyncio
    async def test_create_price_list(self, client: AsyncClient):
        """POST /api/v1/price-lists debe crear y retornar 201."""
        response = await client.post("/api/v1/price-lists", json=self.CREATE_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Lista Standard Test"
        assert "id" in data
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_price_list_missing_name(self, client: AsyncClient):
        """POST sin name debe retornar 422."""
        response = await client.post("/api/v1/price-lists", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_price_lists(self, client: AsyncClient):
        """GET /api/v1/price-lists debe retornar lista paginada."""
        for i in range(3):
            await client.post(
                "/api/v1/price-lists",
                json={"name": f"Lista {i}"},
            )

        response = await client.get("/api/v1/price-lists?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_price_list_by_id(self, client: AsyncClient):
        """GET /api/v1/price-lists/{id} debe retornar la lista."""
        create_resp = await client.post(
            "/api/v1/price-lists", json=self.CREATE_PAYLOAD
        )
        price_list_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/price-lists/{price_list_id}")
        assert response.status_code == 200
        assert response.json()["id"] == price_list_id

    @pytest.mark.asyncio
    async def test_get_price_list_not_found(self, client: AsyncClient):
        """GET /api/v1/price-lists/{id} inexistente debe retornar 404."""
        response = await client.get(f"/api/v1/price-lists/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_price_list(self, client: AsyncClient):
        """PUT /api/v1/price-lists/{id} debe actualizar."""
        create_resp = await client.post(
            "/api/v1/price-lists", json=self.CREATE_PAYLOAD
        )
        price_list_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/price-lists/{price_list_id}",
            json={"name": "Lista Actualizada"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Lista Actualizada"

    @pytest.mark.asyncio
    async def test_delete_price_list(self, client: AsyncClient):
        """DELETE /api/v1/price-lists/{id} debe hacer soft delete."""
        create_resp = await client.post(
            "/api/v1/price-lists", json=self.CREATE_PAYLOAD
        )
        price_list_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/price-lists/{price_list_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False


# ──────────────────────────────────────────────
# PriceListItem CRUD
# ──────────────────────────────────────────────


@pytest.mark.skip(reason="PriceListItem API endpoints not yet implemented — POST /api/v1/price-list-items, GET, PUT, DELETE")
class TestPriceListItemEndpoint:
    """Tests para CRUD de PriceListItem.

    Endpoints esperados:
      POST   /api/v1/price-list-items
      GET    /api/v1/price-list-items
      GET    /api/v1/price-list-items/{id}
      PUT    /api/v1/price-list-items/{id}
      DELETE /api/v1/price-list-items/{id}
    """

    @pytest.mark.asyncio
    async def test_create_price_list_item(self, client: AsyncClient, db_session: AsyncSession):
        """POST /api/v1/price-list-items debe crear un ítem."""
        # Crear PriceList y Product primero
        pl_resp = await client.post(
            "/api/v1/price-lists",
            json={"name": "Lista con Items"},
        )
        assert pl_resp.status_code == 201
        price_list_id = pl_resp.json()["id"]

        prod_resp = await client.post(
            "/api/v1/products",
            json={"code": "ITEM-PROD-001", "name": "Producto para Item"},
        )
        assert prod_resp.status_code == 201
        product_id = prod_resp.json()["id"]

        response = await client.post(
            "/api/v1/price-list-items",
            json={
                "product_id": str(product_id),
                "price_list_id": str(price_list_id),
                "price": 1500.00,
                "currency": "ARS",
                "effective_from": str(date(2025, 1, 1)),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_id
        assert data["price_list_id"] == price_list_id
        assert float(data["price"]) == 1500.00

    @pytest.mark.asyncio
    async def test_list_price_list_items(self, client: AsyncClient):
        """GET /api/v1/price-list-items debe listar items."""
        response = await client.get("/api/v1/price-list-items?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_price_list_items_filter_by_price_list(self, client: AsyncClient):
        """GET /api/v1/price-list-items?price_list_id=... debe filtrar."""
        response = await client.get(
            f"/api/v1/price-list-items?price_list_id={uuid.uuid4()}"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_price_list_item_by_id(self, client: AsyncClient):
        """GET /api/v1/price-list-items/{id} debe retornar el ítem."""
        # Primero crear PriceList y Product
        pl_resp = await client.post(
            "/api/v1/price-lists",
            json={"name": "Lista Get Item"},
        )
        price_list_id = pl_resp.json()["id"]

        prod_resp = await client.post(
            "/api/v1/products",
            json={"code": "GET-ITEM-001", "name": "Get Item Product"},
        )
        product_id = prod_resp.json()["id"]

        create_resp = await client.post(
            "/api/v1/price-list-items",
            json={
                "product_id": str(product_id),
                "price_list_id": str(price_list_id),
                "price": 2000.00,
                "currency": "USD",
                "effective_from": str(date(2025, 6, 1)),
            },
        )
        item_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/price-list-items/{item_id}")
        assert response.status_code == 200
        assert response.json()["id"] == item_id

    @pytest.mark.asyncio
    async def test_update_price_list_item(self, client: AsyncClient):
        """PUT /api/v1/price-list-items/{id} debe actualizar el precio."""
        pl_resp = await client.post(
            "/api/v1/price-lists",
            json={"name": "Lista Update Item"},
        )
        price_list_id = pl_resp.json()["id"]

        prod_resp = await client.post(
            "/api/v1/products",
            json={"code": "UPD-ITEM-001", "name": "Update Item Product"},
        )
        product_id = prod_resp.json()["id"]

        create_resp = await client.post(
            "/api/v1/price-list-items",
            json={
                "product_id": str(product_id),
                "price_list_id": str(price_list_id),
                "price": 100.00,
                "currency": "ARS",
                "effective_from": str(date(2025, 1, 1)),
            },
        )
        item_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/price-list-items/{item_id}",
            json={"price": 250.00},
        )
        assert response.status_code == 200
        assert float(response.json()["price"]) == 250.00

    @pytest.mark.asyncio
    async def test_delete_price_list_item(self, client: AsyncClient):
        """DELETE /api/v1/price-list-items/{id} debe hacer soft delete."""
        pl_resp = await client.post(
            "/api/v1/price-lists",
            json={"name": "Lista Del Item"},
        )
        price_list_id = pl_resp.json()["id"]

        prod_resp = await client.post(
            "/api/v1/products",
            json={"code": "DEL-ITEM-001", "name": "Delete Item Product"},
        )
        product_id = prod_resp.json()["id"]

        create_resp = await client.post(
            "/api/v1/price-list-items",
            json={
                "product_id": str(product_id),
                "price_list_id": str(price_list_id),
                "price": 500.00,
                "currency": "ARS",
                "effective_from": str(date(2025, 1, 1)),
            },
        )
        item_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/price-list-items/{item_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False


# ──────────────────────────────────────────────
# PricingRule CRUD
# ──────────────────────────────────────────────


@pytest.mark.skip(reason="PricingRule API endpoints not yet implemented — POST /api/v1/pricing-rules, GET, PUT, DELETE")
class TestPricingRuleEndpoint:
    """Tests para CRUD de PricingRule.

    Endpoints esperados:
      POST   /api/v1/pricing-rules
      GET    /api/v1/pricing-rules
      GET    /api/v1/pricing-rules/{id}
      PUT    /api/v1/pricing-rules/{id}
      DELETE /api/v1/pricing-rules/{id}
    """

    CREATE_PAYLOAD = {
        "name": "Descuento Test",
        "rule_type": "discount",
        "technology_tier": "all",
        "conditions": {"channel": "digital"},
        "value": 10.0,
        "description": "10% de descuento para testing",
    }

    @pytest.mark.asyncio
    async def test_create_pricing_rule(self, client: AsyncClient):
        """POST /api/v1/pricing-rules debe crear y retornar 201."""
        response = await client.post(
            "/api/v1/pricing-rules", json=self.CREATE_PAYLOAD
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Descuento Test"
        assert data["rule_type"] == "discount"
        assert "id" in data
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_pricing_rule_missing_required(self, client: AsyncClient):
        """POST sin rule_type debe retornar 422."""
        response = await client.post(
            "/api/v1/pricing-rules",
            json={"name": "Regla Incompleta"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_pricing_rules(self, client: AsyncClient):
        """GET /api/v1/pricing-rules debe retornar lista paginada."""
        for i in range(3):
            await client.post(
                "/api/v1/pricing-rules",
                json={
                    "name": f"Regla {i}",
                    "rule_type": "discount",
                    "value": 5.0 * (i + 1),
                },
            )

        response = await client.get("/api/v1/pricing-rules?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_pricing_rules_filter_by_company(self, client: AsyncClient):
        """GET /api/v1/pricing-rules?company_id=... debe filtrar."""
        response = await client.get(
            f"/api/v1/pricing-rules?company_id={uuid.uuid4()}"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_pricing_rules_filter_by_product(self, client: AsyncClient):
        """GET /api/v1/pricing-rules?product_id=... debe filtrar."""
        response = await client.get(
            f"/api/v1/pricing-rules?product_id={uuid.uuid4()}"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_pricing_rule_by_id(self, client: AsyncClient):
        """GET /api/v1/pricing-rules/{id} debe retornar la regla."""
        create_resp = await client.post(
            "/api/v1/pricing-rules", json=self.CREATE_PAYLOAD
        )
        rule_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/pricing-rules/{rule_id}")
        assert response.status_code == 200
        assert response.json()["id"] == rule_id

    @pytest.mark.asyncio
    async def test_get_pricing_rule_not_found(self, client: AsyncClient):
        """GET /api/v1/pricing-rules/{id} inexistente debe retornar 404."""
        response = await client.get(f"/api/v1/pricing-rules/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_pricing_rule(self, client: AsyncClient):
        """PUT /api/v1/pricing-rules/{id} debe actualizar."""
        create_resp = await client.post(
            "/api/v1/pricing-rules", json=self.CREATE_PAYLOAD
        )
        rule_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/pricing-rules/{rule_id}",
            json={"value": 15.0},
        )
        assert response.status_code == 200
        assert float(response.json()["value"]) == 15.0

    @pytest.mark.asyncio
    async def test_delete_pricing_rule(self, client: AsyncClient):
        """DELETE /api/v1/pricing-rules/{id} debe hacer soft delete."""
        create_resp = await client.post(
            "/api/v1/pricing-rules", json=self.CREATE_PAYLOAD
        )
        rule_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/pricing-rules/{rule_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False
