# Desarrollo — Especificación

## Propósito

Definir la documentación inicial del proyecto para onboarding de desarrolladores.

## Capacidades

- `dev-docs`: DEV_SETUP.md, .env.example

## Requisitos

### R-D01: DEV_SETUP.md

El sistema DEBE incluir `docs/DEV_SETUP.md` con instrucciones claras para: clonar el repositorio, configurar variables de entorno (copiar `.env.example` a `.env`), levantar el stack con Docker (`docker compose up --build`), acceder al backend (`http://localhost:8000/docs`), acceder al frontend (`http://localhost:5173`), ejecutar migraciones de base de datos (`alembic upgrade head`), y detener el stack (`docker compose down`).

#### Escenario: Instrucciones completas

- DADO que `docs/DEV_SETUP.md` existe
- CUANDO se lee el documento
- ENTONCES DEBE incluir las secciones: Requisitos, Instalación, Uso con Docker, Desarrollo local (opcional), y Comandos útiles

### R-D02: .env.example

El sistema DEBE incluir `.env.example` en la raíz del proyecto con todas las variables de entorno necesarias para el stack:

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `POSTGRES_USER` | `agented` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `agented_pass` | Contraseña de PostgreSQL |
| `POSTGRES_DB` | `agented` | Nombre de base de datos |
| `DATABASE_URL` | `postgresql+asyncpg://...` | URL de conexión SQLAlchemy |
| `SECRET_KEY` | `change-me-in-production` | Clave secreta para JWT (futuro) |
| `ENVIRONMENT` | `development` | Entorno (dev/staging/prod) |

Las variables sin valor asignado DEBEN contener un valor de ejemplo o placeholder. El archivo `.env.example` NO DEBE contener valores sensibles reales.

#### Escenario: Variables completas y documentadas

- DADO que `.env.example` existe en la raíz
- CUANDO se inspecciona el archivo
- ENTONCES DEBE listar todas las variables requeridas
- Y cada variable DEBE tener un comentario explicativo
- Y `.env.example` DEBE estar en la raíz del proyecto, no en subdirectorios

#### Escenario: .env.example ignorado por git

- DADO que el proyecto usa git
- CUANDO se inspecciona `.gitignore`
- ENTONCES `.env` DEBE estar en la lista de ignorados
- Y `.env.example` NO DEBE estar ignorado
