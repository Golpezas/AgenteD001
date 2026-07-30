"""
Tests para API de CalculationFactors — GET /api/v1/calculation-factors.

Usa el mismo patrón httpx.AsyncClient + ASGITransport que test_api.py.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.core.database import get_db
from app.services.calculation_factor import CalculationFactorService


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


class TestCalculationFactorsAPI:
    """Tests para endpoints de factores de licenciamiento."""

    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient, db_session: AsyncSession):
        """GET /api/v1/calculation-factors debe retornar lista vacía."""
        response = await client.get("/api/v1/calculation-factors")
        assert response.status_code == 200
        data = response.json()
        assert data == {"items": [], "total": 0, "page": 1, "per_page": 10}

    @pytest.mark.asyncio
    async def test_list_with_data(self, client: AsyncClient, db_session: AsyncSession):
        """Debe retornar factores existentes."""
        service = CalculationFactorService(db_session)
        await service.create({
            "concept_key": "test_list",
            "concept_name": "Test List",
            "technology_tier": "Express",
            "factor": 1.0,
        })

        response = await client.get("/api/v1/calculation-factors")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["concept_key"] == "test_list"

    @pytest.mark.asyncio
    async def test_list_pagination(self, client: AsyncClient, db_session: AsyncSession):
        """Debe paginar correctamente."""
        service = CalculationFactorService(db_session)
        for i in range(5):
            await service.create({
                "concept_key": f"pag_{i}",
                "concept_name": f"Page {i}",
                "technology_tier": "Express",
                "factor": 1.0,
            })

        response = await client.get("/api/v1/calculation-factors?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2

    @pytest.mark.asyncio
    async def test_filter_by_technology_tier(self, client: AsyncClient, db_session: AsyncSession):
        """Debe filtrar por technology_tier."""
        service = CalculationFactorService(db_session)
        await service.create({
            "concept_key": "express_one",
            "concept_name": "Express",
            "technology_tier": "Express",
            "factor": 1.0,
        })
        await service.create({
            "concept_key": "premium_one",
            "concept_name": "Premium",
            "technology_tier": "Premium",
            "factor": 5.0,
        })

        response = await client.get("/api/v1/calculation-factors?technology_tier=Premium")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["technology_tier"] == "Premium"

    @pytest.mark.asyncio
    async def test_get_by_concept_key(self, client: AsyncClient, db_session: AsyncSession):
        """GET /api/v1/calculation-factors/{concept_key} debe retornar el factor."""
        service = CalculationFactorService(db_session)
        await service.create({
            "concept_key": "my_factor",
            "concept_name": "My Factor",
            "technology_tier": "Advanced",
            "factor": 3.0,
        })

        response = await client.get("/api/v1/calculation-factors/my_factor")
        assert response.status_code == 200
        data = response.json()
        assert data["concept_key"] == "my_factor"

    @pytest.mark.asyncio
    async def test_get_by_concept_key_with_tier(self, client: AsyncClient, db_session: AsyncSession):
        """Debe filtrar por concept_key + technology_tier."""
        service = CalculationFactorService(db_session)
        await service.create({
            "concept_key": "multi_tier",
            "concept_name": "Multi Tier",
            "technology_tier": "Express",
            "factor": 1.0,
        })
        await service.create({
            "concept_key": "multi_tier",
            "concept_name": "Multi Tier",
            "technology_tier": "Premium",
            "factor": 5.0,
        })

        response = await client.get("/api/v1/calculation-factors/multi_tier?technology_tier=Premium")
        assert response.status_code == 200
        data = response.json()
        assert data["technology_tier"] == "Premium"
        assert float(data["factor"]) == 5.0

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient):
        """Concept_key inexistente debe retornar 404."""
        response = await client.get("/api/v1/calculation-factors/no_existe")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_invalid_page(self, client: AsyncClient):
        """Página inválida debe retornar 422."""
        response = await client.get("/api/v1/calculation-factors?page=0")
        assert response.status_code == 422
