"""
Tests para modelos SQLAlchemy — verifica creación, atributos y relaciones.

Sigue el enfoque RED primero: estos tests describen el comportamiento
esperado de los modelos antes de su implementación completa.
"""

import uuid
from datetime import date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.product import Product
from app.models.price_list import PriceList, PriceListItem
from app.models.pricing_rule import PricingRule


class TestCompanyModel:
    """Suite de tests para el modelo Company."""

    @pytest.mark.asyncio
    async def test_create_company(self, db_session: AsyncSession):
        """Debe crear una empresa con todos los campos obligatorios."""
        company = Company(
            business_name="Tech Corp S.A.",
            cuit="30-12345678-9",
            legal_rep="Juan Pérez",
            email="contacto@techcorp.com",
            phone="+54 11 5555-1234",
            vertical="Tecnología",
            tech_tier="Advanced",
        )
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)

        assert company.id is not None
        assert isinstance(company.id, uuid.UUID)
        assert company.business_name == "Tech Corp S.A."
        assert company.cuit == "30-12345678-9"
        assert company.legal_rep == "Juan Pérez"
        assert company.is_active is True
        assert isinstance(company.created_at, datetime)
        assert isinstance(company.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_company_default_active(self, db_session: AsyncSession):
        """Una empresa nueva debe estar activa por defecto."""
        company = Company(business_name="Default Active Test")
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)

        assert company.is_active is True

    @pytest.mark.asyncio
    async def test_company_extra_data_jsonb(self, db_session: AsyncSession):
        """Debe almacenar metadatos JSONB correctamente."""
        extra = {"bitrix_id": "12345", "confluence_url": "https://confluence.example.com"}
        company = Company(business_name="Meta Corp", extra_data=extra)
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)

        assert company.extra_data == extra
        assert company.extra_data["bitrix_id"] == "12345"


class TestProductModel:
    """Suite de tests para el modelo Product."""

    @pytest.mark.asyncio
    async def test_create_product(self, db_session: AsyncSession):
        """Debe crear un producto con código único."""
        product = Product(
            code="BAL002",
            name="Balcony Plan Standard",
            family="Balcony",
            category="monthly_fee",
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        assert product.id is not None
        assert isinstance(product.id, uuid.UUID)
        assert product.code == "BAL002"
        assert product.name == "Balcony Plan Standard"
        assert product.is_active is True

    @pytest.mark.asyncio
    async def test_product_code_unique(self, db_session: AsyncSession):
        """Códigos de producto deben ser únicos."""
        product1 = Product(code="UNIQUE01", name="Producto Único 1")
        db_session.add(product1)
        await db_session.commit()

        product2 = Product(code="UNIQUE01", name="Producto Único 2")
        db_session.add(product2)
        with pytest.raises(Exception):
            await db_session.commit()
        await db_session.rollback()


class TestPriceListModel:
    """Suite de tests para modelos PriceList y PriceListItem."""

    @pytest.mark.asyncio
    async def test_create_price_list(self, db_session: AsyncSession):
        """Debe crear una lista de precios."""
        price_list = PriceList(name="Lista Standard")
        db_session.add(price_list)
        await db_session.commit()
        await db_session.refresh(price_list)

        assert price_list.id is not None
        assert price_list.name == "Lista Standard"
        assert price_list.is_active is True

    @pytest.mark.asyncio
    async def test_create_price_list_item(self, db_session: AsyncSession):
        """Debe crear un ítem de precio asociado a producto y lista."""
        product = Product(code="ITEM001", name="Producto para Item")
        db_session.add(product)
        await db_session.flush()

        price_list = PriceList(name="Lista Items")
        db_session.add(price_list)
        await db_session.flush()

        item = PriceListItem(
            product_id=product.id,
            price_list_id=price_list.id,
            price=1500.00,
            currency="ARS",
            effective_from=date(2025, 1, 1),
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.id is not None
        assert isinstance(item.id, uuid.UUID)
        assert item.product_id == product.id
        assert item.price_list_id == price_list.id
        assert float(item.price) == 1500.00
        assert item.currency == "ARS"
        assert item.is_active is True

    @pytest.mark.asyncio
    async def test_price_list_item_relationship(self, db_session: AsyncSession):
        """Debe navegar la relación PriceList → items correctamente."""
        product = Product(code="REL001", name="Relational Product")
        db_session.add(product)
        await db_session.flush()

        price_list = PriceList(name="Lista Relacional")
        db_session.add(price_list)
        await db_session.flush()

        item1 = PriceListItem(
            product_id=product.id,
            price_list_id=price_list.id,
            price=100.00,
            currency="ARS",
            effective_from=date(2025, 1, 1),
        )
        item2 = PriceListItem(
            product_id=product.id,
            price_list_id=price_list.id,
            price=200.00,
            currency="ARS",
            effective_from=date(2025, 6, 1),
        )
        db_session.add_all([item1, item2])
        await db_session.commit()

        # Navegar desde PriceList con eager loading para async
        stmt = (
            select(PriceList)
            .options(selectinload(PriceList.items))
            .where(PriceList.id == price_list.id)
        )
        result = await db_session.execute(stmt)
        loaded = result.scalar_one()
        assert len(loaded.items) == 2


class TestPricingRuleModel:
    """Suite de tests para el modelo PricingRule."""

    @pytest.mark.asyncio
    async def test_create_discount_rule(self, db_session: AsyncSession):
        """Debe crear una regla de descuento válida."""
        rule = PricingRule(
            name="Descuento Canal Digital",
            rule_type="discount",
            technology_tier="all",
            conditions={"min_products": 1, "channel": "digital"},
            value=10.00,
            description="10% de descuento para Canal Digital",
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        assert rule.id is not None
        assert isinstance(rule.id, uuid.UUID)
        assert rule.name == "Descuento Canal Digital"
        assert rule.rule_type == "discount"
        assert rule.value == 10.00
        assert rule.is_active is True
        assert rule.conditions["channel"] == "digital"

    @pytest.mark.asyncio
    async def test_create_factor_rule(self, db_session: AsyncSession):
        """Debe crear una regla de factor de licenciamiento."""
        rule = PricingRule(
            name="Factor Premium x5",
            rule_type="factor",
            technology_tier="Premium",
            conditions=None,
            value=5.0,
            description="Factor de licenciamiento x5 para tier Premium",
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        assert rule.rule_type == "factor"
        assert rule.technology_tier == "Premium"
        assert float(rule.value) == 5.0
