"""
Tests para el modelo BusinessPolicy — tipos, vigencia y condiciones JSONB.
"""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_policy import BusinessPolicy


class TestBusinessPolicyModel:
    """Suite de tests para el modelo BusinessPolicy."""

    @pytest.mark.asyncio
    async def test_create_discount_policy(self, db_session: AsyncSession):
        """Debe crear un descuento porcentual."""
        policy = BusinessPolicy(
            name="Canal Digital",
            policy_type="discount",
            value=10.0,
            value_type="percentage",
        )
        db_session.add(policy)
        await db_session.commit()
        await db_session.refresh(policy)

        assert policy.id is not None
        assert isinstance(policy.id, uuid.UUID)
        assert policy.name == "Canal Digital"
        assert policy.policy_type == "discount"
        assert float(policy.value) == 10.0
        assert policy.value_type == "percentage"
        assert policy.is_active is True

    @pytest.mark.asyncio
    async def test_create_financing_policy(self, db_session: AsyncSession):
        """Debe crear un financiamiento con condiciones JSONB."""
        policy = BusinessPolicy(
            name="4 pagos sin interés",
            policy_type="financing",
            conditions={"installments": 4, "interest_free": True},
        )
        db_session.add(policy)
        await db_session.commit()
        await db_session.refresh(policy)

        assert policy.policy_type == "financing"
        assert policy.conditions == {"installments": 4, "interest_free": True}

    @pytest.mark.asyncio
    async def test_policy_with_vigencia(self, db_session: AsyncSession):
        """Debe crear una política con vigencia acotada."""
        today = date.today()
        effective_from = today - timedelta(days=30)
        effective_to = today + timedelta(days=30)

        policy = BusinessPolicy(
            name="Promoción Temporal",
            policy_type="benefit",
            value=15.0,
            value_type="percentage",
            effective_from=effective_from,
            effective_to=effective_to,
        )
        db_session.add(policy)
        await db_session.commit()
        await db_session.refresh(policy)

        assert policy.effective_from == effective_from
        assert policy.effective_to == effective_to

    @pytest.mark.asyncio
    async def test_policy_without_value(self, db_session: AsyncSession):
        """Debe crear una política sin valor (policy type)."""
        policy = BusinessPolicy(
            name="Débito Automático Mandatorio",
            policy_type="policy",
            description="El cliente debe tener débito automático",
        )
        db_session.add(policy)
        await db_session.commit()
        await db_session.refresh(policy)

        assert policy.value is None
        assert policy.value_type is None
        assert policy.description == "El cliente debe tener débito automático"

    @pytest.mark.asyncio
    async def test_client_type_filter(self, db_session: AsyncSession):
        """Debe almacenar client_type correctamente."""
        policy = BusinessPolicy(
            name="Beneficio Clientes Legacy",
            policy_type="benefit",
            value=20.0,
            value_type="percentage",
            client_type="pre-sep-2025",
        )
        db_session.add(policy)
        await db_session.commit()
        await db_session.refresh(policy)

        assert policy.client_type == "pre-sep-2025"

    @pytest.mark.asyncio
    async def test_policy_is_active_default(self, db_session: AsyncSession):
        """is_active debe ser True por defecto."""
        policy = BusinessPolicy(
            name="Política Activa por Defecto",
            policy_type="policy",
        )
        db_session.add(policy)
        await db_session.commit()
        await db_session.refresh(policy)

        assert policy.is_active is True
