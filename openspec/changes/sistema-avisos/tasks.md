# Tareas: Sistema de Avisos (Notificaciones)

## Review Workload Forecast

| Campo | Valor |
|-------|-------|
| Líneas cambiadas estimadas | ~1190 (680 nuevas + 130 modificaciones + 380 tests) |
| Riesgo de presupuesto 400 líneas | Alto |
| Chained PRs recomendados | Sí |
| Split sugerido | Fundación+Backend (PR 1) → Frontend (PR 2) → Integración (PR 3) |
| Estrategia entrega | auto-chain |
| Estrategia cadena | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Work Units

| Unidad | Meta | PR | Test focal | Rollback |
|--------|------|----|------------|----------|
| 1 — Backend Core | Modelo, repo, schemas, service, API, scheduler, +tests backend | PR 1 (base=feature/tracker) | `pytest tests/test_notifications/ -x --cov=app` | Revertir archivos nuevos en backend/ + migración |
| 2 — Frontend | Hook, badge, página, routing, +tests frontend | PR 2 (base=PR1) | `cd frontend && vitest run` | Revertir archivos nuevos en frontend/ |
| 3 — Integración | Inyección en 4 servicios existentes, +tests integración | PR 3 (base=PR2) | `pytest tests/ -x --cov=app` | Revertir cambios en services/\*.py |

## Fase 1: Fundación — Modelo, Repositorio, Schemas

- [x] 1.1 Crear `backend/app/models/notification.py` — modelo Notification SQLAlchemy (UUID PK, type, category, title, description, resource_type, resource_id, is_read, read_at, TimestampMixin, SoftDeleteMixin)
- [x] 1.2 Generar migración Alembic manual `004_add_notifications.py` y validar upgrade/downgrade
- [x] 1.3 Crear `backend/app/schemas/notification.py` — NotificationCreate, NotificationResponse, NotificationList, paginación
- [x] 1.4 Crear `backend/app/repositories/notification.py` — CRUD con filtros type/category/is_read, paginación, soft delete scope
- [x] 1.5 Agregar `apscheduler>=3.10,<4.0` a `backend/requirements.txt`
- [ ] 1.6 Agregar interfaz `Notification` + `NotificationList` a `frontend/src/types/index.ts` *(PR 2)*
- [x] 1.7 Tests unitarios: validación type enum, soft delete, filtros combinados en repositorio

## Fase 2: Backend — Service, API, Scheduler

- [x] 2.1 Crear `backend/app/services/notification.py` — NotificationService con create(), mark_read(), mark_all_read(), force_check() comercial
- [x] 2.2 Crear `backend/app/scheduler.py` — APScheduler en ThreadPoolExecutor, barrido diario de alertas business
- [x] 2.3 Crear `backend/app/api/notifications.py` — GET / (paginado+filtros), PATCH /{id}/read, PATCH /read-all, POST /force-check, POST / (crear manual)
- [x] 2.4 Modificar `backend/app/main.py` — incluir notifications_router + init scheduler en lifespan
- [x] 2.5 Tests integración: 12 escenarios de API (list paginado, filtrar no leídas, marcar leída, 404, read-all, force-check, crear manual, filtros combinados)

## Fase 3: Frontend — Hook, Badge, Página

- [ ] 3.1 Crear `frontend/src/hooks/useNotifications.ts` — polling 30s, markRead, markAllRead, cleanup on unmount, manejo de error
- [ ] 3.2 Crear `frontend/src/components/notifications/NotificationBadge.tsx` — BellOutlined + Badge unreadCount + Dropdown últimas 5 + "Ver todas"
- [ ] 3.3 Crear `frontend/src/pages/Notifications.tsx` — tabla Ant Design paginada server-side, filtros type/category/is_read, botón "Marcar todas leídas"
- [ ] 3.4 Tests hook, badge y página: polling inicial, error red, cleanup, contador cero, dropdown vacío, filtros, marcar leída

## Fase 4: Integración — Inyección en Servicios + Wiring

- [ ] 4.1 Modificar `backend/app/services/product.py` — inyectar NotificationService, crear notificación en create/update/deactivate
- [ ] 4.2 Modificar `backend/app/services/company.py` — inyectar NotificationService en create/update/deactivate
- [ ] 4.3 Modificar `backend/app/services/business_policy.py` — inyectar NotificationService en create/update/deactivate
- [ ] 4.4 Modificar `backend/app/services/price_list_item.py` — inyectar NotificationService en create/update/deactivate
- [ ] 4.5 Modificar `frontend/src/components/layout/AppLayout.tsx` — agregar NotificationBadge en Header
- [ ] 4.6 Modificar `frontend/src/App.tsx` — agregar ruta `/notifications`
- [ ] 4.7 Tests integración: verificar que cada CRUD en servicios genera Notification tipo system, y que error en NotificationService no interrumpe CRUD
