"""
Tests para servicios — verifica lógica de negocio.

Sigue TDD: estos tests describen el comportamiento esperado
de los servicios antes de su implementación.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.product import Product
from app.services.company import CompanyService
from app.services.product import ProductService


class TestCompanyService:
    """Suite de tests para CompanyService."""

    @pytest.mark.asyncio
    async def test_create_company(self, db_session: AsyncSession):
        """Debe crear una empresa válida."""
        service = CompanyService(db_session)
        data = {
            "business_name": "ServiCorp S.A.",
            "cuit": "30-87654321-0",
            "email": "info@servicorp.com",
        }
        company = await service.create(data)

        assert company.id is not None
        assert isinstance(company.id, uuid.UUID)
        assert company.business_name == "ServiCorp S.A."
        assert company.email == "info@servicorp.com"
        assert company.is_active is True

    @pytest.mark.asyncio
    async def test_update_company(self, db_session: AsyncSession):
        """Debe actualizar una empresa existente."""
        service = CompanyService(db_session)
        created = await service.create({"business_name": "Original Name"})

        updated = await service.update(created.id, {"business_name": "Updated Name"})
        assert updated is not None
        assert updated.business_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self, db_session: AsyncSession):
        """Debe retornar None si la empresa a actualizar no existe."""
        service = CompanyService(db_session)
        result = await service.update(uuid.uuid4(), {"business_name": "Nope"})
        assert result is None

    @pytest.mark.asyncio
    async def test_deactivate_company(self, db_session: AsyncSession):
        """Debe desactivar (soft delete) una empresa activa."""
        service = CompanyService(db_session)
        created = await service.create({"business_name": "Active Corp"})
        assert created.is_active is True

        deactivated = await service.deactivate(created.id)
        assert deactivated is not None
        assert deactivated.is_active is False

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent_returns_none(self, db_session: AsyncSession):
        """Debe retornar None si la empresa a desactivar no existe."""
        service = CompanyService(db_session)
        result = await service.deactivate(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Debe obtener una empresa por su ID."""
        service = CompanyService(db_session)
        created = await service.create({"business_name": "Findable Corp"})

        found = await service.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        """Debe retornar empresas paginadas."""
        service = CompanyService(db_session)
        for i in range(5):
            await service.create({"business_name": f"Company {i}"})

        result = await service.get_all(page=1, per_page=2)
        assert len(result["items"]) == 2
        assert result["total"] == 5


class TestProductService:
    """Suite de tests para ProductService."""

    @pytest.mark.asyncio
    async def test_create_product(self, db_session: AsyncSession):
        """Debe crear un producto válido."""
        service = ProductService(db_session)
        product = await service.create({
            "code": "SVC-PROD-001",
            "name": "Servicio Premium",
            "family": "Servicios",
        })

        assert product.id is not None
        assert isinstance(product.id, uuid.UUID)
        assert product.code == "SVC-PROD-001"
        assert product.name == "Servicio Premium"
        assert product.family == "Servicios"

    @pytest.mark.asyncio
    async def test_update_product(self, db_session: AsyncSession):
        """Debe actualizar un producto existente."""
        service = ProductService(db_session)
        created = await service.create({"code": "UPD-002", "name": "Original"})

        updated = await service.update(created.id, {"name": "Modified"})
        assert updated is not None
        assert updated.name == "Modified"

    @pytest.mark.asyncio
    async def test_get_products_by_family(self, db_session: AsyncSession):
        """Debe filtrar productos por familia."""
        service = ProductService(db_session)
        await service.create({"code": "FAM-1", "name": "Alpha 1", "family": "Alpha"})
        await service.create({"code": "FAM-2", "name": "Alpha 2", "family": "Alpha"})
        await service.create({"code": "FAM-3", "name": "Beta 1", "family": "Beta"})

        result = await service.get_by_family("Alpha", page=1, per_page=10)
        assert len(result["items"]) == 2
        assert all(p.family == "Alpha" for p in result["items"])

    @pytest.mark.asyncio
    async def test_deactivate_product(self, db_session: AsyncSession):
        """Debe desactivar (soft delete) un producto activo."""
        service = ProductService(db_session)
        created = await service.create({"code": "DEL-SVC", "name": "To Delete"})
        assert created.is_active is True

        deactivated = await service.deactivate(created.id)
        assert deactivated is not None
        assert deactivated.is_active is False
