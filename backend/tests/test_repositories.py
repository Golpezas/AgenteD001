"""
Tests para repositorios — verifica CRUD genérico y específico.

Sigue TDD: estos tests describen el comportamiento esperado
de los repositorios antes de su implementación.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.product import Product
from app.models.price_list import PriceList, PriceListItem
from app.repositories.company import CompanyRepository
from app.repositories.product import ProductRepository


class TestCompanyRepository:
    """Suite de tests para CompanyRepository."""

    @pytest.mark.asyncio
    async def test_create_company(self, db_session: AsyncSession):
        """Debe crear una empresa y retornarla con ID asignado."""
        repo = CompanyRepository(db_session)
        data = {
            "business_name": "Tech Corp S.A.",
            "cuit": "30-12345678-9",
            "email": "contacto@techcorp.com",
        }
        company = await repo.create(data)

        assert company.id is not None
        assert isinstance(company.id, uuid.UUID)
        assert company.business_name == "Tech Corp S.A."
        assert company.cuit == "30-12345678-9"
        assert company.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Debe obtener una empresa por su ID."""
        repo = CompanyRepository(db_session)
        created = await repo.create({"business_name": "Get Test Inc."})

        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.business_name == "Get Test Inc."

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Debe retornar None si la empresa no existe."""
        repo = CompanyRepository(db_session)
        fake_id = uuid.uuid4()
        found = await repo.get_by_id(fake_id)
        assert found is None

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        """Debe retornar una lista paginada de empresas activas."""
        repo = CompanyRepository(db_session)
        for i in range(5):
            await repo.create({"business_name": f"Company {i}"})

        result = await repo.get_all(page=1, per_page=3)
        assert len(result["items"]) == 3
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["per_page"] == 3

    @pytest.mark.asyncio
    async def test_update_company(self, db_session: AsyncSession):
        """Debe actualizar los campos de una empresa."""
        repo = CompanyRepository(db_session)
        created = await repo.create({"business_name": "Old Name"})

        updated = await repo.update(created.id, {"business_name": "New Name"})
        assert updated is not None
        assert updated.business_name == "New Name"

        # Verificar persistencia
        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.business_name == "New Name"

    @pytest.mark.asyncio
    async def test_update_not_found(self, db_session: AsyncSession):
        """Debe retornar None al actualizar una empresa inexistente."""
        repo = CompanyRepository(db_session)
        result = await repo.update(uuid.uuid4(), {"business_name": "Nope"})
        assert result is None

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session: AsyncSession):
        """Debe marcar is_active=False sin eliminar el registro."""
        repo = CompanyRepository(db_session)
        created = await repo.create({"business_name": "To Delete"})
        assert created.is_active is True

        deleted = await repo.soft_delete(created.id)
        assert deleted is not None
        assert deleted.is_active is False

        # No debe aparecer en listados por defecto
        result = await repo.get_all(page=1, per_page=10)
        ids = [c.id for c in result["items"]]
        assert created.id not in ids

    @pytest.mark.asyncio
    async def test_soft_delete_not_found(self, db_session: AsyncSession):
        """Debe retornar None al eliminar una empresa inexistente."""
        repo = CompanyRepository(db_session)
        result = await repo.soft_delete(uuid.uuid4())
        assert result is None


class TestProductRepository:
    """Suite de tests para ProductRepository."""

    @pytest.mark.asyncio
    async def test_create_product(self, db_session: AsyncSession):
        """Debe crear un producto y retornarlo con ID asignado."""
        repo = ProductRepository(db_session)
        product = await repo.create({
            "code": "PROD-001",
            "name": "Consultoría Premium",
            "family": "Servicios",
        })

        assert product.id is not None
        assert isinstance(product.id, uuid.UUID)
        assert product.code == "PROD-001"
        assert product.name == "Consultoría Premium"
        assert product.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Debe obtener un producto por su ID."""
        repo = ProductRepository(db_session)
        created = await repo.create({"code": "GET-001", "name": "Get Product"})

        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        """Debe retornar productos paginados."""
        repo = ProductRepository(db_session)
        for i in range(4):
            await repo.create({"code": f"PAG-{i:03d}", "name": f"Product {i}"})

        result = await repo.get_all(page=1, per_page=2)
        assert len(result["items"]) == 2
        assert result["total"] == 4

    @pytest.mark.asyncio
    async def test_update_product(self, db_session: AsyncSession):
        """Debe actualizar un producto."""
        repo = ProductRepository(db_session)
        created = await repo.create({"code": "UPD-001", "name": "Original"})

        updated = await repo.update(created.id, {"name": "Updated"})
        assert updated is not None
        assert updated.name == "Updated"

    @pytest.mark.asyncio
    async def test_soft_delete_product(self, db_session: AsyncSession):
        """Debe marcar is_active=False en un producto."""
        repo = ProductRepository(db_session)
        created = await repo.create({"code": "DEL-001", "name": "To Delete"})
        assert created.is_active is True

        deleted = await repo.soft_delete(created.id)
        assert deleted is not None
        assert deleted.is_active is False

    @pytest.mark.asyncio
    async def test_get_products_by_family(self, db_session: AsyncSession):
        """Debe filtrar productos por familia."""
        repo = ProductRepository(db_session)
        await repo.create({"code": "FAM-A1", "name": "Product A1", "family": "Alpha"})
        await repo.create({"code": "FAM-A2", "name": "Product A2", "family": "Alpha"})
        await repo.create({"code": "FAM-B1", "name": "Product B1", "family": "Beta"})

        result = await repo.get_all(page=1, per_page=10, filters={"family": "Alpha"})
        assert len(result["items"]) == 2
        assert all(p.family == "Alpha" for p in result["items"])
