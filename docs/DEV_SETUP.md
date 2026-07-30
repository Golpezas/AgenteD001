# Configuración de Desarrollo — AgenteD

## Requisitos

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| Docker Engine | 24+ | Contenedores |
| docker-compose | v2 | Orquestación local |
| Python | 3.12+ | Backend FastAPI |
| Node.js | 20+ | Frontend React + Vite |
| npm | 10+ | Gestor de paquetes |
| PostgreSQL | 16 | Base de datos |

## Stack

```
AgenteD/
├── backend/          # FastAPI + SQLAlchemy + Alembic
│   ├── app/          # Código fuente
│   ├── alembic/      # Migraciones
│   └── tests/        # Tests (pytest)
├── frontend/         # React + Vite + Ant Design 5
│   └── src/          # Código fuente
├── nginx/            # Configuración Nginx (dev local)
├── docs/             # Documentación
└── openspec/         # SDD (Spec-Driven Development)
```

## Inicio Rápido

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd AgenteD
```

### 2. Variables de entorno

```bash
cp .env.example .env
# Editar .env según sea necesario
# La configuración por defecto funciona para desarrollo local
```

### 3. Levantar todo con Docker

```bash
docker compose up --build
```

Esto levanta 4 servicios:
- **Backend** (FastAPI) → `http://localhost:8000`
- **Frontend** (Nginx) → `http://localhost:80`
- **PostgreSQL** → `localhost:5432`
- **Nginx** (reverse proxy) → `http://localhost`

El health check está disponible en `http://localhost:8000/api/v1/health`.

### 4. Desarrollo Frontend Standalone

Para trabajar solo en el frontend con hot-reload:

```bash
cd frontend
npm install
npm run dev
```

El servidor de desarrollo inicia en `http://localhost:5173`.
Las peticiones a `/api/*` se redirigen automáticamente a `http://localhost:8000`
gracias al proxy configurado en `vite.config.ts`.

### 5. Desarrollo Backend Standalone

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Asegúrate de tener PostgreSQL corriendo
# Edita backend/.env con tu conexión de base de datos

uvicorn app.main:app --reload --port 8000
```

## Comandos Útiles

```bash
# Tests del backend
cd backend && python -m pytest tests/ -v --asyncio-mode=auto

# TestSprite
testsprite run

# TypeScript check (frontend)
cd frontend && npx tsc --noEmit

# Build frontend
cd frontend && npm run build

# Migraciones Alembic
cd backend && alembic upgrade head     # Aplicar migraciones
cd backend && alembic downgrade -1     # Revertir última migración
cd backend && alembic revision --autogenerate -m "descripcion"

# Docker
docker compose up --build              # Construir y levantar
docker compose down                    # Detener servicios
docker compose down -v                 # Detener y eliminar volúmenes
docker compose logs -f                 # Ver logs en tiempo real
```

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check del sistema |
| POST | `/api/v1/companies` | Crear empresa/cliente |
| GET | `/api/v1/companies` | Listar empresas (paginado) |
| GET | `/api/v1/companies/:id` | Obtener empresa por ID |
| PUT | `/api/v1/companies/:id` | Actualizar empresa |
| DELETE | `/api/v1/companies/:id` | Eliminar empresa (soft delete) |
| POST | `/api/v1/products` | Crear producto |
| GET | `/api/v1/products` | Listar productos (paginado) |
| GET | `/api/v1/products/:id` | Obtener producto por ID |
| PUT | `/api/v1/products/:id` | Actualizar producto |
| DELETE | `/api/v1/products/:id` | Eliminar producto (soft delete) |
| GET | `/api/v1/pixelrag/test` | Test de integración PixelRAG |

## Estructura del Frontend

```
frontend/
├── index.html                 # Entry point HTML
├── package.json               # Dependencias y scripts
├── vite.config.ts             # Configuración Vite + proxy
├── tsconfig.json              # TypeScript estricto
├── nginx.conf                 # Config Nginx para build de producción
├── Dockerfile                 # Multi-stage build (Node → Nginx)
└── src/
    ├── main.tsx               # Entry point React + ConfigProvider dark
    ├── App.tsx                # Router principal
    ├── types/index.ts         # Interfaces TypeScript
    ├── services/api.ts        # Cliente HTTP tipado
    ├── hooks/
    │   ├── useClients.ts      # CRUD de clientes
    │   ├── useProducts.ts     # CRUD de productos
    │   └── useDashboard.ts    # Estadísticas del dashboard
    ├── components/
    │   ├── layout/
    │   │   └── AppLayout.tsx  # Sidebar + Header + Outlet
    │   ├── clients/
    │   │   ├── ClientTable.tsx # Tabla Ant Design
    │   │   └── ClientForm.tsx  # Modal con formulario
    │   ├── products/
    │   │   ├── ProductTable.tsx
    │   │   └── ProductForm.tsx
    │   └── ui/
    │       └── StatCard.tsx   # Card con estadística
    └── pages/
        ├── Dashboard.tsx      √ (ruta: /)
        ├── Clients.tsx        √ (ruta: /clients)
        └── Products.tsx       √ (ruta: /products)
```

## Convenciones

- **Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **Frontend**: TypeScript estricto, Ant Design 5 dark, Container-Presentational
- **Backend**: Python 3.12+ tipado, SQLAlchemy 2.0 async, Repository + Service Layer
- **Testing**: TDD (RED → GREEN → REFACTOR) con pytest + TestSprite
- **UI**: Todos los textos en español

## Rollback

```bash
# Revertir cambios locales no commiteados
git checkout -- <archivo>

# Revertir último commit manteniendo cambios en working directory
git reset --soft HEAD~1

# Revertir Docker (destructivo)
docker compose down -v
```
