# Delta para API Productos

## ADDED Requirements

### R-P05: Familias y categorías como valores controlados

El sistema DEBE validar que `family` y `category` en Product estén en listados controlados: `family`: "Zeus", "Balcony", "MasPedidos", "Prescriptor", "Pidea", "CASH", "Servicios Globales", "Otros". `category`: "software", "hardware", "servicio", "suscripcion", "consultoria", "capacitacion", "marketplace". Valores fuera de estos listados DEBEN rechazarse con 422.

#### Escenario: Producto con familia válida

- DADO que existe el catálogo de familias seed
- CUANDO se crea un producto con family="Zeus", category="software"
- ENTONCES el producto DEBE crearse exitosamente con esos valores

#### Escenario: Familia no válida

- DADO que las familias permitidas son las del catálogo
- CUANDO se crea un producto con family="Inexistente"
- ENTONCES la respuesta DEBE ser 422 Unprocessable Entity

### R-P06: Endpoints de factores de licenciamiento

El sistema DEBE exponer GET `/api/v1/products/{id}/factors` (factores aplicables) y GET `/api/v1/products/{id}/price-with-factors?technology_tier=X` (precio calculado con factores).

#### Escenario: Factores aplicables a un producto

- DADO un producto existente y factores en pricing-engine
- CUANDO se GET `/api/v1/products/{id}/factors?technology_tier=Express`
- ENTONCES la respuesta DEBE listar factores con concept_key y factor

#### Escenario: Precio calculado con factores

- DADO un producto con base_price=1000.00 y factores "Express"
- CUANDO se GET `/api/v1/products/{id}/price-with-factors?technology_tier=Express`
- ENTONCES la respuesta DEBE incluir base_price, factores y total

## MODIFIED Requirements

### R-P01: Modelo Product

El sistema DEBE proveer un modelo SQLAlchemy `Product` con: `id` (UUID, PK), `company_id` (UUID, FK → Company, nullable), `sku` (VARCHAR, unique), `name` (VARCHAR, NOT NULL), `description` (TEXT, nullable), `category` (VARCHAR, nullable — valores controlados: "software", "hardware", "servicio", "suscripcion", "consultoria", "capacitacion", "marketplace"), `family` (VARCHAR, nullable — valores controlados: "Zeus", "Balcony", "MasPedidos", "Prescriptor", "Pidea", "CASH", "Servicios Globales", "Otros"), `unit` (VARCHAR, nullable), `metadata` (JSONB, nullable), `is_active` (BOOLEAN, default true), `created_at`, `updated_at`.
(Anteriormente: sin campo family, category como VARCHAR libre)

#### Escenario: Crear producto con familia y categoría

- DADO una empresa existente con `id` conocido
- CUANDO POST `/api/v1/products` con company_id, sku="PROD-001", name="Consultoría Premium", family="Zeus", category="consultoria"
- ENTONCES 201 Created con family="Zeus" y category="consultoria"

#### Escenario: SKU duplicado

- DADO que existe un producto con SKU "PROD-001"
- CUANDO se intenta crear otro con el mismo SKU
- ENTONCES 409 Conflict indicando que el SKU ya existe

#### Escenario: Migración segura con columna nullable

- DADO productos existentes sin `company_id`
- CUANDO se ejecuta la migración Alembic
- ENTONCES `company_id` DEBE ser nullable y productos existentes DEBEN mantener NULL
- Y `alembic downgrade -1` DEBE revertir sin pérdida

### R-P04: Endpoints CRUD

El sistema DEBE exponer endpoints REST:

| Modelo | Métodos |
|--------|---------|
| Product | GET list, POST, GET by id, PUT, DELETE |
| PriceList | GET list, POST, GET by id, PUT, DELETE |
| PriceListItem | GET list (filtrable), POST, PUT, DELETE |
| PricingRule | GET list (filtrable), POST, PUT, DELETE |
| CalculationFactor | GET list (filtrable, solo lectura desde api-productos) |
| BusinessPolicy | GET list (filtrable, solo lectura desde api-productos) |

Paginado: items, total, page, per_page.
(Anteriormente: sin filas CalculationFactor ni BusinessPolicy)

#### Escenario: Listar items por lista de precios

- DADO 15 items en "Lista Standard" y 5 en "Lista VIP"
- CUANDO GET `/api/v1/price-list-items?price_list_id=<id>&page=1&per_page=10`
- ENTONCES 10 items, total=15, todos de "Lista Standard"

#### Escenario: Soft delete en producto

- DADO un producto activo con `id` conocido
- CUANDO DELETE `/api/v1/products/{id}`
- ENTONCES 200 OK e is_active=false
- Y price_list_items asociados NO DEBEN eliminarse en cascada
