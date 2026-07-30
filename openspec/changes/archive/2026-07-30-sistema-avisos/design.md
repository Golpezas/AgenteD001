# Design: Sistema de Avisos (Notificaciones)

## Technical Approach

Backend sincrónico sin event bus. `NotificationService` inyectado como dependencia en servicios CRUD existentes. Scheduler APScheduler en `ThreadPoolExecutor` dentro del lifespan. Frontend con polling 30s vía hook `useNotifications`. Sin SSE ni WebSocket — la app no requiere tiempo real estricto.

## Architecture Decisions

| Opción | Alternativas | Decisión | Rationale |
|--------|-------------|----------|-----------|
| **Sync NotificationService** | Event bus (Redis pub/sub, RabbitMQ) | ✅ Sync | No hay consumidores externos. El event bus agrega latencia e infraestructura sin beneficio. La notificación es fire-and-forget con try/except para no interrumpir el CRUD. |
| **resource_type + resource_id (str)** | FK polimórfica real, JSONB | ✅ Sin FK | Postgres no soporta FKs polimórficas nativas. `resource_type` (str) + `resource_id` (str UUID) permite referencias débiles sin CHECK constraints ni tablas de unión. El frontend resuelve enlaces por type. |
| **APScheduler en ThreadPoolExecutor** | Async schedule librería (apscheduler async), Celery | ✅ TP Executor | APScheduler 3.x async es inmaduro. Celery es overkill. `run_in_executor(None, ...)` separa el scheduler del event loop sin bloquear lifespan. Mínima dependencia. |
| **Polling 30s (useEffect + setInterval)** | SSE, WebSocket | ✅ Polling | Sin necesidad de tiempo real estricto. Polling 30s es simple, sin conexiones persistentes, compatible con serverless/Render. SSE requiere mantener conexión abierta (Render free timeout). |
| **is_read global** | is_read por usuario | ✅ Global | Sin autenticación de usuarios. Una sola empresa/grupo opera el sistema. `is_read` booleano + `read_at` timestamp cubre el caso de uso. |

## Data Flow

```
ProductService.create()
  │
  ├── repository.create(product) ──→ PostgreSQL (products)
  │
  └── NotificationService.create()
        │   type="system", resource_type="product", resource_id=product.id
        │
        └── notification_repository.create(notif) ──→ PostgreSQL (notifications)
                                                          │
                    ┌──────────────────────────────────────┘
                    ▼
    Frontend (polling 30s)
      useNotifications ──→ GET /api/v1/notifications?is_read=false
        │
        ├── Badge muestra unreadCount
        └── Dropdown últimas 5
```

## File Changes

| File | Acción | Descripción |
|------|--------|-------------|
| `backend/app/models/notification.py` | Crear | Modelo Notification + migración Alembic |
| `backend/app/schemas/notification.py` | Crear | Schemas Pydantic (create, response, list) |
| `backend/app/repositories/notification.py` | Crear | CRUD con filtros por type/category/is_read |
| `backend/app/services/notification.py` | Crear | `create()`, `mark_read()`, `mark_all_read()`, `force_check()` |
| `backend/app/scheduler.py` | Crear | APScheduler diario + verificación comercial |
| `backend/app/api/notifications.py` | Crear | GET /, PATCH /{id}/read, PATCH /read-all, POST /force-check |
| `backend/app/services/product.py` | Modificar | Inyectar NotificationService en create/update/deactivate |
| `backend/app/services/company.py` | Modificar | Inyectar NotificationService |
| `backend/app/services/business_policy.py` | Modificar | Inyectar NotificationService |
| `backend/app/services/price_list_item.py` | Modificar | Inyectar NotificationService |
| `backend/app/main.py` | Modificar | Agregar router + lifespan scheduler init |
| `backend/requirements.txt` | Modificar | Agregar `apscheduler>=3.10,<4.0` |
| `frontend/src/types/index.ts` | Modificar | Agregar interfaz Notification y NotificationList |
| `frontend/src/services/api.ts` | Modificar | Sin cambios (api genérico ya existe) |
| `frontend/src/hooks/useNotifications.ts` | Crear | Polling 30s, markRead, markAllRead |
| `frontend/src/components/notifications/NotificationBadge.tsx` | Crear | BellOutlined + Badge + Dropdown últimas 5 |
| `frontend/src/pages/Notifications.tsx` | Crear | Tabla paginada con filtros type/category/is_read |
| `frontend/src/components/layout/AppLayout.tsx` | Modificar | Agregar NotificationBadge en Header |
| `frontend/src/App.tsx` | Modificar | Agregar ruta `/notifications` |

## Interfaces / Contracts

```python
# Model (SQLAlchemy)
class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID]       # PK
    type: Mapped[str]            # "system" | "business" | "manual"
    category: Mapped[str]        # "product" | "company" | "policy" | "price" | "commercial"
    title: Mapped[str]
    description: Mapped[str | None]
    resource_type: Mapped[str | None]  # "product", "company", etc.
    resource_id: Mapped[str | None]    # UUID string
    is_read: Mapped[bool]        # default False
    read_at: Mapped[datetime | None]

# API
GET    /api/v1/notifications?page=1&per_page=20&type=system&is_read=false
PATCH  /api/v1/notifications/{id}/read          → { is_read: true, read_at: ... }
PATCH  /api/v1/notifications/read-all            → { updated: N }
POST   /api/v1/notifications/force-check         → { created: N }
```

```typescript
// Frontend types
interface Notification {
  id: string;
  type: 'system' | 'business' | 'manual';
  category: string;
  title: string;
  description: string | null;
  resource_type: string | null;
  resource_id: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}
```

## Testing Strategy

| Capa | Coverage | Approach |
|------|----------|----------|
| **Unit (backend)** | NotificationService, scheduler logic, mocking DB | `pytest` + `AsyncMock` — service decide, repository mockeado |
| **Integration (backend)** | API endpoints CRUD + filtros | `httpx.AsyncClient` + `ASGITransport` — test contra DB real |
| **Unit (frontend)** | useNotifications hook, NotificationBadge | `vitest` + `@testing-library/react` — mockear fetch, verificar polling |
| **Component (frontend)** | Página Notifications con tabla y filtros | `vitest` + RTL — render, filtrar, marcar leída |

Sin migración de datos requerida — tabla nueva.

## Threat Matrix

N/A — el diseño no toca routing, shell, subprocess, VCS/PR automation, executable-file classification ni process-integration boundaries.

## Migration / Rollout

No requiere migración de datos. Rollout: crear tabla → deploy backend → deploy frontend. Rollback secuencial por `alembic downgrade -1`.

## Open Questions

- Ninguna — decisiones cerradas en las ADRs arriba.
