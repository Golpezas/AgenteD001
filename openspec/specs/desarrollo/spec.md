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

### R-BT01: Cobertura de código con pytest-cov

El sistema DEBE incluir `pytest-cov` como dependencia de desarrollo en `backend/requirements.txt`. La configuración de cobertura DEBE definir un umbral mínimo del 80% en `backend/pyproject.toml` usando las opciones `--cov=app --cov-report=term-missing --cov-fail-under=80`.

#### Escenario: Cobertura mínima configurada

- DADO que `pytest-cov` está instalado
- CUANDO se ejecuta `pytest --cov=app --cov-fail-under=80` en `backend/`
- ENTONCES el comando DEBE ejecutarse sin error de configuración
- Y DEBE reportar el porcentaje de cobertura de `app/`

#### Escenario: Cobertura falla bajo 80%

- DADO que existe una refactorización sin tests que reduce la cobertura
- CUANDO se ejecuta `pytest --cov=app --cov-fail-under=80`
- ENTONCES DEBE fallar con código distinto de 0 si la cobertura es menor a 80%

### R-BT02: Tests de PriceList endpoints

El sistema DEBE incluir tests de API para los endpoints CRUD de PriceList, PriceListItem y PricingRule en `backend/tests/test_api.py`. Los tests DEBEN usar el fixture `client` (AsyncClient) y `db_session` existentes, y ejecutarse con `pytest --asyncio-mode=auto`. Cada conjunto DEBE probar create, list, get by id, update y delete.

#### Escenario: PriceList CRUD completo

- DADO los fixtures `client` y `db_session` disponibles
- CUANDO se ejecutan los tests de `TestPriceListEndpoint`
- ENTONCES DEBEN probar: creación (201), listado paginado (200), obtención por ID (200), actualización (200), y soft delete (200)
- Y todos los tests DEBEN pasar

#### Escenario: PriceListItem CRUD con filtros

- DADO un PriceList y un Product existentes en la base de datos de test
- CUANDO se ejecutan los tests de `TestPriceListItemEndpoint`
- ENTONCES DEBEN probar creación, listado filtrable por `price_list_id` y `product_id`, actualización y eliminación
- Y todos los tests DEBEN pasar

#### Escenario: PricingRule CRUD con filtros

- DADO una Company existente en la base de datos de test
- CUANDO se ejecutan los tests de `TestPricingRuleEndpoint`
- ENTONCES DEBEN probar creación, listado filtrable por `company_id` y `product_id`, actualización y eliminación
- Y todos los tests DEBEN pasar
