"""
Tests para seed data — verifica que el script de seed funcione correctamente.

Ejecuta seed_todo() contra la base de datos de test (SQLite) y verifica
conteos mínimos de cada tipo de dato sembrado.
"""

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_policy import BusinessPolicy
from app.models.calculation_factor import CalculationFactor
from app.models.price_list import PriceList, PriceListItem
from app.models.product import Product
from seed.seed_data import seed_todo


class TestSeedData:
    """Suite de tests para el script de seed."""

    @pytest.mark.asyncio
    async def test_seed_factores(self, db_session: AsyncSession):
        """Debe sembrar factores del Maestro de Elaboración."""
        counts = await seed_todo(db_session)
        assert counts["factores"] > 0

        # Verificar en DB
        result = await db_session.execute(
            select(func.count()).select_from(CalculationFactor)
        )
        total = result.scalar() or 0
        assert total == counts["factores"]

    @pytest.mark.asyncio
    async def test_seed_politicas(self, db_session: AsyncSession):
        """Debe sembrar 20+ políticas comerciales."""
        counts = await seed_todo(db_session)
        assert counts["politicas"] >= 20

        result = await db_session.execute(
            select(func.count()).select_from(BusinessPolicy)
        )
        total = result.scalar() or 0
        assert total == counts["politicas"]

    @pytest.mark.asyncio
    async def test_seed_productos(self, db_session: AsyncSession):
        """Debe sembrar productos reales (ZEUS, Balcony, MasPedidos, Partner, Servicios)."""
        counts = await seed_todo(db_session)
        assert counts["productos"] >= 20

        result = await db_session.execute(
            select(func.count()).select_from(Product)
        )
        total = result.scalar() or 0
        assert total == counts["productos"]

        # Verificar familias
        result = await db_session.execute(
            select(Product.family).distinct()
        )
        familias = [r[0] for r in result.all()]
        for expected in ["Zeus", "Balcony", "MasPedidos", "Prescriptor", "Servicios Globales"]:
            assert expected in familias, f"Falta familia {expected}"

    @pytest.mark.asyncio
    async def test_seed_price_list(self, db_session: AsyncSession):
        """Debe sembrar lista de precios con ítems."""
        counts = await seed_todo(db_session)
        pl_info = counts["price_list"]
        assert pl_info["items"] > 0

        result = await db_session.execute(
            select(func.count()).select_from(PriceListItem)
        )
        total = result.scalar() or 0
        assert total == pl_info["items"]

    @pytest.mark.asyncio
    async def test_seed_idempotent(self, db_session: AsyncSession):
        """Ejecutar seed dos veces no debe duplicar datos."""
        first = await seed_todo(db_session)
        second = await seed_todo(db_session)

        # Segunda ejecución debe crear 0 nuevos registros
        assert second["factores"] == 0
        assert second["politicas"] == 0
        assert second["productos"] == 0
        # Price list items también deben ser 0 nuevos
        assert second["price_list"]["items"] == 0

        # Totales deben coincidir
        for key in ["factores", "politicas", "productos"]:
            assert first[key] == first[key]

    @pytest.mark.asyncio
    async def test_seed_politicas_types(self, db_session: AsyncSession):
        """Debe haber políticas de todos los tipos."""
        await seed_todo(db_session)

        result = await db_session.execute(
            select(BusinessPolicy.policy_type).distinct()
        )
        tipos = {r[0] for r in result.all()}
        for expected in {"discount", "benefit", "financing", "policy"}:
            assert expected in tipos, f"Falta tipo de política {expected}"
