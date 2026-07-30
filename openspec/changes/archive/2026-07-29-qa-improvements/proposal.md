# Propuesta: QA Improvements

## Intención

Resolver las 6 sugerencias de mejora identificadas en la verificación de `fase-1-fundacion`: cobertura de código, tests faltantes, frontend testing, CI pipeline, consistencia del modelo Product, y rendimiento del bundle frontend.

## Alcance

### Incluye
1. **pytest-cov**: Configuración de cobertura mínima (80%) para backend
2. **PriceList endpoint tests**: Tests de API para PriceList, PriceListItem, PricingRule CRUD
3. **Vitest + React Testing Library**: Test runner frontend con jsdom + test de ejemplo
4. **CI pipeline**: GitHub Actions con pytest --cov, tsc --noEmit, vitest run
5. **company_id FK en Product**: ForeignKey a Company + migración Alembic + ajustes
6. **Code-splitting**: manualChunks en vite.config.ts (react, antd, app)

### Excluye
- Autenticación, PixelRAG avanzado, Price Engine, GAP Analysis (fases posteriores)
- Tests de integración Docker (requieren entorno completo)
- Frontend E2E testing (Cypress/Playwright — fase posterior)
- Prueba de health check degradado (DB caída)

## Capacidades

> Contracto con sdd-spec. Solo se listan cambios a nivel de especificación.

### Nuevas capacidades
- `ci-pipeline`: Pipeline CI/CD con GitHub Actions para build, test y coverage del backend y frontend

### Capacidades modificadas
- `products-crud`: R-P01 se modifica para requerir `company_id` (UUID, FK → Company) en el modelo Product. El campo pasa de opcional a requerido en creación. Los escenarios existentes se actualizan y se agrega verificación de FK.

### Sin cambios de spec
Las siguientes mejoras son puramente de configuración/herramientas y no modifican especificaciones existentes:
- pytest-cov (config)
- PriceList endpoint tests (cobertura de tests, no nuevos requisitos)
- Vitest + RTL (tooling)
- Code-splitting (build config)

## Enfoque

1. **pytest-cov**: Agregar `pytest-cov` a `requirements.txt`, configurar en `pyproject.toml` (tbd: crear si no existe), comando `pytest --cov=app --cov-report=term-missing --cov-fail-under=80`
2. **PriceList tests**: Nuevas clases `TestPriceListEndpoint`, `TestPriceListItemEndpoint`, `TestPricingRuleEndpoint` en `test_api.py`. Reutilizar fixture `client` + `db_session`. Tests: create, list, get, update, delete + filtros
3. **Vitest**: Instalar `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`. Configurar en `vite.config.ts` con `test.environment: 'jsdom'`. Agregar `App.test.tsx` básico
4. **CI**: `.github/workflows/ci.yml` con jobs: `backend` (pytest --cov) y `frontend` (tsc --noEmit + vitest run). Triggers: push y PR a main
5. **company_id FK**: Agregar columna `company_id` a `Product` (nullable para migración segura), FK → `companies.id`. Nueva revisión Alembic. Actualizar schemas (ProductCreate con `company_id` opcional por compatibilidad), services, tests existentes
6. **Code-splitting**: `build.rollupOptions.output.manualChunks` en `vite.config.ts`: `react` (react, react-dom, react-router-dom), `antd` (antd, @ant-design/icons), `vendor` (demás), `app` (código propio)

## Áreas Afectadas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `backend/requirements.txt` | Modificado | +pytest-cov |
| `backend/pyproject.toml` | Nuevo | Config coverage |
| `backend/app/models/product.py` | Modificado | +company_id FK |
| `backend/app/schemas/product.py` | Modificado | +company_id en schemas |
| `backend/app/repositories/product.py` | Modificado | Filtros por company |
| `backend/app/services/product.py` | Modificado | Validación company |
| `backend/alembic/versions/002_*` | Nuevo | Migración company_id |
| `backend/tests/test_api.py` | Modificado | +PriceList tests, ajustes Product |
| `frontend/vite.config.ts` | Modificado | +test config + manualChunks |
| `frontend/package.json` | Modificado | +vitest, RTL, jsdom |
| `frontend/src/App.test.tsx` | Nuevo | Test inicial vitest |
| `.github/workflows/ci.yml` | Nuevo | CI pipeline |
| `testsprite.config.yml` | Modificado | Posible actualización |

## Riesgos

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| company_id FK rompe tests existentes de Product | Media | Migración con columna nullable + `company_id` opcional en Create schema. Ajustar tests existentes para proveer company_id |
| Vitest + jsdom requiere configuración de mocking del router/provider | Media | Envolver componentes con MemoryRouter + ConfigProvider en test |
| CI pipeline falla si no hay secrets de DB configurados | Baja | Usar SQLite para CI o configurar service containers en GH Actions |
| Chunk splitting cambia nombres de chunks y puede afectar deploy | Baja | Verificar build output, usar `chunkFileNames` predecible |

## Plan de Rollback

1. Revertir `company_id` en Product: `git revert <commit>` + `alembic downgrade -1`
2. Revertir CI: borrar `.github/workflows/ci.yml`
3. Revertir frontend: `git revert` cambios en `vite.config.ts` y `package.json`
4. Ejecutar `pytest` para verificar que 53 tests originales pasan

## Dependencias

- Node.js 20+ (para vitest local, CI lo provee)
- Python 3.12+ (CI lo provee vía actions/setup-python)
- pytest-cov (nueva dependencia pip)

## Criterios de Éxito

- [ ] `pytest --cov=app --cov-fail-under=80` pasa (cobertura ≥80%)
- [ ] Tests de PriceList, PriceListItem, PricingRule endpoints existen y pasan
- [ ] `vitest run` pasa con al menos 1 test de componente
- [ ] CI pipeline corre exitosamente en push y PR
- [ ] `company_id` existe en Product, migración aplica y revierte limpiamente
- [ ] 53 tests originales siguen pasando tras los cambios
- [ ] Build frontend produce chunks separados (react, antd, vendor, app)
- [ ] Frontend compila sin errores (`tsc --noEmit`)
