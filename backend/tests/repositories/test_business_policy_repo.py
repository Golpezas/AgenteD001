"""
Tests para BusinessPolicyRepository — CRUD, filtros y políticas vigentes.
"""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.business_policy import BusinessPolicyRepository


class TestBusinessPolicyRepository:
    """Suite de tests para BusinessPolicyRepository."""

    @pytest.mark.asyncio
    async def test_create_policy(self, db_session: AsyncSession):
        """Debe crear una política y retornarla con ID asignado."""
        repo = BusinessPolicyRepository(db_session)
        policy = await repo.create({
            "name": "Canal Digital",
            "policy_type": "discount",
            "value": 10.0,
            "value_type": "percentage",
        })

        assert policy.id is not None
        assert isinstance(policy.id, uuid.UUID)
        assert policy.name == "Canal Digital"
        assert policy.policy_type == "discount"
        assert float(policy.value) == 10.0
        assert policy.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Debe obtener una política por su ID."""
        repo = BusinessPolicyRepository(db_session)
        created = await repo.create({
            "name": "Get Test",
            "policy_type": "benefit",
        })

        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == "Get Test"

    @pytest.mark.asyncio
    async def test_get_by_type(self, db_session: AsyncSession):
        """Debe filtrar políticas por tipo."""
        repo = BusinessPolicyRepository(db_session)
        await repo.create({"name": "Discount 1", "policy_type": "discount"})
        await repo.create({"name": "Discount 2", "policy_type": "discount"})
        await repo.create({"name": "Benefit 1", "policy_type": "benefit"})

        discounts = await repo.get_by_type("discount")
        assert len(discounts) == 2
        assert all(p.policy_type == "discount" for p in discounts)

        benefits = await repo.get_by_type("benefit")
        assert len(benefits) == 1

    @pytest.mark.asyncio
    async def test_get_by_type_excludes_inactive(self, db_session: AsyncSession):
        """get_by_type debe excluir políticas inactivas."""
        repo = BusinessPolicyRepository(db_session)
        await repo.create({"name": "Active", "policy_type": "discount"})
        await repo.create({
            "name": "Inactive",
            "policy_type": "discount",
            "is_active": False,
        })

        result = await repo.get_by_type("discount")
        names = [p.name for p in result]
        assert "Active" in names
        assert "Inactive" not in names

    @pytest.mark.asyncio
    async def test_get_active(self, db_session: AsyncSession):
        """Debe retornar solo políticas vigentes."""
        repo = BusinessPolicyRepository(db_session)
        today = date.today()

        # Vigente: sin fechas
        await repo.create({"name": "Sin Fechas", "policy_type": "policy"})
        # Vigente: effective_from pasado, effective_to futuro
        await repo.create({
            "name": "Vigente",
            "policy_type": "benefit",
            "effective_from": today - timedelta(days=30),
            "effective_to": today + timedelta(days=30),
        })
        # No vigente: effective_to pasado
        await repo.create({
            "name": "Expirada",
            "policy_type": "discount",
            "effective_from": today - timedelta(days=60),
            "effective_to": today - timedelta(days=1),
        })
        # No vigente: effective_from futuro
        await repo.create({
            "name": "Futura",
            "policy_type": "benefit",
            "effective_from": today + timedelta(days=10),
        })
        # Inactiva (excluida por is_active filter)
        inactive = await repo.create({
            "name": "Inactiva",
            "policy_type": "policy",
            "is_active": False,
        })

        active_policies = await repo.get_active()
        names = [p.name for p in active_policies]

        assert "Sin Fechas" in names
        assert "Vigente" in names
        assert "Expirada" not in names
        assert "Futura" not in names
        assert "Inactiva" not in names

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        """Debe retornar políticas paginadas."""
        repo = BusinessPolicyRepository(db_session)
        for i in range(5):
            await repo.create({
                "name": f"Policy {i}",
                "policy_type": "policy",
            })

        result = await repo.get_all(page=1, per_page=3)
        assert len(result["items"]) == 3
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["per_page"] == 3

    @pytest.mark.asyncio
    async def test_get_all_filter_by_type(self, db_session: AsyncSession):
        """Debe filtrar por policy_type usando filters."""
        repo = BusinessPolicyRepository(db_session)
        await repo.create({"name": "Discount", "policy_type": "discount"})
        await repo.create({"name": "Financing", "policy_type": "financing"})

        result = await repo.get_all(
            page=1, per_page=10, filters={"policy_type": "financing"}
        )
        assert len(result["items"]) == 1
        assert result["items"][0].name == "Financing"

    @pytest.mark.asyncio
    async def test_update_policy(self, db_session: AsyncSession):
        """Debe actualizar una política existente."""
        repo = BusinessPolicyRepository(db_session)
        created = await repo.create({
            "name": "Original",
            "policy_type": "discount",
            "value": 5.0,
        })

        updated = await repo.update(created.id, {"name": "Updated", "value": 10.0})
        assert updated is not None
        assert updated.name == "Updated"
        assert float(updated.value) == 10.0

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session: AsyncSession):
        """Debe marcar is_active=False sin eliminar el registro."""
        repo = BusinessPolicyRepository(db_session)
        created = await repo.create({
            "name": "To Delete",
            "policy_type": "policy",
        })
        assert created.is_active is True

        deleted = await repo.soft_delete(created.id)
        assert deleted is not None
        assert deleted.is_active is False

        # No debe aparecer en get_all por defecto
        result = await repo.get_all(page=1, per_page=10)
        ids = [p.id for p in result["items"]]
        assert created.id not in ids
