"""
Tests para el modelo CalculationFactor — constraints, defaults y relaciones.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.calculation_factor import CalculationFactor


class TestCalculationFactorModel:
    """Suite de tests para el modelo CalculationFactor."""

    @pytest.mark.asyncio
    async def test_create_calculation_factor(self, db_session: AsyncSession):
        """Debe crear un factor con todos los campos obligatorios."""
        factor = CalculationFactor(
            concept_key="accesos_simultaneos",
            concept_name="Accesos Simultáneos",
            technology_tier="Express",
            factor=5.0,
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        assert factor.id is not None
        assert isinstance(factor.id, uuid.UUID)
        assert factor.concept_key == "accesos_simultaneos"
        assert factor.concept_name == "Accesos Simultáneos"
        assert factor.technology_tier == "Express"
        assert float(factor.factor) == 5.0
        assert factor.is_available is True
        assert factor.is_active is True

    @pytest.mark.asyncio
    async def test_factor_requires_quote(self, db_session: AsyncSession):
        """Debe permitir factor=NULL y metadata con requires_quote."""
        factor = CalculationFactor(
            concept_key="horas_dba",
            concept_name="Horas DBA",
            technology_tier="Premium",
            factor=None,
            is_available=False,
            metadata={"requires_quote": True},
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        assert factor.factor is None
        assert factor.is_available is False
        assert factor.metadata == {"requires_quote": True}

    @pytest.mark.asyncio
    async def test_unique_constraint_concept_tier(self, db_session: AsyncSession):
        """La tupla (concept_key, technology_tier) debe ser única."""
        factor1 = CalculationFactor(
            concept_key="accesos_simultaneos",
            concept_name="Accesos Simultáneos",
            technology_tier="Express",
            factor=5.0,
        )
        db_session.add(factor1)
        await db_session.commit()

        factor2 = CalculationFactor(
            concept_key="accesos_simultaneos",
            concept_name="Accesos Simultáneos",
            technology_tier="Express",
            factor=3.0,
        )
        db_session.add(factor2)
        with pytest.raises(Exception):
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_is_available_default(self, db_session: AsyncSession):
        """is_available debe ser True por defecto."""
        factor = CalculationFactor(
            concept_key="test_default",
            concept_name="Test Default",
            technology_tier="Advanced",
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        assert factor.is_available is True

    @pytest.mark.asyncio
    async def test_factor_can_be_negative(self, db_session: AsyncSession):
        """Debe permitir factores negativos si el negocio lo requiere."""
        factor = CalculationFactor(
            concept_key="descuento_penalizacion",
            concept_name="Penalización",
            technology_tier="Premium",
            factor=-1.0,
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        assert float(factor.factor) == -1.0
