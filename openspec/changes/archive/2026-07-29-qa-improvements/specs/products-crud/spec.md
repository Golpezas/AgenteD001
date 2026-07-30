# Delta para products-crud

## MODIFIED Requirements

### R-P01: Modelo Product

El sistema DEBE proveer un modelo SQLAlchemy `Product` con campos: `id` (UUID, PK), `company_id` (UUID, FK → Company, nullable para migración), `sku` (VARCHAR, unique), `name` (VARCHAR, NOT NULL), `description` (TEXT, nullable), `category` (VARCHAR, nullable), `unit` (VARCHAR, nullable, ej: "unidad", "kg", "hora"), `metadata` (JSONB, nullable), `is_active` (BOOLEAN, default true), `created_at` (TIMESTAMP), `updated_at` (TIMESTAMP).
(Previously: company_id sin especificar nulabilidad ni estrategia de migración)

#### Escenario: Crear producto asociado a empresa

- DADO una empresa existente con `id` conocido
- CUANDO se hace POST a `/api/v1/products` con `{"company_id": "<id>", "sku": "PROD-001", "name": "Consultoría Premium"}`
- ENTONCES la respuesta DEBE ser 201 Created
- Y el producto DEBE quedar asociado a la empresa indicada

#### Escenario: SKU duplicado

- DADO que existe un producto con SKU "PROD-001"
- CUANDO se intenta crear otro producto con el mismo SKU
- ENTONCES la respuesta DEBE ser 409 Conflict
- Y DEBE indicar que el SKU ya existe

#### Escenario: Migración segura con columna nullable

- DADO que la base de datos tiene productos existentes sin `company_id`
- CUANDO se ejecuta la nueva migración Alembic
- ENTONCES la columna `company_id` DEBE agregarse como nullable
- Y los productos existentes DEBEN mantener su valor `NULL` en `company_id`
- Y `alembic downgrade -1` DEBE revertir la columna sin pérdida de datos

## ADDED Requirements

### R-P01a: Schema ProductCreate con company_id opcional

El sistema DEBE aceptar `company_id` como campo opcional en `ProductCreate` para mantener compatibilidad con clientes existentes que aún no envían el campo. Si no se provee, DEBE almacenarse como `NULL`.

#### Escenario: Crear producto sin company_id

- DADO que el schema `ProductCreate` existe
- CUANDO se hace POST a `/api/v1/products` sin incluir `company_id`
- ENTONCES la respuesta DEBE ser 201 Created
- Y `company_id` en la respuesta DEBE ser `null`

#### Escenario: Crear producto con company_id válido

- DADO una empresa existente
- CUANDO se hace POST a `/api/v1/products` con `company_id` válido
- ENTONCES la respuesta DEBE ser 201 Created
- Y `company_id` DEBE coincidir con el valor enviado
