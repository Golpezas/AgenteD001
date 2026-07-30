# Frontend Base — Especificación

## Propósito

Definir el scaffold inicial del frontend con Vite + React + TypeScript + Ant Design 5 dark, y el layout base con sidebar, header y routing.

## Capacidades

- `frontend-scaffold`: Vite + React + TypeScript + Ant Design 5 dark
- `frontend-layout`: Sidebar, Header, routing con React Router

## Requisitos

### R-F01: Proyecto Vite

El sistema DEBE tener un proyecto frontend en `frontend/` creado con Vite + React + TypeScript. Ant Design 5 DEBE estar instalado y configurado con el token de tema oscuro (`algorithm: theme.darkAlgorithm`). El `package.json` DEBE incluir scripts para `dev`, `build` y `preview`. El `vite.config.ts` DEBE configurar proxy para `/api` hacia `http://localhost:8000`.

#### Escenario: Dev server inicia

- DADO que `frontend/` existe con `package.json` y configuraciones
- CUANDO se ejecuta `npm run dev`
- ENTONCES el servidor de desarrollo DEBE iniciar en `http://localhost:5173`

#### Escenario: Build produce dist/

- DADO el proyecto frontend configurado
- CUANDO se ejecuta `npm run build`
- ENTONCES DEBE producirse el directorio `frontend/dist/`
- Y DEBE contener `index.html` y archivos JS/CSS compilados

#### Escenario: Tema oscuro aplicado globalmente

- DADO que el frontend ha cargado en el navegador
- CUANDO se inspecciona el `ConfigProvider` de Ant Design
- ENTONCES `algorithm` DEBE ser `theme.darkAlgorithm`
- Y los componentes DEBEN renderizar con fondo oscuro

#### Escenario: Proxy de API funciona

- DADO que el backend está corriendo en `http://localhost:8000`
- CUANDO el frontend hace fetch a `/api/v1/companies`
- ENTONCES Vite DEBE redirigir la petición al backend
- Y la respuesta DEBE venir del backend

### R-F02: Layout con Sidebar y Header

El sistema DEBE renderizar un layout persistente con: un `Header` con el nombre del sistema ("AgenteD"), un `Sider` (sidebar) colapsable con items de navegación, y un `<Outlet />` para el contenido. El `Sider` DEBE incluir al menos tres entradas: "Dashboard", "Clientes" y "Productos". El sidebar DEBE poder colapsarse/expanderse con un botón en el header.

#### Escenario: Layout se renderiza

- DADO que el frontend carga en el navegador
- CUANDO se navega a cualquier ruta
- ENTONCES el Header DEBE mostrar "AgenteD"
- Y el Sider DEBE mostrar los items: Dashboard, Clientes, Productos
- Y el contenido DEBE renderizarse en el área principal

#### Escenario: Sidebar colapsable

- DADO el layout renderizado
- CUANDO se hace clic en el botón de colapso del sidebar
- ENTONCES el sidebar DEBE contraerse mostrando solo iconos
- Y CUANDO se hace clic nuevamente
- ENTONCES el sidebar DEBE expandirse mostrando etiquetas completas

### R-F03: Routing con React Router

El sistema DEBE usar React Router v6+ con las siguientes rutas:

| Ruta | Componente | Descripción |
|------|-----------|-------------|
| `/` | Dashboard | Página de bienvenida |
| `/clients` | ClientsPage | CRUD de clientes |
| `/products` | ProductsPage | CRUD de productos/precios |

Cualquier ruta no definida DEBE redirigir a `/`.

#### Escenario: Navegación entre rutas

- DADO que el frontend está cargado
- CUANDO se hace clic en "Clientes" en el sidebar
- ENTONCES la URL DEBE cambiar a `/clients`
- Y el contenido DEBE mostrar la página de clientes
- Y el item activo del sidebar DEBE resaltarse

#### Escenario: Ruta desconocida redirige

- DADO que el frontend está cargado
- CUANDO se navega a `/ruta-inexistente`
- ENTONCES el sistema DEBE redirigir a `/`
