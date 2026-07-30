# Notifications Backend — Especificación

## Propósito

Sistema de notificaciones internas que registra eventos automáticos del sistema, alertas comerciales periódicas y avisos manuales, sin email ni servicios externos.

## Requisitos

### R-NB01: Modelo Notification

El sistema DEBE tener un modelo `Notification` con: `id` (UUID PK), `type` (enum: system|business|manual), `category` (str), `title` (str), `description` (str, nullable), `resource_type` (str, nullable), `resource_id` (str, nullable), `is_read` (bool, default false), `read_at` (datetime, nullable). DEBE incluir `TimestampMixin` (created_at, updated_at) y `SoftDeleteMixin` (deactivated_at).

#### Escenario: Crear notificación no leída

- DADO que el modelo Notification existe en la BD
- CUANDO se crea una notificación sin especificar `is_read`
- ENTONCES `is_read` DEBE ser false
- Y `read_at` DEBE ser NULL
- Y `created_at` DEBE poblarse automáticamente

#### Escenario: Soft delete de notificación

- DADA una notificación existente
- CUANDO se elimina (soft delete)
- ENTONCES `deactivated_at` DEBE poblarse
- Y la notificación NO DEBE aparecer en queries por defecto

#### Escenario: Tipo inválido

- DADO que se intenta crear una notificación
- CUANDO `type` no es system, business ni manual
- ENTONCES el sistema DEBE rechazar con error de validación

### R-NB02: API REST Notifications

El sistema DEBE exponer bajo `/api/v1/notifications`:

| Método | Ruta | Comportamiento |
|--------|------|---------------|
| GET | `/` | Listar, paginado (default 20), filtrable por type, category, is_read |
| PATCH | `/{id}/read` | Marcar una notificación como leída |
| PATCH | `/read-all` | Marcar todas como leídas |
| POST | `/force-check` | Ejecutar verificación comercial manual |

#### Escenario: Listar notificaciones paginadas

- DADO que existen 50 notificaciones en BD
- CUANDO se hace GET `/api/v1/notifications?page=1&page_size=20`
- ENTONCES DEBE retornar 20 notificaciones
- Y DEBE incluir `total: 50`, `page: 1`, `page_size: 20`

#### Escenario: Filtrar no leídas

- DADO que hay 10 notificaciones (3 no leídas, 7 leídas)
- CUANDO se hace GET `/api/v1/notifications?is_read=false`
- ENTONCES DEBE retornar solo las 3 no leídas

#### Escenario: Marcar como leída individual

- DADA una notificación no leída
- CUANDO se hace PATCH `/api/v1/notifications/{id}/read`
- ENTONCES `is_read` DEBE ser true
- Y `read_at` DEBE contener el timestamp actual

#### Escenario: Marcar todas como leídas

- DADO que hay 5 notificaciones no leídas
- CUANDO se hace PATCH `/api/v1/notifications/read-all`
- ENTONCES todas las notificaciones no leídas DEBEN tener `is_read=true`

#### Escenario: Notificación inexistente

- DADO que no existe una notificación con ese ID
- CUANDO se hace PATCH `/api/v1/notifications/{id}/read`
- ENTONCES DEBE retornar 404

### R-NB03: APScheduler — Barrido Comercial

El sistema DEBE ejecutar un scheduler con APScheduler que realice un barrido diario de reglas de negocio y genere notificaciones de tipo `business`. El scheduler DEBE iniciarse en el evento `lifespan` de FastAPI en un `ThreadPoolExecutor` separado para no bloquear el arranque.

#### Escenario: Scheduler genera alertas

- DADO que hay productos con precio vencido según reglas de negocio
- CUANDO el scheduler ejecuta la verificación comercial
- ENTONCES DEBE crear una Notification de tipo `business` por cada alerta

#### Escenario: Scheduler no bloquea inicio de la app

- DADO que el scheduler falla al instanciarse
- CUANDO la aplicación inicia
- ENTONCES la app DEBE estar operativa
- Y el error DEBE registrarse en logs

### R-NB04: Integración en Servicios CRUD

El sistema DEBE inyectar `NotificationService` en `ProductService`, `CompanyService`, `BusinessPolicyService` y `PriceListItemService`. Cada servicio DEBE crear una notificación de tipo `system` al crear, actualizar o desactivar una entidad. La creación de notificación DEBE ser asíncrona (fire-and-forget) para no afectar la respuesta del CRUD.

#### Escenario: Notificación al crear producto

- DADO que ProductService tiene NotificationService inyectado
- CUANDO se crea un producto exitosamente
- ENTONCES DEBE persistirse una Notification con `type=system`
- Y `title` DEBE describir el evento (ej: "Producto {name} creado")
- Y `resource_type` DEBE ser "product" y `resource_id` el ID del producto

#### Escenario: Notificación al desactivar empresa

- DADO que CompanyService tiene NotificationService inyectado
- CUANDO se desactiva una empresa
- ENTONCES DEBE persistirse una Notification con `type=system`

#### Escenario: Error no interrumpe CRUD

- DADO que NotificationService lanza una excepción
- CUANDO se ejecuta una operación CRUD
- ENTONCES el CRUD DEBE completarse sin error
- Y el error de notificación DEBE registrarse en logs
