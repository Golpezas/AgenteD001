# Propuesta: Fase 1 — Fundación

## Intención

Establecer la infraestructura base del proyecto: que compile, corra completo
en Docker y tenga funcionalidad operativa para gestión de clientes, productos
y precios con un modelo de datos genérico y configurable, más la integración
de PixelRAG como capa de ingestion visual.

## Alcance

### Incluye
- **Docker**: FastAPI + React + PostgreSQL + Nginx (reverse proxy)
- **Backend**: app base con health check, config, database session + Alembic
- **Backend**: modelo companies (genérico, sin acoplamiento a plataformas)
- **Backend**: modelos products + price_list_items + pricing_rules (configurables por negocio)
- **Backend**: API CRUD completo de clientes, productos y precios
- **PixelRAG**: instalación como dependencia + wrapper service base (pixelshot)
- **Frontend**: scaffold Vite + React + TypeScript + Ant Design (dark theme)
- **Frontend**: layout base (sidebar, header, routing con React Router)
- **Frontend**: dashboard con bienvenida y cards de resumen
- **Frontend**: CRUD clientes (listar, crear, editar, eliminar)
- **Frontend**: CRUD productos/precios (listar, crear, editar, eliminar)
- **Documentación**: DEV_SETUP.md, .env.example

### Excluye
- Autenticación (fase posterior)
- UI de upload de capturas / ingestion visual por PixelRAG (Fase 2)
- Price Engine, GAP Analysis, Proposal Generator (Fase 3)
- Task Manager, notificaciones, WebSocket, workers (Fase 4-5)
- Integraciones específicas con APIs de CRM/ERP (fases posteriores)

## Capacidades

### Nuevas capacidades
| Capacidad | Descripción |
|-----------|-------------|
| `docker-setup` | Stack completo dockerizado con Nginx reverse proxy |
| `health-check` | Endpoint GET /health con estado del sistema |
| `database-session` | Config, sesión SQLAlchemy y migración Alembic inicial |
| `companies-crud` | API REST CRUD de empresas/clientes (modelo genérico) |
| `products-crud` | API REST CRUD de productos, price_list_items y pricing_rules |
| `pixelrag-base` | Instalación de PixelRAG + wrapper service para renderizado |
| `frontend-scaffold` | Vite + React + TypeScript + Ant Design 5 dark |
| `frontend-layout` | Sidebar, Header, routing con React Router |
| `frontend-dashboard` | Página de bienvenida con cards de resumen |
| `frontend-clients` | Página CRUD clientes (tabla + modal formulario) |
| `frontend-products` | Página CRUD productos/precios (tabla + formulario) |
| `dev-docs` | DEV_SETUP.md, .env.example |

### Modificadas
Ninguna.

## Enfoque

Backend FastAPI con Repository + Service Layer, SQLAlchemy 2.0 style.
Frontend SPA con Ant Design 5 dark, Atomic Design, Container-Presentational.
Docker multi-stage con Nginx.
PixelRAG instalado como dependencia del backend con service wrapper.

## Áreas Afectadas

| Área | Impacto |
|------|---------|
| `docker-compose.yml` | Nuevo |
| `backend/Dockerfile` | Nuevo |
| `backend/app/` | Nuevo |
| `backend/requirements.txt` | Nuevo (incluye pixelrag) |
| `frontend/Dockerfile` | Nuevo |
| `frontend/` | Nuevo |
| `nginx/` | Nuevo |
| `db/` | Nuevo |
| `.env.example` | Nuevo |
| `docs/DEV_SETUP.md` | Nuevo |

## Riesgos

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| PixelRAG requiere Chrome/Chromium en producción | Baja | Incluir Chrome headless en Dockerfile del backend |
| Modelo de datos genérico puede necesitar ajustes por negocio | Media | Usar JSONB para campos flexibles; migraciones evolutivas |
| Versiones de imágenes Docker incompatibles | Baja | Pin versions exactas en docker-compose.yml |

## Plan de Rollback

1. `docker compose down -v` para destruir contenedores y volúmenes
2. `git checkout HEAD~1` para revertir archivos de código
3. `git clean -fd` para eliminar archivos no trackeados (verificar con `--dry-run`)
4. Verificar que `openspec/changes/fase-1-fundacion/` quede consistente

## Dependencias

- Docker Engine 24+ y docker-compose v2
- Python 3.12+, Node.js 20+, PostgreSQL 16 (imágenes base)
- PixelRAG (instalado vía pip en el backend)
- Chrome/Chromium (para pixelshot en pipeline de render)

## Criterios de Éxito

- [ ] `docker compose up --build` levanta todo el stack sin errores
- [ ] `GET /health` responde 200 OK con estado de servicios
- [ ] API CRUD clientes funcional (POST, GET, PUT, DELETE)
- [ ] API CRUD productos/precios funcional
- [ ] PixelRAG instalado y `pixelshot` accesible desde el backend
- [ ] Wrapper service de renderizado responde correctamente
- [ ] Frontend carga con tema oscuro Ant Design 5
- [ ] Sidebar navega entre Dashboard, Clientes y Productos
