# Tasks: QA Improvements

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~400–420 |
| 400-line budget risk | Low |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Tooling: pytest-cov, Vitest/RTL, CI pipeline | PR 1 | `pytest --cov=app --cov-fail-under=80` | CI workflow | Revert pyproject.toml, package.json, vite.config.ts, .github/workflows/ |
| 2 | Data: company_id FK | PR 2 | `pytest tests/test_models.py -x -k "product"` | local pytest | `alembic downgrade -1` + revert model/schema/service |
| 3 | Tests & Build: PriceList tests, StatCard test, code-splitting | PR 3 | `pytest tests/test_price_lists.py -x` | local pytest + `npm run build` | Revert test_price_lists.py, StatCard.test.tsx, vite.config.ts |

## Phase 1: Foundation

- [x] 1.1 Add `pytest-cov>=5.0.0` to `backend/requirements.txt`
- [x] 1.2 Create `backend/pyproject.toml` with cov config (`addopts = --cov=app --cov-report=term-missing --cov-fail-under=80`, exclude tests/*, migrations/*)
- [x] 1.3 Add vitest, @testing-library/react, @testing-library/jest-dom, jsdom to `frontend/package.json` devDependencies
- [x] 1.4 Add `test: { environment: 'jsdom', globals: true }` to `frontend/vite.config.ts`
- [x] 1.5 Create `.github/workflows/ci.yml` — jobs: `backend` (Python 3.12, postgres:16, pytest --cov) and `frontend` (Node 22, tsc --noEmit, vitest run); triggers: push + PR a main

## Phase 2: Data — company_id FK

- [x] 2.1 Add `company_id` (UUID, FK → companies.id, nullable) + `company` relationship to `backend/app/models/product.py`
- [x] 2.2 Add `company_id: Optional[UUID]` to Product schemas (Base, Create, Update, Response) in `backend/app/schemas/product.py`
- [x] 2.3 Validate company_id exists in `backend/app/services/product.py` create/update
- [x] 2.4 Run `alembic revision --autogenerate -m "add_company_id_to_product"` → save as `backend/alembic/versions/002_add_company_id.py`
- [x] 2.5 Adjust `backend/tests/test_models.py` — create Company + associate Product
- [x] 2.6 Adjust `backend/tests/test_api.py` — provide `company_id` in Product CREATE_PAYLOAD

## Phase 3: Testing & Build

- [x] 3.1 Create `backend/tests/test_price_lists.py` — TestPriceListEndpoint, TestPriceListItemEndpoint, TestPricingRuleEndpoint (CRUD: create, list, get, update, delete + filters)
- [x] 3.2 Create `frontend/src/components/ui/StatCard.test.tsx` — render test with RTL
- [x] 3.3 Add manualChunks to `frontend/vite.config.ts` build.rollupOptions.output (react, antd, vendor, app)
- [x] 3.4 Verify `pytest --cov=app --cov-fail-under=80` passes
- [x] 3.5 Verify `vitest run` passes
- [x] 3.6 Verify `npm run build` produces separated chunks

## Dependencies

- Phase 1 → Phase 2, 3: CI pipeline y tooling son prerequisitos para verificación
- Task 1.4 → 3.2: Vitest config necesaria para StatCard.test.tsx
- Task 1.3, 1.4 → 3.3: Code-splitting modifica mismo archivo (vite.config.ts)
- Phase 2 es independiente de Phase 3
