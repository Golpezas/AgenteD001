# Tareas: Asistente Inteligente — Fundación de Datos

## Review Workload Forecast

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1200–1500 |
| Delivery strategy | auto-chain |
| Suggested split | PR 1 → PR 2 → PR 3 |

### Work Units

| Unit | Goal | PR | Test cmd | Harness | Rollback |
|------|------|----|----------|---------|----------|
| 1 | Models + Repos + Schemas + Migration | PR 1 → feature | `pytest tests/unit/models/ -x` | `python -c "from app.models import CalculationFactor"` | `alembic downgrade -1` |
| 2 | Services + API + Seed + Product schema | PR 2 → PR 1 | `pytest tests/integration/api/ -x` | `uvicorn app.main:app` + curl | `alembic downgrade -1` |
| 3 | Frontend pages + components + routing | PR 3 → PR 2 | `vitest run src/pages/` | `npm run dev` + browse | `git revert` commits |

## Phase 1: Modelos Backend (PR 1)

- [x] 1.1 Crear `models/calculation_factor.py` — concept_key+tier UniqueConstraint, is_available, metadata
- [x] 1.2 Crear `models/business_policy.py` — policy_type, conditions JSONB, value_type, vigencia
- [x] 1.3 `models/__init__.py` re-exportar modelos
- [x] 1.4 Crear `schemas/calculation_factor.py` — Create/Response/List con filtros
- [x] 1.5 Crear `schemas/business_policy.py` — policy_type Literal, value_type validado
- [x] 1.6 `schemas/__init__.py` re-exportar schemas
- [x] 1.7 Crear `repositories/calculation_factor.py` — CRUD + filtro technology_tier
- [x] 1.8 Crear `repositories/business_policy.py` — CRUD + filtros policy_type/is_active
- [x] 1.9 `repositories/__init__.py` re-exportar
- [x] 1.10 `alembic revision --autogenerate` + aplicar migración
- [x] 1.11 Tests: modelos (constraints) + schemas (validación enum)
- [x] 1.12 Tests: repos CRUD + unique constraint

## Phase 2: API y Seed Data (PR 2)

- [x] 2.1 Crear `services/calculation_factor.py` — get_by_concept_and_tier()
- [x] 2.2 Crear `services/business_policy.py` — get_by_type(), get_active()
- [x] 2.3 Crear `api/calculation_factors.py` — GET list filtrable, GET by concept+tier
- [x] 2.4 Crear `api/business_policies.py` — GET list filtrable, GET by id
- [x] 2.5 `main.py` incluir routers nuevos
- [x] 2.6 `schemas/product.py` — family/category como Literal
- [x] 2.7 Crear `seed/seed_data.py` — productos reales, precios, factores Maestro, 20+ políticas
- [x] 2.8 Tests: integración API (filtros, paginación, seed verification)

## Phase 3: Frontend Pages (PR 3)

- [x] 3.1 `types/index.ts` — interfaces CalculationFactor, BusinessPolicy y corregir PriceListItem
- [x] 3.2 Crear `hooks/usePriceLists.ts` — fetch price_list_items + products
- [x] 3.3 Crear `hooks/useBusinessRules.ts` — fetch policies filtrable
- [x] 3.4 Crear `pages/PriceLists.tsx` — productos por familia, precios, histórico, edición inline
- [x] 3.5 Crear `pages/BusinessRules.tsx` — políticas agrupadas por tipo, read-only
- [x] 3.6 Crear `components/price-lists/PriceListTable.tsx`
- [x] 3.7 Crear `components/price-lists/PriceHistory.tsx` — expandible
- [x] 3.8 Crear `components/price-lists/PriceEditModal.tsx`
- [x] 3.9 Crear `components/business-rules/PolicyViewer.tsx`
- [x] 3.10 `AppLayout.tsx` — items menú "Lista de Precios" / "Reglas de Negocio"
- [x] 3.11 `App.tsx` — rutas /price-lists, /business-rules
- [x] 3.12 Tests: componentes frontend (historial, edición, visualización)
