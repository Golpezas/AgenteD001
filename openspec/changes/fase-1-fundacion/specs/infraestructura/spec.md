# Infraestructura — Especificación

## Propósito

Definir el stack dockerizado del sistema, el health check del backend y la configuración de base de datos con SQLAlchemy y Alembic.

## Capacidades

- `docker-setup`: Stack completo dockerizado con Nginx reverse proxy
- `health-check`: Endpoint GET /health con estado del sistema
- `database-session`: Config, sesión SQLAlchemy y migración Alembic inicial

## Requisitos

### R-I01: Stack Docker

El sistema DEBE proporcionar un `docker-compose.yml` que defina los servicios: `backend` (FastAPI), `frontend` (Vite + React), `db` (PostgreSQL 16) y `nginx` (reverse proxy). El backend DEBE usar un Dockerfile multi-stage. Los nombres de contenedor DEBEN incluir el prefijo `agented-`. Los volúmenes persistentes DEBEN usarse para PostgreSQL. Las variables de entorno DEBEN cargarse desde un archivo `.env`.

#### Escenario: Stack se levanta completo

- DADO que el archivo `.env` existe con todas las variables requeridas
- CUANDO se ejecuta `docker compose up --build`
- ENTONCES los cuatro servicios (backend, frontend, db, nginx) DEBEN iniciar sin errores
- Y el backend DEBE ser accesible en `http://localhost:8000`
- Y el frontend DEBE ser accesible en `http://localhost:5173`

#### Escenario: Nginx enruta correctamente

- DADO que el stack Docker está corriendo
- CUANDO se accede a `http://localhost/api/`
- ENTONCES Nginx DEBE redirigir al backend FastAPI
- Y CUANDO se accede a `http://localhost/`
- ENTONCES Nginx DEBE servir el frontend compilado

#### Escenario: PostgreSQL persiste datos

- DADO que el stack Docker está corriendo con datos creados
- CUANDO se ejecuta `docker compose down -v` (sin la bandera `-v`)
- Y luego `docker compose up -d`
- ENTONCES los datos previamente creados DEBEN persistir

### R-I02: Health Check

El sistema DEBE exponer `GET /health` que retorne un objeto JSON con: `status` ("ok" o "degraded"), `version` (desde `__version__`), `database` (conectada o no), `timestamp` en ISO 8601. Si la base de datos no responde, `status` DEBE ser "degraded" pero el endpoint NO DEBE retornar error HTTP.

#### Escenario: Sistema saludable

- DADO que el backend está corriendo y PostgreSQL responde
- CUANDO se hace GET a `/health`
- ENTONCES la respuesta DEBE ser 200 OK
- Y el body DEBE contener `{"status": "ok", "version": "...", "database": "connected", "timestamp": "..."}`

#### Escenario: Base de datos caída

- DADO que el backend está corriendo pero PostgreSQL no responde
- CUANDO se hace GET a `/health`
- ENTONCES la respuesta DEBE ser 200 OK
- Y `status` DEBE ser `"degraded"`
- Y `database` DEBE ser `"disconnected"`

### R-I03: Sesión de Base de Datos

El sistema DEBE usar SQLAlchemy 2.0 asíncrono con `asyncpg`. La conexión DEBE configurarse mediante variable de entorno `DATABASE_URL`. La sesión DEBE gestionarse con dependency injection de FastAPI (`SessionLocal` por request, cerrada automáticamente). Alembic DEBE estar configurado con directorio `backend/alembic/` y la migración inicial DEBE crear la tabla `alembic_version`.

#### Escenario: Sesión se inyecta correctamente

- DADO que la aplicación inicia con `DATABASE_URL` válida
- CUANDO un endpoint usa la dependencia de sesión
- ENTONCES la sesión SE DEBE abrir, usar y cerrar automáticamente al finalizar el request

#### Escenario: Migración inicial ejecutada

- DADO que el directorio `backend/alembic/` existe con configuración válida
- CUANDO se ejecuta `alembic upgrade head`
- ENTONCES la tabla `alembic_version` DEBE crearse en la base de datos
- Y el comando DEBE finalizar con código 0
