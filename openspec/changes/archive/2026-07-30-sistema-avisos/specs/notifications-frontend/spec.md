# Notifications Frontend — Especificación

## Propósito

Componentes de interfaz para visualizar y gestionar notificaciones del sistema: badge con contador en Header, dropdown con últimas 5 no leídas, y página de historial completo con paginación y filtros.

## Requisitos

### R-NF01: Hook useNotifications

El sistema DEBE proveer un hook `useNotifications` que exponga: `notifications` (Notification[]), `unreadCount` (number), `markRead(id)`, `markAllRead()`, `loading` (boolean), `error` (string | null). El hook DEBE implementar polling cada 30s a `GET /api/v1/notifications?is_read=false&page_size=20` y detener el polling al desmontar el componente.

#### Escenario: Polling inicial y actualización

- DADO que el hook se monta en un componente
- CUANDO transcurren 30 segundos
- ENTONCES DEBE hacer GET a `/api/v1/notifications?is_read=false&page_size=20`
- Y DEBE actualizar `notifications` y `unreadCount` con la respuesta

#### Escenario: Error de red en polling

- DADO que el backend no responde
- CUANDO el polling falla
- ENTONCES `error` DEBE contener el mensaje de error
- Y el polling DEBE continuar en el siguiente ciclo de 30s

#### Escenario: Polling se detiene al desmontar

- DADO que el hook está activo
- CUANDO el componente se desmonta
- ENTONCES el intervalo de polling DEBE limpiarse

### R-NF02: NotificationBadge con Dropdown

El sistema DEBE renderizar un componente `NotificationBadge` con: icono `BellOutlined` de Ant Design, `Badge` mostrando `unreadCount`, y un `Dropdown` (menu Ant Design) con las últimas 5 notificaciones no leídas. Cada item del dropdown DEBE mostrar título, hora relativa y un enlace "Ver todas" al final.

#### Escenario: Badge muestra contador

- DADO que hay 3 notificaciones no leídas
- CUANDO el NotificationBadge se renderiza
- ENTONCES el Badge DEBE mostrar el número 3

#### Escenario: Dropdown con últimas 5

- DADO que hay 10 notificaciones no leídas
- CUANDO se hace clic en la campana
- ENTONCES el dropdown DEBE listar solo 5 notificaciones
- Y cada una DEBE mostrar título y timestamp relativo
- Y DEBE existir un item "Ver todas" al final

#### Escenario: Dropdown vacío

- DADO que no hay notificaciones no leídas
- CUANDO se hace clic en la campana
- ENTONCES el dropdown DEBE mostrar "No hay notificaciones"
- Y NO DEBE mostrar el enlace "Ver todas"

#### Escenario: Contador cero no se muestra

- DADO que `unreadCount` es 0
- CUANDO el Badge se renderiza
- ENTONCES el Badge NO DEBE mostrar número visible

### R-NF03: Página /notifications

El sistema DEBE renderizar en la ruta `/notifications` una página con: título "Notificaciones", tabla Ant Design paginada (columnas: type, category, title, created_at, leída, acciones), filtros por type (select), category (input), is_read (switch). La tabla DEBE consumir `GET /api/v1/notifications` con paginación server-side. DEBE incluir botón "Marcar todas leídas".

#### Escenario: Historial paginado

- DADO que existen 50 notificaciones en BD
- CUANDO se navega a `/notifications`
- ENTONCES la tabla DEBE mostrar 20 notificaciones
- Y DEBE tener controles de paginación (anterior/siguiente)

#### Escenario: Filtrar por tipo

- DADO que hay notificaciones de type system y business
- CUANDO se selecciona el filtro "system"
- ENTONCES la tabla DEBE recargar mostrando solo type=system

#### Escenario: Marcar como leída desde la tabla

- DADA una notificación no leída en la tabla
- CUANDO se hace clic en acción "Marcar leída"
- ENTONCES DEBE llamar a PATCH `/api/v1/notifications/{id}/read`
- Y la fila DEBE reflejar el estado leído

#### Escenario: Error de carga

- DADO que el backend retorna error 500
- CUANDO se carga la página
- ENTONCES DEBE mostrarse un mensaje de error en la UI
- Y la tabla DEBE mostrar estado vacío
