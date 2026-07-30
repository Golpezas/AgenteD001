# Delta para Frontend Layout

## ADDED Requirements

### R-F02-A01: Header con NotificationBadge

El sistema DEBE agregar el componente `NotificationBadge` dentro del `Header` existente del layout. El badge DEBE contener un icono `BellOutlined` de Ant Design con un `Badge` mostrando el contador de notificaciones no leídas (`unreadCount`). Al hacer clic, DEBE abrir un `Dropdown` con las últimas 5 notificaciones y un enlace "Ver todas" que navegue a `/notifications`. Este requisito extiende el `Header` definido en R-F02 de `frontend-base`.

#### Escenario: Badge integrado en Header

- DADO que el layout con Header se renderiza
- CUANDO el Header se muestra
- ENTONCES DEBE existir el icono BellOutlined con un Badge
- Y el Badge DEBE reflejar el contador de notificaciones no leídas

#### Escenario: Dropdown con enlace a historial

- DADO que el dropdown de notificaciones está abierto
- CUANDO se hace clic en "Ver todas"
- ENTONCES el sistema DEBE navegar a `/notifications`
- Y el dropdown DEBE cerrarse

#### Escenario: Sin notificaciones nuevas

- DADO que `unreadCount` es 0
- CUANDO el Header se renderiza
- ENTONCES el Badge NO DEBE mostrar número
- Y al abrir el dropdown DEBE mostrar "No hay notificaciones"

#### Escenario: Ruta /notifications es accesible

- DADO el enrutador configurado con la ruta `/notifications`
- CUANDO se navega directamente a `/notifications`
- ENTONCES DEBE renderizarse la página de historial de notificaciones
- Y el sidebar NO DEBE mostrar un item nuevo (la navegación es solo desde el dropdown)
