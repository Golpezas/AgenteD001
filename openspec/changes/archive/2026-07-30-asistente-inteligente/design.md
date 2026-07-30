# Design: Asistente Inteligente — Fundación de Datos

## Technical Approach

Agregar dos modelos (`CalculationFactor`, `BusinessPolicy`) siguiendo Repository + Service Layer existente. Seed data scriptable con catálogo real. Frontend: dos páginas nuevas en patrón contenedor-presentacional. Validación de familias/categorías vía Pydantic enum en schemas.

## Architecture Decisions

### Decision: CalculationFactor como modelo separado (no extender PricingRule)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Extender PricingRule con `concept_key` | Modelo único, menos migraciones, pero rompe semántica: factor no es regla con prioridad/conditions | ❌ |
| Modelo nuevo CalculationFactor | Tupla única (concept_key, technology_tier), campos específicos (is_available, metadata), sin mezclar concerns | ✅ |

**Rationale**: PricingRule modela reglas condicionales con prioridad. CalculationFactor modela multiplicadores fijos por concepto+tier. Son dominios distintos.

### Decision: BusinessPolicy como modelo separado

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Reusar PricingRule | policy_type, client_type, effective_range no encajan en rule_type/priority | ❌ |
| Modelo nuevo BusinessPolicy | Tipado específico (value_type, client_type, vigencia), conditions JSONB para flexibilidad | ✅ |

**Rationale**: Las 20+ políticas comerciales (descuentos, beneficios, financiamiento) tienen semántica propia. Mezclarlas con reglas de pricing crearía acoplamiento innecesario.

### Decision: Validación de familia/categoría vía Pydantic enum, no DB enum

**Alternativa**: ENUM en PostgreSQL. **Decisión**: Pydantic `Literal[...]` en schemas.
**Rationale**: Agregar un ENUM en DB requiere migration compleja con ALTER TYPE. Pydantic da 422 automático y es fácil de modificar. El catálogo seed es la fuente de verdad, no una constraint DB.

### Decision: Seed data como script Python, no en migración Alembic

**Alternativa**: Seed en migration de datos. **Decisión**: Script independiente `python -m backend.seed.seed_data`.
**Rationale**: Las migraciones deben ser livianas. Seed data con ~30 productos + precios históricos + factores + políticas (>200 filas) merece su propio entrypoint. El script usa Session directamente, no Alembic.

## Data Flow

```
Frontend (price-lists) → GET /api/v1/price-list-items?product_id=X
  → ProductRepository.get_with_prices() → PriceListItem[]
  ← Product + precios vigentes + históricos

Frontend (business-rules) → GET /api/v1/business-policies?policy_type=discount
  → BusinessPolicyRepository.get_all(filters)
  ← BusinessPolicy[] paginado

Frontend (factors) → GET /api/v1/calculation-factors?technology_tier=Express
  → CalculationFactorRepository.get_all(filters)
  ← CalculationFactor[] paginado
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/calculation_factor.py` | Create | Modelo con concept_key, technology_tier, factor, is_available, metadata. UniqueConstraint(concept_key, technology_tier) |
| `backend/app/models/business_policy.py` | Create | Modelo con name, policy_type, value, value_type, conditions JSONB, client_type, effective range |
| `backend/app/models/__init__.py` | Modify | Re-exportar CalculationFactor, BusinessPolicy |
| `backend/app/schemas/calculation_factor.py` | Create | Schemas Pydantic (Create, Response, List) con filtros |
| `backend/app/schemas/business_policy.py` | Create | Schemas Pydantic con policy_type como Literal, value_type validado |
| `backend/app/schemas/__init__.py` | Modify | Re-exportar nuevos schemas |
| `backend/app/repositories/calculation_factor.py` | Create | CRUD con filtro por technology_tier, include_unavailable |
| `backend/app/repositories/business_policy.py` | Create | CRUD con filtros por policy_type, client_type, is_active |
| `backend/app/repositories/__init__.py` | Modify | Re-exportar |
| `backend/app/services/calculation_factor.py` | Create | Service con get_by_concept_and_tier() |
| `backend/app/services/business_policy.py` | Create | Service con get_by_type() |
| `backend/app/api/calculation_factors.py` | Create | Endpoints GET list (filtrable), GET by concept+tier |
| `backend/app/api/business_policies.py` | Create | Endpoints GET list (filtrable), GET by id |
| `backend/app/main.py` | Modify | Incluir routers nuevos |
| `backend/app/schemas/product.py` | Modify | family como Literal[...], category como Literal[...] |
| `backend/seed/__init__.py` | Create | Package init |
| `backend/seed/seed_data.py` | Create | Seed con productos reales, price_list_items, factores, políticas |
| `frontend/src/types/index.ts` | Modify | Agregar CalculationFactor, BusinessPolicy interfaces |
| `frontend/src/services/api.ts` | Modify | Agregar métodos si es necesario (o usar genéricos) |
| `frontend/src/pages/PriceLists.tsx` | Create | Container: lista precios por familia, histórico expandible, edición inline |
| `frontend/src/pages/BusinessRules.tsx` | Create | Container: políticas agrupadas por tipo, vista read-only |
| `frontend/src/hooks/usePriceLists.ts` | Create | Hook: fetch price_list_items con filtros |
| `frontend/src/hooks/useBusinessRules.ts` | Create | Hook: fetch policies con filtros |
| `frontend/src/components/price-lists/PriceListTable.tsx` | Create | Tabla de productos con precios actuales |
| `frontend/src/components/price-lists/PriceHistory.tsx` | Create | Expandable: histórico de precios por producto |
| `frontend/src/components/price-lists/PriceEditModal.tsx` | Create | Modal de edición de precio inline |
| `frontend/src/components/business-rules/PolicyViewer.tsx` | Create | Cards/tabla con políticas agrupadas por tipo |
| `frontend/src/components/layout/AppLayout.tsx` | Modify | Agregar items "Lista de Precios" y "Reglas de Negocio" al menú |
| `frontend/src/App.tsx` | Modify | Agregar rutas /price-lists, /business-rules |

## Interfaces / Contracts

```python
# CalculationFactor
class CalculationFactor(Base, TimestampMixin):
    __tablename__ = "calculation_factors"
    __table_args__ = (UniqueConstraint("concept_key", "technology_tier"),)
    id: UUID
    concept_key: str       # "accesos_simultaneos"
    concept_name: str      # "Accesos Simultáneos"
    technology_tier: str   # "Express" | "Advanced" | "Premium"
    factor: float | None   # null → requires_quote
    is_available: bool
    metadata: dict | None

# BusinessPolicy
class BusinessPolicy(Base, TimestampMixin):
    __tablename__ = "business_policies"
    id: UUID
    name: str
    policy_type: str       # "discount" | "benefit" | "financing" | "policy"
    description: str | None
    value: float | None
    value_type: str | None # "percentage" | "fixed_amount"
    conditions: dict | None
    client_type: str | None
    is_active: bool
    effective_from: datetime | None
    effective_to: datetime | None
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Models: constraints, defaults | pytest-asyncio, SQLite in-memory |
| Unit | Schemas: validation (family/category enum, policy_type) | Pydantic direct tests |
| Integration | CalculationFactor CRUD + unique constraint | asyncpg, test DB setup |
| Integration | BusinessPolicy CRUD + filters | asyncpg, test DB setup |
| Integration | Seed script execution | Dry-run con SQLite, contar filas |
| E2E | PriceLists page: carga, histórico, edición | Playwright / Vitest + MSW |

## Threat Matrix

N/A — No routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary changes.

## Migration / Rollout

No migration required for new models (Alembic autogenerate). Seed data via `python -m backend.seed.seed_data`. Family/category validation via Pydantic — no DB migration needed.

## Open Questions

- None — all decisions resolved from specs and existing patterns.
