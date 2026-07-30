"""
Seed data — productos, precios, factores y políticas comerciales.

Población inicial del esquema con datos reales extraídos de documentos
comerciales: factores del Maestro de Elaboración, productos ZEUS/Balcony/
MasPedidos/Partner, listas de precios julio 2026, y 20+ políticas.

Ejecutar:
    python -m backend.seed.seed_data

Es IDEMPOTENTE: verifica existencia antes de insertar.
"""

import asyncio
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.business_policy import BusinessPolicy
from app.models.calculation_factor import CalculationFactor
from app.models.price_list import PriceList, PriceListItem
from app.models.product import Product

logger = logging.getLogger("seed")

# ---------------------------------------------------------------------------
# Factores del Maestro de Elaboración
# ---------------------------------------------------------------------------

FACTORES_DATA = [
    # accesos_simultaneos
    {"concept_key": "accesos_simultaneos", "concept_name": "Accesos Simultáneos", "technology_tier": "Express", "factor": 1},
    {"concept_key": "accesos_simultaneos", "concept_name": "Accesos Simultáneos", "technology_tier": "Advanced", "factor": 3},
    {"concept_key": "accesos_simultaneos", "concept_name": "Accesos Simultáneos", "technology_tier": "Premium", "factor": 5},
    # accesos_virtuales
    {"concept_key": "accesos_virtuales", "concept_name": "Accesos Virtuales (RDP/App)", "technology_tier": "Express", "factor": 1},
    {"concept_key": "accesos_virtuales", "concept_name": "Accesos Virtuales (RDP/App)", "technology_tier": "Advanced", "factor": 3},
    {"concept_key": "accesos_virtuales", "concept_name": "Accesos Virtuales (RDP/App)", "technology_tier": "Premium", "factor": 5},
    # marketplaces
    {"concept_key": "marketplaces", "concept_name": "Marketplaces", "technology_tier": "Express", "factor": 1},
    {"concept_key": "marketplaces", "concept_name": "Marketplaces", "technology_tier": "Advanced", "factor": 3},
    {"concept_key": "marketplaces", "concept_name": "Marketplaces", "technology_tier": "Premium", "factor": 5},
    # alta_rs
    {"concept_key": "alta_rs", "concept_name": "Alta de Responsabilidad Sectorial", "technology_tier": "Express", "factor": 2},
    {"concept_key": "alta_rs", "concept_name": "Alta de Responsabilidad Sectorial", "technology_tier": "Advanced", "factor": 2},
    {"concept_key": "alta_rs", "concept_name": "Alta de Responsabilidad Sectorial", "technology_tier": "Premium", "factor": 2},
    # cambio_titularidad
    {"concept_key": "cambio_titularidad", "concept_name": "Cambio de Titularidad", "technology_tier": "Express", "factor": 1},
    {"concept_key": "cambio_titularidad", "concept_name": "Cambio de Titularidad", "technology_tier": "Advanced", "factor": 1},
    {"concept_key": "cambio_titularidad", "concept_name": "Cambio de Titularidad", "technology_tier": "Premium", "factor": 1},
    # tintometrico
    {"concept_key": "tintometrico_x6", "concept_name": "Tintométrico (x6 Prev)", "technology_tier": "Advanced", "factor": 6},
    {"concept_key": "tintometrico_x6", "concept_name": "Tintométrico (x6 Prev)", "technology_tier": "Premium", "factor": 6},
    {"concept_key": "tintometrico_x3", "concept_name": "Tintométrico (x3 Prev)", "technology_tier": "Express", "factor": 3},
    # usuario_base
    {"concept_key": "usuario_base", "concept_name": "Usuario Base del Sistema", "technology_tier": "Express", "factor": 1},
    {"concept_key": "usuario_base", "concept_name": "Usuario Base del Sistema", "technology_tier": "Advanced", "factor": 1},
    {"concept_key": "usuario_base", "concept_name": "Usuario Base del Sistema", "technology_tier": "Premium", "factor": 1},
    # modulo_contable
    {"concept_key": "modulo_contable", "concept_name": "Módulo Contable", "technology_tier": "Advanced", "factor": 1},
    {"concept_key": "modulo_contable", "concept_name": "Módulo Contable", "technology_tier": "Premium", "factor": 1},
    # modulo_stock
    {"concept_key": "modulo_stock", "concept_name": "Módulo Stock", "technology_tier": "Advanced", "factor": 1},
    {"concept_key": "modulo_stock", "concept_name": "Módulo Stock", "technology_tier": "Premium", "factor": 1},
    # modulo_factura_electronica
    {"concept_key": "modulo_fe", "concept_name": "Factura Electrónica", "technology_tier": "Advanced", "factor": 1},
    {"concept_key": "modulo_fe", "concept_name": "Factura Electrónica", "technology_tier": "Premium", "factor": 1},
]

# ---------------------------------------------------------------------------
# Políticas comerciales (20+)
# ---------------------------------------------------------------------------

POLITICAS_DATA = [
    # ── Discounts ──────────────────────────────────────────────────
    {
        "name": "Descuento Canal Digital",
        "policy_type": "discount",
        "description": "10% de descuento por contratación online (canal digital directo)",
        "value": 10.0,
        "value_type": "percentage",
        "client_type": "new",
    },
    {
        "name": "Descuento Pronto Pago",
        "policy_type": "discount",
        "description": "20% de descuento en la primera cuota por pago anticipado",
        "value": 20.0,
        "value_type": "percentage",
        "client_type": "all",
    },
    {
        "name": "Descuento Prime",
        "policy_type": "discount",
        "description": "15% de descuento para clientes Prime (facturación anual)",
        "value": 15.0,
        "value_type": "percentage",
        "client_type": "prime",
    },
    {
        "name": "Descuento por Referido",
        "policy_type": "discount",
        "description": "10% de descuento por cliente referido, válido por 3 meses",
        "value": 10.0,
        "value_type": "percentage",
        "conditions": {"max_duration_months": 3},
    },
    {
        "name": "Descuento Volumen Partners",
        "policy_type": "discount",
        "description": "Descuento progresivo por volumen para partners: 5% +1% por cada 10 licencias",
        "value": 5.0,
        "value_type": "percentage",
        "client_type": "partner",
        "conditions": {"increment_per_10_licenses": 1.0, "max_discount": 15.0},
    },
    {
        "name": "Descuento por Migración",
        "policy_type": "discount",
        "description": "25% de descuento en primeros 6 meses para clientes que migran desde competencia",
        "value": 25.0,
        "value_type": "percentage",
        "client_type": "new",
        "conditions": {"requires_migration_proof": True, "max_duration_months": 6},
    },
    # ── Benefits ───────────────────────────────────────────────────
    {
        "name": "Acceso a Webinars Exclusivos",
        "policy_type": "benefit",
        "description": "Acceso gratuito a webinars mensuales de capacitación y mejores prácticas",
    },
    {
        "name": "Capacitación Inicial",
        "policy_type": "benefit",
        "description": "8 horas de capacitación inicial sin cargo para nuevos clientes",
        "conditions": {"hours": 8, "delivery": "remote"},
    },
    {
        "name": "Soporte Prioritario",
        "policy_type": "benefit",
        "description": "Soporte técnico prioritario con SLA de 2 horas hábiles",
        "client_type": "premium",
        "conditions": {"sla_hours": 2, "channel": "ticket"},
    },
    {
        "name": "Soporte Estándar",
        "policy_type": "benefit",
        "description": "Soporte técnico estándar con SLA de 24 horas hábiles",
        "conditions": {"sla_hours": 24, "channel": "email"},
    },
    {
        "name": "Actualizaciones Incluidas",
        "policy_type": "benefit",
        "description": "Todas las actualizaciones menores y de seguridad incluidas en la suscripción",
    },
    {
        "name": "API Access",
        "policy_type": "benefit",
        "description": "Acceso a API pública para integraciones con sistemas externos",
        "client_type": "advanced",
        "conditions": {"rate_limit": 1000, "unit": "requests/minute"},
    },
    {
        "name": "Entorno de Testing",
        "policy_type": "benefit",
        "description": "Entorno sandbox de pruebas sin costo adicional",
        "client_type": "partner",
        "conditions": {"is_sandbox": True},
    },
    {
        "name": "Reportes Avanzados",
        "policy_type": "benefit",
        "description": "Módulo de reportes avanzados con dashboard personalizable",
        "client_type": "premium",
    },
    # ── Financing ──────────────────────────────────────────────────
    {
        "name": "Débito Automático Mandatorio",
        "policy_type": "financing",
        "description": "El pago DEBE realizarse mediante débito automático (CBU). No se aceptan otros medios.",
        "conditions": {"required": True, "method": "direct_debit"},
    },
    {
        "name": "Facturación Mensual Anticipada",
        "policy_type": "financing",
        "description": "La facturación es mensual y anticipada, con vencimiento a los 15 días",
        "conditions": {"billing_cycle": "monthly", "type": "advance", "due_days": 15},
    },
    {
        "name": "Facturación Anual con Descuento",
        "policy_type": "financing",
        "description": "Opción de facturación anual equivalente a 10 meses (2 meses de descuento)",
        "value": 16.67,
        "value_type": "percentage",
        "conditions": {"billing_cycle": "annual", "equivalent_months": 10},
    },
    {
        "name": "Plan Cuotas sin Interés",
        "policy_type": "financing",
        "description": "Hasta 6 cuotas sin interés con tarjeta de crédito seleccionada",
        "conditions": {"max_installments": 6, "interest_free": True},
    },
    {
        "name": "Ajuste por Inflación",
        "policy_type": "financing",
        "description": "Los precios se ajustan trimestralmente según índice de inflación oficial",
        "conditions": {"adjustment_frequency": "quarterly", "index": "official_inflation"},
    },
    # ── General Policies ───────────────────────────────────────────
    {
        "name": "Permanencia Mínima 6 Meses",
        "policy_type": "policy",
        "description": "Se requiere permanencia mínima de 6 meses. Cancelación anticipada genera penalidad.",
        "conditions": {"min_months": 6, "early_cancellation_fee": True},
    },
    {
        "name": "Precio Asegurado 4 Meses",
        "policy_type": "policy",
        "description": "El precio de contratación se mantiene fijo por 4 meses desde la fecha de alta",
        "conditions": {"locked_months": 4},
    },
    {
        "name": "Política de Privacidad RGPD",
        "policy_type": "policy",
        "description": "Todos los datos personales se procesan conforme a RGPD. El cliente es responsable de obtener consentimientos.",
        "conditions": {"regulation": "GDPR"},
    },
    {
        "name": "Acuerdo de Nivel de Servicio (SLA)",
        "policy_type": "policy",
        "description": "Disponibilidad del sistema: 99.5% mensual. Créditos por downtime superior.",
        "conditions": {"availability_pct": 99.5, "credits_for_downtime": True},
    },
    {
        "name": "Política de Cancelación",
        "policy_type": "policy",
        "description": "La cancelación debe notificarse con 30 días de anticipación por escrito",
        "conditions": {"notice_days": 30, "channel": "written"},
    },
    {
        "name": "Propiedad Intelectual",
        "policy_type": "policy",
        "description": "El software se licencia, no se vende. El cliente no adquiere derechos de propiedad intelectual.",
    },
]

# ---------------------------------------------------------------------------
# Productos reales
# ---------------------------------------------------------------------------

PRODUCTOS_DATA = [
    # ── ZEUS ───────────────────────────────────────────────────────
    {"code": "ZEUS-EXP-ARS", "name": "ZEUS Express (ARS)", "family": "Zeus", "category": "suscripcion"},
    {"code": "ZEUS-EXP-USD", "name": "ZEUS Express (USD)", "family": "Zeus", "category": "suscripcion"},
    {"code": "ZEUS-ADV-ARS", "name": "ZEUS Advanced (ARS)", "family": "Zeus", "category": "suscripcion"},
    {"code": "ZEUS-ADV-USD", "name": "ZEUS Advanced (USD)", "family": "Zeus", "category": "suscripcion"},
    {"code": "ZEUS-PRM-ARS", "name": "ZEUS Premium (ARS)", "family": "Zeus", "category": "suscripcion"},
    {"code": "ZEUS-PRM-USD", "name": "ZEUS Premium (USD)", "family": "Zeus", "category": "suscripcion"},
    # ── Balcony ────────────────────────────────────────────────────
    {"code": "BAL002", "name": "Balcony — Módulo Ventas", "family": "Balcony", "category": "software"},
    {"code": "BAL003", "name": "Balcony — Módulo Compras", "family": "Balcony", "category": "software"},
    {"code": "BAL004", "name": "Balcony — Módulo Stock", "family": "Balcony", "category": "software"},
    {"code": "BAL005", "name": "Balcony — Módulo Contable", "family": "Balcony", "category": "software"},
    {"code": "BAL006", "name": "Balcony — Factura Electrónica", "family": "Balcony", "category": "software"},
    {"code": "BAL007", "name": "Balcony — Módulo Producción", "family": "Balcony", "category": "software"},
    {"code": "BAL008", "name": "Balcony — RRHH", "family": "Balcony", "category": "software"},
    {"code": "BAL009", "name": "Balcony — CRM", "family": "Balcony", "category": "software"},
    # ── MasPedidos ─────────────────────────────────────────────────
    {"code": "MPE001", "name": "MasPedidos — Plan Básico", "family": "MasPedidos", "category": "suscripcion"},
    {"code": "MPE002", "name": "MasPedidos — Plan Profesional", "family": "MasPedidos", "category": "suscripcion"},
    {"code": "MPE003", "name": "MasPedidos — Plan Enterprise", "family": "MasPedidos", "category": "suscripcion"},
    # ── Prescriptor ────────────────────────────────────────────────
    {"code": "PTN-BASIC", "name": "Partner — Plan Básico", "family": "Prescriptor", "category": "suscripcion"},
    {"code": "PTN-PRO", "name": "Partner — Plan Profesional", "family": "Prescriptor", "category": "suscripcion"},
    {"code": "PTN-ENT", "name": "Partner — Plan Enterprise", "family": "Prescriptor", "category": "suscripcion"},
    # ── Servicios ──────────────────────────────────────────────────
    {"code": "SVC-IMPL", "name": "Implementación Inicial", "family": "Servicios Globales", "category": "servicio"},
    {"code": "SVC-CONS", "name": "Consultoría", "family": "Servicios Globales", "category": "consultoria"},
    {"code": "SVC-TRAIN", "name": "Capacitación", "family": "Servicios Globales", "category": "capacitacion"},
    {"code": "SVC-MIGR", "name": "Migración de Datos", "family": "Servicios Globales", "category": "servicio"},
    {"code": "SVC-CUST", "name": "Customización", "family": "Servicios Globales", "category": "consultoria"},
]

# ---------------------------------------------------------------------------
# Price list + items (julio 2026)
# ---------------------------------------------------------------------------

PRICE_LIST_NAME = "Lista Standard Julio 2026"
PRICE_LIST_EFFECTIVE_FROM = date(2026, 7, 1)
PRICE_LIST_EFFECTIVE_TO = date(2026, 7, 31)

PRICE_LIST_ITEMS_DATA = {
    "ZEUS-EXP-ARS": 45000.0,
    "ZEUS-EXP-USD": 45.0,
    "ZEUS-ADV-ARS": 85000.0,
    "ZEUS-ADV-USD": 85.0,
    "ZEUS-PRM-ARS": 150000.0,
    "ZEUS-PRM-USD": 150.0,
    "BAL002": 25000.0,
    "BAL003": 25000.0,
    "BAL004": 35000.0,
    "BAL005": 40000.0,
    "BAL006": 15000.0,
    "BAL007": 35000.0,
    "BAL008": 30000.0,
    "BAL009": 25000.0,
    "MPE001": 29900.0,
    "MPE002": 59900.0,
    "MPE003": 99900.0,
    "PTN-BASIC": 19900.0,
    "PTN-PRO": 49900.0,
    "PTN-ENT": 89900.0,
    "SVC-IMPL": 250000.0,
    "SVC-CONS": 15000.0,
    "SVC-TRAIN": 12000.0,
    "SVC-MIGR": 100000.0,
    "SVC-CUST": 18000.0,
}

MONTHLY_FAMILIES = {"Zeus", "MasPedidos", "Prescriptor"}
SERVICES_CATEGORIES = {"servicio", "consultoria", "capacitacion"}
LICENSE_CATEGORIES = {"software"}


# ---------------------------------------------------------------------------
# Funciones de seed
# ---------------------------------------------------------------------------


async def seed_factores(session: AsyncSession) -> int:
    """Siembra factores del Maestro de Elaboración."""
    count = 0
    for data in FACTORES_DATA:
        exists = await session.execute(
            select(CalculationFactor).where(
                CalculationFactor.concept_key == data["concept_key"],
                CalculationFactor.technology_tier == data["technology_tier"],
            )
        )
        if not exists.scalar_one_or_none():
            session.add(CalculationFactor(**data))
            count += 1
    await session.commit()
    return count


async def seed_politicas(session: AsyncSession) -> int:
    """Siembra políticas comerciales."""
    count = 0
    for data in POLITICAS_DATA:
        exists = await session.execute(
            select(BusinessPolicy).where(BusinessPolicy.name == data["name"])
        )
        if not exists.scalar_one_or_none():
            session.add(BusinessPolicy(**data))
            count += 1
    await session.commit()
    return count


async def seed_productos(session: AsyncSession) -> int:
    """Siembra productos."""
    count = 0
    for data in PRODUCTOS_DATA:
        exists = await session.execute(
            select(Product).where(Product.code == data["code"])
        )
        if not exists.scalar_one_or_none():
            session.add(Product(**data))
            count += 1
    await session.commit()
    return count


async def seed_price_list(session: AsyncSession) -> dict:
    """Siembra lista de precios y sus ítems."""
    # Crear o recuperar la lista de precios
    result = await session.execute(
        select(PriceList).where(PriceList.name == PRICE_LIST_NAME)
    )
    price_list = result.scalar_one_or_none()
    if not price_list:
        price_list = PriceList(
            name=PRICE_LIST_NAME,
            description="Lista de precios estándar vigente para julio 2026",
        )
        session.add(price_list)
        await session.commit()
        await session.refresh(price_list)

    # Obtener productos existentes mapeados por código
    result = await session.execute(select(Product))
    products = {p.code: p for p in result.scalars().all()}

    items_count = 0
    for code, price in PRICE_LIST_ITEMS_DATA.items():
        product = products.get(code)
        if not product:
            continue

        # Verificar si ya existe un item para este producto+fecha
        exists = await session.execute(
            select(PriceListItem).where(
                PriceListItem.product_id == product.id,
                PriceListItem.price_list_id == price_list.id,
                PriceListItem.effective_from == PRICE_LIST_EFFECTIVE_FROM,
            )
        )
        if exists.scalar_one_or_none():
            continue

        # Determinar moneda por código de producto
        currency = "USD" if code.endswith("-USD") else "ARS"

        item = PriceListItem(
            product_id=product.id,
            price_list_id=price_list.id,
            price=price,
            currency=currency,
            effective_from=PRICE_LIST_EFFECTIVE_FROM,
            effective_to=PRICE_LIST_EFFECTIVE_TO,
        )
        session.add(item)
        items_count += 1

    await session.commit()
    return {"price_list": price_list.name, "items": items_count}


async def seed_todo(session: AsyncSession) -> dict:
    """Ejecuta todos los seeds en orden y retorna conteos."""
    return {
        "factores": await seed_factores(session),
        "politicas": await seed_politicas(session),
        "productos": await seed_productos(session),
        "price_list": await seed_price_list(session),
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def main():
    """Punto de entrada para ejecución directa."""
    engine = create_async_engine(settings.database_url)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_factory() as session:
        counts = await seed_todo(session)

    await engine.dispose()

    logger.info("✅ Seed completado:")
    logger.info(f"   Factores: {counts['factores']} creados")
    logger.info(f"   Políticas: {counts['politicas']} creadas")
    logger.info(f"   Productos: {counts['productos']} creados")
    pl = counts["price_list"]
    logger.info(f"   Lista: {pl['price_list']} — {pl['items']} ítems")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
