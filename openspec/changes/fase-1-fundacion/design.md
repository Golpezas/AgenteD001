# Diseño: Fase 1 — Fundación

## Enfoque Técnico

Backend FastAPI asíncrono con SQLAlchemy 2.0 + asyncpg, siguiendo Repository + Service Layer. Frontend SPA con Vite + React + TypeScript + Ant Design 5 dark, usando Container-Presentational. Stack completo dockerizado con multi-stage builds y Nginx como reverse proxy para desarrollo local. Deploy: **Vercel** (frontend), **Render/Railway** (backend + PostgreSQL). PixelRAG integrado como dependencia pip con wrapper service lazy. **TestSprite** como plataforma de testing. **n8n** para workflows en fases posteriores. Versión de API: `/api/v1/`.

---

## Decisiones de Arquitectura

| Decisión | Opciones | Decisión | Razón |
|----------|----------|----------|-------|
| ORM | Sync SQLAlchemy / raw asyncpg | **SQLAlchemy 2.0 async** | Escalabilidad, tipado moderno, alineado con el ecosistema FastAPI |
| IDs | Auto-increment / ULID | **UUID** | Seguro para sistemas distribuidos, sin colisiones en merge, evita enumeración |
| Campos flexibles | EAV / tablas separadas | **JSONB** | Consultable e indexable en PostgreSQL, evita migraciones por personalización |
| Eliminación | Hard delete / deleted_at | **Soft delete (`is_active`)** | Recuperación de datos, seguridad en cascada, auditoría |
| Frontend state | Redux / Zustand / Context | **Context + hooks locales** | Sufficiente para fase 1; migrar a Zustand en fases posteriores si escala |
| API versioning | Header-based / sin version | **URL prefix `/api/v1/`** | Explícito, enrutable desde Nginx, independiente de cliente |
| Tema oscuro | CSS vars / styled-components | **Ant Design ConfigProvider** | Nativo de la librería, evita gestión manual de colores |
| Frontend deploy | Docker + Nginx / Vercel | **Vercel** | Build automático, CDN global, cero ops, preview deployments |
| Backend deploy | Docker compose / Render | **Render (primary) + Railway (alt)** | Deploy desde GitHub, PostgreSQL managed, SSL automático |
| Test platform | Pytest solo / TestSprite | **TestSprite + pytest** | AI-powered testing, cobertura visual, integración continua |
| Workflow engine | Custom services / n8n | **n8n (Fase 2+)** | Automatización visual de notificaciones, webhooks e integraciones |

---

## Flujo de Datos

### Secuencia de arranque Docker

```
docker compose up --build
  ├── Build backend (multi-stage)
  │   ├── Stage 1: pip install -r requirements.txt + Chromium
  │   └── Stage 2: copia site-packages + app → imagen slim
  ├── Build frontend (multi-stage)
  │   ├── Stage 1: npm ci && npm run build
  │   └── Stage 2: Nginx Alpine sirve dist/
  ├── PostgreSQL inicia con volumen persistente
  ├── Backend ejecuta alembic upgrade head al iniciar
  └── Nginx enruta /api/* → backend :8000, /* → frontend :80
```

### Flujo CRUD (Crear Empresa)

```
React UI → api.ts (POST /api/v1/companies) → Nginx → FastAPI router
  → get_db session (DI) → CompanyService.create(payload)
    → CompanyRepository.create(payload)
      → db.add(Company) → db.commit() → db.refresh(company)
  → CompanyResponse (201) → React actualiza tabla
```

### Flujo Health Check

```
GET /health → FastAPI (sin auth)
  → intenta conexión DB
  → si ok:  200 {"status":"ok","database":"connected","version":"...","timestamp":"..."}
  → si falla: 200 {"status":"degraded","database":"disconnected",...}
```

---

## Archivos Afectados (~45 archivos nuevos)

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `docker-compose.yml` | Crear | 4 servicios: backend, frontend, db, nginx (dev local) |
| `nginx/nginx.conf` | Crear | Reverse proxy /api/* → backend, /* → frontend (dev local) |
| `.env.example` | Crear | Template de variables de entorno |
| `.gitignore` | Crear | Ignorar .env, node_modules, __pycache__, dist/ |
| `vercel.json` | Crear | Config deploy frontend en Vercel |
| `render.yaml` | Crear | Config deploy backend + DB en Render (Blueprint) |
| `backend/Dockerfile` | Crear | Multi-stage con Chromium para pixelshot + deploy Render |
| `backend/requirements.txt` | Crear | FastAPI, SQLAlchemy, asyncpg, alembic, pixelrag, httpx, testsprite |
| `backend/app/main.py` | Crear | FastAPI app con lifespan, CORS, routers |
| `backend/app/__init__.py` | Crear | Paquete |
| `backend/app/core/config.py` | Crear | Pydantic Settings desde variables de entorno |
| `backend/app/core/database.py` | Crear | AsyncEngine, async_session, get_db dependency |
| `backend/app/models/*.py` | Crear | Company, Product, PriceList, PriceListItem, PricingRule |
| `backend/app/schemas/*.py` | Crear | Pydantic v2: Create, Update, Response, PaginatedResponse |
| `backend/app/repositories/*.py` | Crear | CompanyRepository, ProductRepository (CRUD genérico) |
| `backend/app/services/*.py` | Crear | CompanyService, ProductService, PixelRAGService |
| `backend/app/api/*.py` | Crear | health.py, clients.py, products.py, pixelrag.py |
| `backend/alembic/` | Crear | Config inicial + migrations/env.py |
| `frontend/package.json` | Crear | Dependencias: react, antd, react-router-dom, @ant-design/icons |
| `frontend/vite.config.ts` | Crear | Proxy /api → localhost:8000 |
| `frontend/src/main.tsx` | Crear | Entry point con ConfigProvider dark |
| `frontend/src/App.tsx` | Crear | Router + AppLayout wrapper |
| `frontend/src/components/layout/` | Crear | AppLayout (Sider + Header + Outlet) |
| `frontend/src/components/clients/` | Crear | ClientTable (Ant Table), ClientForm (Ant Modal) |
| `frontend/src/components/products/` | Crear | ProductTable, ProductForm |
| `frontend/src/components/ui/` | Crear | StatCard para dashboard |
| `frontend/src/pages/*.tsx` | Crear | Dashboard, Clients, Products pages |
| `frontend/src/services/api.ts` | Crear | Cliente HTTP (fetch wrapper) con tipado |
| `frontend/src/hooks/*.ts` | Crear | useClients, useProducts, useDashboard |
| `frontend/src/types/index.ts` | Crear | Interfaces Company, Product, PriceList, PaginatedResponse |
| `frontend/Dockerfile` | Crear | Multi-stage: build + Nginx serve (opcional, para dev local) |
| `testsprite.config.yml` | Crear | Configuración de TestSprite |
| `docs/DEV_SETUP.md` | Crear | Onboarding: requisitos, instalación, comandos |

---

## Interfaces / Contratos

### Paginación unificada (todos los endpoints GET list)

```json
{
  "items": [{"id": "uuid", ...}],
  "total": 25,
  "page": 1,
  "per_page": 10
}
```

### Formato error

```json
{
  "detail": [
    {"loc": ["body", "name"], "msg": "field required", "type": "value_error.missing"}
  ]
}
```

### Dependencia de sesión

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

---

## Estrategia de Pruebas

| Capa | Qué probar | Enfoque |
|------|-----------|---------|
| Unit | Services, Repositories | Pytest + pytest-asyncio + TestSprite AI, mock de sesión SQLAlchemy |
| Integration | Endpoints CRUD | TestClient de FastAPI + TestSprite para cobertura visual |
| E2E | Flujo completo frontend-backend | TestSprite (AI-powered E2E) |

**Strict TDD**: HABILITADO. TestSprite es el test runner principal.
- Los tests se escriben ANTES del código (RED → GREEN → REFACTOR)
- TestSprite genera tests visuales y funcionales automáticamente
- `testsprite.config.yml` en la raíz del proyecto

---

## Matriz de Amenazas

| Límite | Aplicabilidad | Razón |
|--------|--------------|-------|
| Documentation-like paths | N/A | No hay ejecución de archivos clasificados por extensión |
| Git repository selection | N/A | Sin automatización de git en esta fase |
| Commit state | N/A | Sin operaciones de commit automatizadas |
| Push state | N/A | Sin operaciones de push |
| PR commands | N/A | Sin automatización de PRs |

Nota: pixelshot involucra subprocess (Chromium), pero en esta fase el wrapper solo expone `render_url()` con URLs controladas internamente. La seguridad del subprocess se revisará en Fase 2 cuando se exponga a URLs de usuario.

---

## Despliegue

### Frontend → Vercel
- Build: `npm run build` (Vite)
- `vercel.json` con rewrites para SPA
- Preview deployments por PR
- Dominio personalizado opcional

### Backend → Render
- Dockerfile existente + PostgreSQL managed
- `render.yaml` (Blueprint) para infraestructura como código
- Auto-deploy desde GitHub (branch main)
- Health check endpoint para uptime monitoring

### Railway (alternativa)
- Misma Dockerfile, mismo entry point
- Útil si Render tiene outages o para staging

### Local dev
- `docker compose up` levanta todo (backend, frontend, DB, Nginx)
- O frontend standalone con `npm run dev` + proxy Vite a backend local

## Migración

Migración inicial con Alembic: `alembic revision --autogenerate -m "init"` genera la primera migración con todas las tablas de Fase 1. Se ejecuta automáticamente al arrancar el backend en desarrollo (lifespan event).

Sin migración de datos previa — el proyecto arranca desde cero.

---

## Preguntas Abiertas

- Ninguna. El alcance de Fase 1 está completamente cubierto por las decisiones documentadas.
