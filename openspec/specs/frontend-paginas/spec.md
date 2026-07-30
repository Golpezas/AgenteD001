# Frontend Páginas — Especificación

## Propósito

Definir las páginas del frontend: dashboard con resumen, CRUD de clientes y CRUD de productos/precios.

## Capacidades

- `frontend-dashboard`: Página de bienvenida con cards de resumen
- `frontend-clients`: Página CRUD clientes (tabla + modal formulario)
- `frontend-products`: Página CRUD productos/precios (tabla + formulario)

## Requisitos

### R-G01: Dashboard

El sistema DEBE renderizar en `/` una página de bienvenida con: título ("Bienvenido a AgenteD"), subtítulo descriptivo, y al menos tres cards de resumen con iconos de Ant Design: "Empresas", "Productos" y "Listas de Precio". Cada card DEBE mostrar un contador (total de registros activos) obtenido del backend.

#### Escenario: Dashboard carga con datos

- DADO que el backend tiene 10 empresas, 25 productos y 5 listas de precio
- CUANDO se navega a `/`
- ENTONCES DEBEN renderizarse tres cards con los títulos "Empresas", "Productos" y "Listas de Precio"
- Y los valores DEBEN ser 10, 25 y 5 respectivamente

#### Escenario: Dashboard sin datos

- DADO que el backend no tiene registros
- CUANDO se navega a `/`
- ENTONCES los cards DEBEN mostrar valor 0
- Y NO DEBE mostrar errores

### R-G02: Página de Clientes

El sistema DEBE renderizar en `/clients` una página con: título "Clientes", botón "Nuevo Cliente", tabla Ant Design con columnas `name`, `legal_name`, `tax_id`, `email`, `phone`, `actions`. Los actions DEBEN incluir editar (modal) y eliminar (confirmación). El formulario DEBE estar en un `Modal` de Ant Design con campos para `name`, `legal_name`, `tax_id`, `email`, `phone`, `address`. La tabla DEBE soportar paginado.

#### Escenario: Listar clientes en tabla

- DADO que existen clientes en el backend
- CUANDO se navega a `/clients`
- ENTONCES la tabla DEBE mostrar los clientes paginados
- Y cada fila DEBE mostrar nombre, información fiscal y acciones

#### Escenario: Crear cliente desde modal

- DADO que el modal "Nuevo Cliente" está abierto
- CUANDO se completan los campos requeridos y se hace clic en "Guardar"
- ENTONCES el cliente DEBE crearse vía POST al backend
- Y la tabla DEBE actualizarse con el nuevo cliente
- Y el modal DEBE cerrarse

#### Escenario: Eliminar cliente con confirmación

- DADO que la tabla de clientes está visible
- CUANDO se hace clic en el icono de eliminar
- ENTONCES DEBE mostrarse un `Popconfirm` de Ant Design
- Y al confirmar, el cliente DEBE eliminarse (soft delete)
- Y la tabla DEBE actualizarse

#### Escenario: Validación en formulario

- DADO que el modal de crear/editar está abierto
- CUANDO se intenta guardar sin completar `name`
- ENTONCES el campo DEBE mostrar mensaje de validación
- Y el modal NO DEBE cerrarse

### R-G03: Página de Productos

El sistema DEBE renderizar en `/products` una página con: título "Productos", botón "Nuevo Producto", tabla Ant Design con columnas `sku`, `name`, `category`, `base_price`, `unit`, `actions`. Los actions DEBEN incluir editar y eliminar. El formulario DEBE estar en un `Modal` con campos: `sku`, `name`, `description`, `category`, `unit`, `base_price`. La tabla DEBE soportar paginado.

#### Escenario: Crear producto con precio base

- DADO que el modal "Nuevo Producto" está abierto
- CUANDO se completan `sku`, `name` y `base_price` y se guarda
- ENTONCES el producto DEBE crearse vía POST
- Y la tabla DEBE mostrar el nuevo producto con su precio

#### Escenario: SKU duplicado desde frontend

- DADO que se intenta crear un producto con SKU existente
- CUANDO el backend retorna 409 Conflict
- ENTONCES la página DEBE mostrar una notificación de error
- Y el modal DEBE permanecer abierto para corrección
