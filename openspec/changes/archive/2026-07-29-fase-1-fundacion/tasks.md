# Tareas: Fase 1 — Fundación

## Review Workload Forecast

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

Estimated changed lines: ~2500 en 47+ archivos. Se recomiendan 3 PRs encadenados.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Infra + Backend Core (Docker, config, models, DB, Alembic) | PR 1 | `docker compose up --build && curl -s localhost:8000/health` | `docker compose up` | `docker compose down -v` + git reset |
| 2 | Backend API + PixelRAG (repos, services, endpoints, pixelrag) | PR 2 | `pytest -v --asyncio-mode=auto` | `docker compose up backend db` | git revert |
| 3 | Frontend + Docs (scaffold, layout, pages, hooks, docs) | PR 3 | `cd frontend && npx tsc --noEmit && npm run build` | `npm run dev` + backend | git revert |

## Fase 1: Infraestructura

- [x] F1.1 .gitignore, .env.example, backend/requirements.txt
- [x] F1.2 docker-compose.yml (4 servicios: backend, frontend, db, nginx)
- [x] F1.3 nginx/nginx.conf (proxy /api/* y /*)
- [x] F1.4 backend/Dockerfile (multi-stage con Chromium)
- [x] F1.5 frontend/Dockerfile, vercel.json, render.yaml

## Fase 2: Backend Core (Strict TDD)

- [x] F2.1 Tests RED para modelos SQLAlchemy (Company, Product, PriceList, PriceListItem, PricingRule)
- [x] F2.2 Crear backend/app/core/config.py (Pydantic Settings) + database.py (AsyncEngine, session, get_db)
- [x] F2.3 backend/app/models/*.py — 5 modelos con UUID PK, JSONB, soft delete
- [x] F2.4 backend/app/schemas/*.py — Pydantic v2 DTOs (Create, Update, Response, PaginatedResponse)
- [x] F2.5 backend/alembic/ — env.py + revisión inicial "init"

## Fase 3: Backend API (Strict TDD)

- [x] F3.1 Tests RED para repositories y services
- [x] F3.2 CompanyRepository, ProductRepository (CRUD genérico SQLAlchemy 2.0)
- [x] F3.3 CompanyService, ProductService (lógica de negocio inyectable)
- [x] F3.4 Tests RED para endpoints (health, CRUD clientes y productos)
- [x] F3.5 Endpoints: health.py (GET /health), clients.py, products.py
- [x] F3.6 backend/app/main.py (lifespan, CORS, routers, lifespan DB migration)

## Fase 4: PixelRAG

- [x] F4.1 Tests RED para PixelRAGService (render_url)
- [x] F4.2 services/pixelrag.py — wrapper lazy con render_url() y ValueErrors
- [x] F4.3 api/pixelrag.py — endpoint GET /api/v1/pixelrag/test

## Fase 5: Frontend

- [x] F5.1 package.json, vite.config.ts (proxy /api), tsconfig.json
- [x] F5.2 src/main.tsx (ConfigProvider dark) + App.tsx (Router + AppLayout)
- [x] F5.3 src/types/index.ts + src/services/api.ts (fetch wrapper tipado)
- [x] F5.4 src/components/layout/ (AppLayout: Sider colapsable + Header + Outlet)
- [x] F5.5 hooks/ (useClients, useProducts, useDashboard) + components/ui/StatCard
- [x] F5.6 components/clients/ (ClientTable Ant Table + ClientForm Modal)
- [x] F5.7 components/products/ (ProductTable + ProductForm Modal)
- [x] F5.8 src/pages/ (Dashboard, Clients, Products)

## Fase 6: Documentación

- [x] F6.1 testsprite.config.yml
- [x] F6.2 docs/DEV_SETUP.md
