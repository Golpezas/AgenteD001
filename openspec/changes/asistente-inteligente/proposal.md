# Propuesta: Asistente Inteligente — Fundación de Datos

## Intención

Construir la base de datos del motor de precios: modelar productos reales, listas de precios con vigencia histórica, factores de licenciamiento y políticas comerciales extraídas de documentos reales de la empresa. Sin esta fundación, el asistente conversacional no tendría datos con qué operar.

## Scope

### In Scope
- Modelo `CalculationFactor` para factores multiplicadores (x5, x2, x1, x6, x3) por concepto y technology tier
- Modelo `BusinessPolicy` para políticas comerciales (descuentos, beneficios, formas de pago)
- Seed data con TODOS los productos reales (ZEUS, Balcony) y precios actuales extraídos de documentos
- Vista frontend de listas de precios con precios históricos y actuales
- Vista frontend de reglas de negocio y políticas (consulta)
- Endpoints API para factores de licenciamiento y políticas

### Out of Scope
- Motor de GAP Analysis (futuro)
- Generación de propuestas PDF (futuro)
- Asistente conversacional / chatbot (futuro)
- Integración Bitrix24 / extracción de URLs (futuro)
- Task manager / notificaciones (futuro)

## Capabilities

### New Capabilities
- `pricing-engine`: Factores de licenciamiento por concepto y technology tier (Express/Advanced/Premium), cálculo de precios base con multiplicadores
- `business-policies`: Políticas comerciales, descuentos (10% Canal Digital, 20% Alianza, 15% Corporativo), beneficios (pago anual 10% OFF) y condiciones de financiamiento

### Modified Capabilities
- `products-crud` (api-productos): Extender spec con familias seed (Zeus, Balcony, MasPedidos, etc.) como valores controlados, categorías como enum, y endpoints de factores de licenciamiento

## Approach

Los modelos base ya existen (Product, PriceList, PriceListItem, PricingRule). Se agregan `CalculationFactor` y `BusinessPolicy` como modelos nuevos. Los factores se relacionan por concept_key + technology_tier. Las políticas se modelan con tipo, condiciones JSON y valor. Seed data en script Python ejecutable con `alembic upgrade head --seed`. Frontend: 2 páginas nuevas (price-lists, business-rules) siguiendo patrón contenedor-presentacional.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/calculation_factor.py` | New | Factores x5/x2/x1/x6/x3 por concepto + tier |
| `backend/app/models/business_policy.py` | New | Políticas comerciales, descuentos, beneficios |
| `backend/app/models/__init__.py` | Modified | Re-exportar nuevos modelos |
| `backend/app/schemas/` | New | Schemas Pydantic para nuevos modelos |
| `backend/app/api/` | New | Endpoints CRUD para factores y políticas |
| `backend/app/services/` | New | Service layer para cálculo de precios |
| `backend/seed/` | New | Scripts con catálogo real de productos y precios |
| `openspec/specs/api-productos/spec.md` | Modified | Agregar familias seed, categorías enum |
| `frontend/src/pages/` | New | PriceListsPage, BusinessRulesPage |
| `frontend/src/components/` | New | FactorTable, PolicyViewer, PriceListForm |

## Riesgos

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| Datos de precios desactualizados al momento de seed | Media | Versionar seed data y documentar fecha de extracción |
| Modelo de factores muy rígido para casos futuros | Baja | Usar concept_key + JSONB conditions para flexibilidad |

## Plan de Rollback

`alembic downgrade -1` para nuevas migraciones. Eliminar seed data con script de rollback. Desactivar feature flags en frontend si es necesario.

## Criterios de Éxito

- [ ] Seed data ejecutable que carga 30+ productos reales con precios
- [ ] Factores de licenciamiento consultables por concept_key + technology_tier
- [ ] Frontend muestra listas de precios con precios históricos y vigentes
- [ ] Frontend muestra políticas comerciales en vista de solo consulta
