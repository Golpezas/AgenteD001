# Propuesta: Sistema de Avisos (Notificaciones)

## Intención

Sistema de notificaciones interno que informe sobre eventos automáticos del sistema, alertas comerciales periódicas y avisos manuales, sin email ni servicios externos.

## Alcance

### Incluye
- Modelo `Notification` + migración Alembic
- `NotificationService` síncrono inyectado en servicios existentes
- API `/api/v1/notifications`: listar, marcar leída, forzar verificación comercial
- APScheduler con barrido diario de alertas comerciales
- Badge + campana en Header con dropdown (últimas 5)
- Página `/notifications` con historial paginado y filtros
- Eventos automáticos en ProductService, CompanyService, BusinessPolicyService, PriceListItemService

### Excluye
- Email, Slack, WebSocket
- Autenticación / notificaciones por usuario
- Centro de preferencias
- Push en tiempo real (solo polling)

## Capacidades

### Nuevas Capacidades
- `notifications-backend`: Modelo, repositorio, servicio, API, scheduler APScheduler, integración CRUD
- `notifications-frontend`: NotificationBadge, dropdown, página historial, polling 30s, hook useNotifications

### Capacidades Modificadas
- `frontend-layout`: Header incluye NotificationBadge con campana y contador

## Enfoque

Backend: modelo `Notification` (id, type, category, title, description, resource_type, resource_id, is_read, leído_at + TimestampMixin). `NotificationService.create()` se inyecta en create/update/deactivate de cada servicio. Endpoints: GET list (paginated, filterable), PATCH mark-read, POST force-check. APScheduler inicia en lifespan.

Frontend: hook `useNotifications` con polling 30s. NotificationBadge + BellOutlined en Header. Dropdown últimas 5. Página `/notifications` con tabla paginada y filtros por tipo/categoría/leído.

## Áreas Afectadas

| Área | Impacto |
|------|---------|
| `backend/app/models/notification.py` | Nuevo |
| `backend/app/repositories/notification.py` | Nuevo |
| `backend/app/services/notification.py` | Nuevo |
| `backend/app/services/{product,company,business_policy,price_list_item}.py` | Modificado |
| `backend/app/api/notifications.py` | Nuevo |
| `backend/app/main.py` | Modificado |
| `backend/app/scheduler.py` | Nuevo |
| `backend/app/schemas/notification.py` | Nuevo |
| `backend/requirements.txt` | Modificado |
| `frontend/src/components/layout/AppLayout.tsx` | Modificado |
| `frontend/src/components/notifications/` | Nuevo |
| `frontend/src/hooks/useNotifications.ts` | Nuevo |
| `frontend/src/pages/Notifications.tsx` | Nuevo |
| `frontend/src/types/index.ts` | Modificado |
| `frontend/src/App.tsx` | Modificado |

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Scheduler bloquea lifespan | Baja | ThreadPoolExecutor separado |
| Polling 30s satura API | Baja | Paginación default 20; índice `is_read + created_at` |
| Olvidar inyectar notify en servicio | Media | Test integración verifica Notification tras cada CRUD |

## Plan de Rollback

1. Revertir inyección de NotificationService en servicios
2. Remover router y scheduler de main.py
3. Revertir cambios en frontend (AppLayout, App.tsx)
4. `alembic downgrade -1`
5. Remover APScheduler de requirements.txt

## Criterios de Éxito

- [ ] CRUD de producto genera Notification tipo "system"
- [ ] Dropdown en Header muestra últimas 5 no leídas con contador
- [ ] `/notifications` con historial paginado y filtros funcionales
- [ ] "Forzar verificación comercial" genera notificaciones business
- [ ] Notificaciones se marcan como leídas (individual/masivo)
- [ ] Cobertura de tests > 80%
