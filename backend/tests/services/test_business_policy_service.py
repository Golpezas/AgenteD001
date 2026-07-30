"""
Tests para BusinessPolicyService — lógica de negocio de políticas comerciales.
"""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_policy import BusinessPolicy
from app.services.business_policy import BusinessPolicyService


class TestBusinessPolicyService:
    """Suite de tests para BusinessPolicyService."""

    @pytest.mark.asyncio
    async def test_create_policy(self, db_session: AsyncSession):
        """Debe crear una política y retornarla con ID."""
        service = BusinessPolicyService(db_session)
        policy = await service.create({
            "name": "Test Policy",
            "policy_type": "discount",
            "value": 15.0,
            "value_type": "percentage",
        })
        assert policy.id is not None
        assert isinstance(policy.id, uuid.UUID)
        assert policy.name == "Test Policy"
        assert policy.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_type(self, db_session: AsyncSession):
        """Debe filtrar políticas por tipo."""
        service = BusinessPolicyService(db_session)
        await service.create({"name": "Discount A", "policy_type": "discount"})
        await service.create({"name": "Discount B", "policy_type": "discount"})
        await service.create({"name": "Benefit A", "policy_type": "benefit"})

        result = await service.get_by_type("discount", page=1, per_page=10)
        assert len(result["items"]) == 2
        assert all(p.policy_type == "discount" for p in result["items"])

    @pytest.mark.asyncio
    async def test_get_by_type_empty(self, db_session: AsyncSession):
        """Debe retornar lista vacía si no hay políticas de ese tipo."""
        service = BusinessPolicyService(db_session)
        result = await service.get_by_type("financing", page=1, per_page=10)
        assert len(result["items"]) == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_active_filters_by_date(self, db_session: AsyncSession):
        """get_active debe retornar solo políticas vigentes."""
        service = BusinessPolicyService(db_session)
        today = date.today()

        # Vigente: sin fechas
        await service.create({"name": "Sin Fechas", "policy_type": "policy"})
        # Vigente: con fechas vigentes
        await service.create({
            "name": "Vigente",
            "policy_type": "benefit",
            "effective_from": today - timedelta(days=30),
            "effective_to": today + timedelta(days=30),
        })
        # No vigente: expirada
        await service.create({
            "name": "Expirada",
            "policy_type": "discount",
            "effective_from": today - timedelta(days=60),
            "effective_to": today - timedelta(days=1),
        })
        # No vigente: futura
        await service.create({
            "name": "Futura",
            "policy_type": "benefit",
            "effective_from": today + timedelta(days=10),
        })
        # Inactiva
        inactive = BusinessPolicy(
            name="Inactiva",
            policy_type="policy",
            is_active=False,
        )
        db_session.add(inactive)
        await db_session.commit()

        result = await service.get_active(page=1, per_page=10)
        names = [p.name for p in result["items"]]

        assert "Sin Fechas" in names
        assert "Vigente" in names
        assert "Expirada" not in names
        assert "Futura" not in names
        assert "Inactiva" not in names

    @pytest.mark.asyncio
    async def test_get_active_paginated(self, db_session: AsyncSession):
        """get_active debe paginar correctamente."""
        service = BusinessPolicyService(db_session)
        for i in range(5):
            await service.create({
                "name": f"Policy {i}",
                "policy_type": "policy",
            })

        result = await service.get_active(page=1, per_page=2)
        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["per_page"] == 2

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        """Debe retornar políticas paginadas."""
        service = BusinessPolicyService(db_session)
        for i in range(5):
            await service.create({
                "name": f"Policy {i}",
                "policy_type": "policy",
            })

        result = await service.get_all(page=1, per_page=3)
        assert len(result["items"]) == 3
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Debe obtener una política por ID."""
        service = BusinessPolicyService(db_session)
        created = await service.create({
            "name": "Find Me",
            "policy_type": "benefit",
        })

        found = await service.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == "Find Me"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Debe retornar None para ID inexistente."""
        service = BusinessPolicyService(db_session)
        result = await service.get_by_id(uuid.uuid4())
        assert result is None
