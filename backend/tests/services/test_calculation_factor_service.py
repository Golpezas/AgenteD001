"""
Tests para CalculationFactorService — lógica de negocio de factores.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calculation_factor import CalculationFactor
from app.services.calculation_factor import CalculationFactorService


class TestCalculationFactorService:
    """Suite de tests para CalculationFactorService."""

    @pytest.mark.asyncio
    async def test_create_factor(self, db_session: AsyncSession):
        """Debe crear un factor y retornarlo con ID."""
        service = CalculationFactorService(db_session)
        factor = await service.create({
            "concept_key": "test_concept",
            "concept_name": "Concepto de Prueba",
            "technology_tier": "Express",
            "factor": 5.0,
        })
        assert factor.id is not None
        assert isinstance(factor.id, uuid.UUID)
        assert float(factor.factor) == 5.0

    @pytest.mark.asyncio
    async def test_get_by_concept_and_tier_found(self, db_session: AsyncSession):
        """Debe encontrar un factor por tupla (concept_key, technology_tier)."""
        service = CalculationFactorService(db_session)
        await service.create({
            "concept_key": "mi_concepto",
            "concept_name": "Mi Concepto",
            "technology_tier": "Advanced",
            "factor": 3.0,
        })

        found = await service.get_by_concept_and_tier("mi_concepto", "Advanced")
        assert found is not None
        assert float(found.factor) == 3.0

    @pytest.mark.asyncio
    async def test_get_by_concept_and_tier_not_found(self, db_session: AsyncSession):
        """Debe retornar None si no existe la combinación."""
        service = CalculationFactorService(db_session)
        result = await service.get_by_concept_and_tier("no_existe", "Premium")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        """Debe retornar factores paginados."""
        service = CalculationFactorService(db_session)
        for i in range(5):
            await service.create({
                "concept_key": f"concept_{i}",
                "concept_name": f"Concept {i}",
                "technology_tier": "Express",
                "factor": 1.0,
            })

        result = await service.get_all(page=1, per_page=2)
        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["per_page"] == 2

    @pytest.mark.asyncio
    async def test_get_all_filter_by_technology_tier(self, db_session: AsyncSession):
        """Debe filtrar factores por technology_tier."""
        service = CalculationFactorService(db_session)
        await service.create({
            "concept_key": "express_only",
            "concept_name": "Express Only",
            "technology_tier": "Express",
            "factor": 1.0,
        })
        await service.create({
            "concept_key": "premium_only",
            "concept_name": "Premium Only",
            "technology_tier": "Premium",
            "factor": 5.0,
        })

        result = await service.get_all(technology_tier="Premium")
        assert len(result["items"]) == 1
        assert result["items"][0].concept_key == "premium_only"

    @pytest.mark.asyncio
    async def test_get_all_excludes_unavailable_by_default(self, db_session: AsyncSession):
        """Por defecto debe excluir factores no disponibles."""
        service = CalculationFactorService(db_session)
        await service.create({
            "concept_key": "available_one",
            "concept_name": "Available",
            "technology_tier": "Express",
            "factor": 1.0,
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

        result = await service.get_all()
        assert len(result["items"]) == 1
        assert result["items"][0].concept_key == "available_one"

    @pytest.mark.asyncio
    async def test_get_all_include_unavailable(self, db_session: AsyncSession):
        """include_unavailable=True debe incluir factores no disponibles."""
        service = CalculationFactorService(db_session)
        await service.create({
            "concept_key": "avail",
            "concept_name": "Available",
            "technology_tier": "Express",
            "factor": 1.0,
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

        result = await service.get_all(include_unavailable=True)
        assert len(result["items"]) == 2
