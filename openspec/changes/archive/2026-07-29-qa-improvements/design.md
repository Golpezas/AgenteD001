# Design: QA Improvements

## Technical Approach

Seis mejoras independientes que se implementan en paralelo. El diseño sigue patrones existentes (Service/Repository, httpx+ASGITransport async tests, Pydantic v2, SQLAlchemy 2.0). No hay cambios de arquitectura — solo extensiones sobre infraestructura existente.

---

## Architecture Decisions

### 1. pytest-cov — Config

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| `pyproject.toml` | Único archivo, PyPA estándar; pytest 8+ lo soporta nativamente | ✅ **Elegido** |
| `.coveragerc` | Archivo separado, más verboso, fragmenta configuración | ❌ Descartado |
| `setup.cfg` | Deprecado como formato de configuración | ❌ Descartado |

**Exclusiones**: `*/tests/*`, `*/migrations/*`, `*/__init__.py`, `*/core/config.py` (settings), `conftest.py`.

**Comando integrado en `pyproject.toml`** bajo `[tool.pytest.ini_options]` para que `pytest --cov` funcione sin flags adicionales.

### 2. PriceList endpoint tests

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Archivo separado `test_price_lists.py` | Aísla por dominio; más archivos que gestionar | ✅ **Elegido** — consistente con separación de concerns |
| Unificar en `test_api.py` | Archivo monolítico, difícil de manteneer | ❌ Descartado |

**Fixtures reutilizadas**: `client`, `db_session` de `conftest.py`. Mismo patrón que `TestCompaniesEndpoint` / `TestProductsEndpoint`.

**Endpoints a testear** (asumiendo que los endpoints CRUD existen o se crearán):
- `POST /api/v1/price-lists`, `GET /api/v1/price-lists`, `GET /api/v1/price-lists/{id}`, `PUT /api/v1/price-lists/{id}`, `DELETE /api/v1/price-lists/{id}`
- `POST /api/v1/price-list-items`, `GET /api/v1/price-list-items`, `GET /api/v1/price-list-items/{id}`, `PUT /api/v1/price-list-items/{id}`, `DELETE /api/v1/price-list-items/{id}`
- `POST /api/v1/pricing-rules`, `GET /api/v1/pricing-rules`, `GET /api/v1/pricing-rules/{id}`, `PUT /api/v1/pricing-rules/{id}`, `DELETE /api/v1/pricing-rules/{id}`

### 3. Vitest + RTL — Config

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Config inline en `vite.config.ts` | Un solo archivo, evita duplicación; Vitest hereda plugins/resolve | ✅ **Elegido** |
| `vitest.config.ts` aparte | Archivo extra, sincronización manual con Vite | ❌ Descartado |

**Environment**: `jsdom` vía `/// <reference types="vitest" />` + `test.environment: 'jsdom'`.

**Test de ejemplo**: `StatCard` (no requiere router, no depende de providers Ant Design externos).

### 4. CI Pipeline

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| GitHub Actions | Integración nativa con GitHub, service containers PostgreSQL | ✅ **Elegido** — proyecto ya en GitHub |
| GitLab CI / CircleCI | Sin evidencia de uso en el ecosistema del proyecto | ❌ Descartado |

**Jobs**:
- `backend`: Python 3.12, service container postgres:16, `pytest --cov=app --cov-fail-under=80`
- `frontend`: Node 22, `tsc --noEmit`, `vitest run`

**Triggers**: `push` y `pull_request` a `main`.

**Cache**: `actions/cache` para `~/.cache/pip` y `~/.npm`. Estrategia de restore como fallback para evitar bloqueos de caché faltante.

### 5. company_id FK en Product

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| nullable + opcional en Create | Migración segura sin romper tests existentes; se vuelve requerido en Fase 2 | ✅ **Elegido** |
| NOT NULL desde el inicio | Rompe todos los tests existentes sin datos seed | ❌ Descartado |

**Modelo**: `company_id: Mapped[uuid.UUID | None]` columna `Uuid`, `ForeignKey("companies.id")`, nullable.

**Schema**: `Optional[UUID] = None` en `ProductCreate` y `ProductUpdate`. `company_id: UUID | None` en `ProductResponse`.

**Migración**: `alembic revision --autogenerate -m "add_company_id_to_product"`. Downgrade elimina la columna.

**Tests**: Ajustar `test_models.py` (crear Company + asociar) y `test_api.py` (proveer `company_id` en `CREATE_PAYLOAD`).

### 6. Code-splitting

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| `manualChunks` con función por módulo | Control granular, IDs predecibles, separación clara | ✅ **Elegido** |
| `splitChunks` automático | Sin control sobre nombres ni agrupación | ❌ Descartado |

**Estrategia**: función que inspecciona `moduleId` en `build.rollupOptions.output.manualChunks`:
- `node_modules/react*/` → `vendor-react`
- `node_modules/antd*/` o `@ant-design/` → `vendor-antd`
- `node_modules/` → `vendor` (resto)
- `src/` → `app`
- Default → `vendor`

---

## Data Flow — company_id FK

```
ProductCreate (company_id: Optional[UUID])
    │
    ▼
POST /api/v1/products
    │
    ▼
ProductService.create(data)
    │
    ▼
ProductRepository.create(data)
    │
    ▼
Product model (company_id FK → companies.id)
    │
    ▼
ProductResponse (company_id: UUID | None)
```

---

## File Changes

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `backend/pyproject.toml` | **Crear** | Config pytest-cov (addopts, exclude, cov-fail-under=80) |
| `backend/requirements.txt` | Modificar | +`pytest-cov>=5.0.0` |
| `backend/app/models/product.py` | Modificar | +`company_id` FK column + relationship |
| `backend/app/schemas/product.py` | Modificar | +`company_id: Optional[UUID]` en ProductBase/ProductCreate/ProductUpdate/ProductResponse |
| `backend/app/services/product.py` | Modificar | Validar company_id existe en create/update |
| `backend/app/repositories/product.py` | Modificar | (si hay filtros por company) |
| `backend/alembic/versions/002_add_company_id.py` | **Crear** | Migración autogenerated |
| `backend/tests/test_api.py` | Modificar | Ajustar CREATE_PAYLOAD de Product para incluir `company_id` |
| `backend/tests/test_models.py` | Modificar | Ajustar tests de Product para crear Company asociada |
| `backend/tests/test_price_lists.py` | **Crear** | Tests CRUD para PriceList, PriceListItem, PricingRule endpoints |
| `frontend/vite.config.ts` | Modificar | +Vitest config + manualChunks code-splitting |
| `frontend/package.json` | Modificar | +vitest, @testing-library/react, @testing-library/jest-dom, jsdom |
| `frontend/tsconfig.json` | Modificar | (opcional) ajustar types para vitest globals |
| `frontend/src/components/ui/StatCard.test.tsx` | **Crear** | Test de ejemplo con RTL |
| `.github/workflows/ci.yml` | **Crear** | Pipeline CI con jobs backend + frontend |

---

## Interfaces / Contracts

### Product model — company_id

```python
# Product model (addition)
company_id: Mapped[uuid.UUID | None] = mapped_column(
    Uuid,
    ForeignKey("companies.id", ondelete="SET NULL"),
    nullable=True,
)
company: Mapped["Company | None"] = relationship(backref="products")
```

### Product schemas — company_id

```python
# ProductBase (addition)
company_id: Optional[UUID] = None

# ProductResponse (addition)
company_id: UUID | None
```

---

## Testing Strategy

| Capa | Qué testear | Enfoque |
|------|-------------|---------|
| Unit (backend) | Product model con company_id FK | Crear Company + Product asociado, verificar FK |
| Unit (backend) | PriceList/Item/Rule models | Tests existentes en `test_models.py` (ya cubiertos) |
| Integration (backend) | Product endpoints con company_id | POST/GET/PUT/DELETE, proveer company_id existente y uno inexistente (422) |
| Integration (backend) | PriceList/Item/Rule endpoints | CRUD completo siguiendo patrón de Companies/Products |
| Coverage (backend) | `pytest --cov=app --cov-fail-under=80` | Todos los módulos de `app/` excluyendo tests/migrations |
| Unit (frontend) | StatCard render | RTL + vitest, renderizado con props, snapshot básico |
| Build (frontend) | `tsc --noEmit` | Sin errores de tipo |
| Build (frontend) | Code-splitting | `vite build` produce chunks `vendor-react`, `vendor-antd`, `vendor`, `app` |

---

## Threat Matrix

**N/A** — Este diseño no modifica routing, shell commands, subprocesses, VCS/PR automation, executable-file classification, ni process-integration boundaries dentro de la aplicación. El CI pipeline ejecuta herramientas estándar (pytest, tsc, vitest) via GitHub Actions sin procesamiento de argumentos dinámicos ni lógica de autorización.

---

## Migration / Rollout

1. Migración `company_id` se aplica con `alembic upgrade head` automáticamente por el lifespan de la app (comportamiento existente).
2. Columna nullable → no requiere backfill de datos.
3. Code-splitting es transparente: solo cambia la salida del build.
4. Vitest y pytest-cov son adiciones sin impacto en producción.

**Rollback**:
- `company_id`: `alembic downgrade -1` + revertir modelo/schemas/services/tests
- CI: borrar `.github/workflows/ci.yml`
- Frontend: revertir `vite.config.ts` y `package.json`
- Coverage/tests: revertir `pyproject.toml`, `requirements.txt`, borrar archivos de test nuevos

---

## Open Questions

- [ ] Confirmar nombres de endpoints de PriceList (¿bajo `/api/v1/price-lists` o existe un prefijo diferente?)
- [ ] ¿PriceList endpoints ya existen o se crean en este cambio? La propuesta menciona solo tests, pero los endpoints deben existir primero.
