"""
Tests para CalculationFactorRepository — CRUD, unique constraint y filtros.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calculation_factor import CalculationFactor
from app.repositories.calculation_factor import CalculationFactorRepository


class TestCalculationFactorRepository:
    """Suite de tests para CalculationFactorRepository."""

    @pytest.mark.asyncio
    async def test_create_factor(self, db_session: AsyncSession):
        """Debe crear un factor y retornarlo con ID asignado."""
        repo = CalculationFactorRepository(db_session)
        factor = await repo.create({
            "concept_key": "accesos_simultaneos",
            "concept_name": "Accesos Simultáneos",
            "technology_tier": "Express",
            "factor": 5.0,
        })

        assert factor.id is not None
        assert isinstance(factor.id, uuid.UUID)
        assert factor.concept_key == "accesos_simultaneos"
        assert factor.technology_tier == "Express"
        assert float(factor.factor) == 5.0
        assert factor.is_available is True
        assert factor.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Debe obtener un factor por su ID."""
        repo = CalculationFactorRepository(db_session)
        created = await repo.create({
            "concept_key": "get_test",
            "concept_name": "Get Test",
            "technology_tier": "Advanced",
            "factor": 2.0,
        })

        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.concept_key == "get_test"

    @pytest.mark.asyncio
    async def test_get_by_concept_and_tier(self, db_session: AsyncSession):
        """Debe obtener un factor por tupla (concept_key, technology_tier)."""
        repo = CalculationFactorRepository(db_session)
        await repo.create({
            "concept_key": "unique_concept",
            "concept_name": "Unique Concept",
            "technology_tier": "Premium",
            "factor": 6.0,
        })

        found = await repo.get_by_concept_and_tier("unique_concept", "Premium")
        assert found is not None
        assert float(found.factor) == 6.0

        not_found = await repo.get_by_concept_and_tier("unique_concept", "Express")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_unique_constraint(self, db_session: AsyncSession):
        """La tupla (concept_key, technology_tier) debe ser única."""
        repo = CalculationFactorRepository(db_session)
        await repo.create({
            "concept_key": "duplicate_test",
            "concept_name": "Original",
            "technology_tier": "Express",
            "factor": 5.0,
        })

        with pytest.raises(Exception):
            await repo.create({
                "concept_key": "duplicate_test",
                "concept_name": "Duplicate",
                "technology_tier": "Express",
                "factor": 3.0,
            })

    @pytest.mark.asyncio
    async def test_get_all_filters_unavailable(self, db_session: AsyncSession):
        """get_all debe excluir factores no disponibles por defecto."""
        repo = CalculationFactorRepository(db_session)
        await repo.create({
            "concept_key": "available_one",
            "concept_name": "Available",
            "technology_tier": "Express",
            "factor": 1.0,
            "is_available": True,
        })
        # Crear uno no disponible directamente
        unavailable = CalculationFactor(
            concept_key="unavailable_one",
            concept_name="Unavailable",
            technology_tier="Express",
            factor=2.0,
            is_available=False,
        )
        db_session.add(unavailable)
        await db_session.commit()

        result = await repo.get_all(page=1, per_page=10)
        assert len(result["items"]) == 1
        assert result["items"][0].concept_key == "available_one"

    @pytest.mark.asyncio
    async def test_get_all_include_unavailable(self, db_session: AsyncSession):
        """include_unavailable=True debe incluir factores no disponibles."""
        repo = CalculationFactorRepository(db_session)
        await repo.create({
            "concept_key": "avail",
            "concept_name": "Available",
            "technology_tier": "Express",
            "factor": 1.0,
            "is_available": True,
        })
        unavailable = CalculationFactor(
            concept_key="unavail",
            concept_name="Unavailable",
            technology_tier="Express",
            factor=2.0,
            is_available=False,
        )
        db_session.add(unavailable)
        await db_session.commit()

        result = await repo.get_all(page=1, per_page=10, include_unavailable=True)
        assert len(result["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_all_filter_by_technology_tier(self, db_session: AsyncSession):
        """Debe filtrar por technology_tier usando filters."""
        repo = CalculationFactorRepository(db_session)
        await repo.create({
            "concept_key": "express_concept",
            "concept_name": "Express Concept",
            "technology_tier": "Express",
            "factor": 5.0,
        })
        await repo.create({
            "concept_key": "premium_concept",
            "concept_name": "Premium Concept",
            "technology_tier": "Premium",
            "factor": 6.0,
        })

        result = await repo.get_all(
            page=1, per_page=10, filters={"technology_tier": "Premium"}
        )
        assert len(result["items"]) == 1
        assert result["items"][0].technology_tier == "Premium"

    @pytest.mark.asyncio
    async def test_update_factor(self, db_session: AsyncSession):
        """Debe actualizar un factor existente."""
        repo = CalculationFactorRepository(db_session)
        created = await repo.create({
            "concept_key": "update_test",
            "concept_name": "Original Name",
            "technology_tier": "Advanced",
            "factor": 2.0,
        })

        updated = await repo.update(created.id, {"factor": 3.0, "concept_name": "Updated Name"})
        assert updated is not None
        assert float(updated.factor) == 3.0
        assert updated.concept_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session: AsyncSession):
        """Debe marcar is_active=False sin eliminar el registro."""
        repo = CalculationFactorRepository(db_session)
        created = await repo.create({
            "concept_key": "soft_del",
            "concept_name": "To Delete",
            "technology_tier": "Express",
            "factor": 1.0,
        })
        assert created.is_active is True

        deleted = await repo.soft_delete(created.id)
        assert deleted is not None
        assert deleted.is_active is False

        # No debe aparecer en listados por defecto
        result = await repo.get_all(page=1, per_page=10, include_unavailable=True)
        ids = [f.id for f in result["items"]]
        assert created.id not in ids
