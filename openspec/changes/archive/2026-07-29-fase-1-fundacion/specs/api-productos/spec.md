# API Productos — Especificación

## Propósito

Definir el API REST CRUD de productos, price_list_items y pricing_rules con modelos configurables por negocio.

## Capacidades

- `products-crud`: API REST CRUD de productos, price_list_items y pricing_rules

## Requisitos

### R-P01: Modelo Product

El sistema DEBE proveer un modelo SQLAlchemy `Product` con campos: `id` (UUID, PK), `company_id` (UUID, FK → Company), `sku` (VARCHAR, unique), `name` (VARCHAR, NOT NULL), `description` (TEXT, nullable), `category` (VARCHAR, nullable), `unit` (VARCHAR, nullable, ej: "unidad", "kg", "hora"), `metadata` (JSONB, nullable), `is_active` (BOOLEAN, default true), `created_at` (TIMESTAMP), `updated_at` (TIMESTAMP).

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

### R-P02: Modelo PriceListItem

El sistema DEBE proveer un modelo `PriceListItem` con campos: `id` (UUID, PK), `product_id` (UUID, FK → Product), `price_list_id` (UUID, FK → PriceList), `base_price` (DECIMAL, NOT NULL), `currency` (VARCHAR, default "ARS"), `min_quantity` (INTEGER, default 1), `max_quantity` (INTEGER, nullable), `is_active` (BOOLEAN, default true), `created_at`, `updated_at`, y un modelo `PriceList` con `id`, `name` (VARCHAR, NOT NULL), `company_id`, `is_active`, `created_at`, `updated_at`.

#### Escenario: Crear item en lista de precios

- DADO un producto y una lista de precios existentes
- CUANDO se hace POST a `/api/v1/price-list-items` con `{"product_id": "<id>", "price_list_id": "<id>", "base_price": 1500.00}`
- ENTONCES la respuesta DEBE ser 201 Created
- Y el item DEBE reflejar el `base_price` y `currency` por defecto "ARS"

### R-P03: Modelo PricingRule

El sistema DEBE proveer un modelo `PricingRule` con campos: `id` (UUID, PK), `company_id` (UUID, FK → Company, nullable), `product_id` (UUID, FK → Product, nullable), `rule_type` (VARCHAR, NOT NULL — ej: "discount", "markup", "tiered"), `conditions` (JSONB, nullable), `value` (DECIMAL, NOT NULL), `priority` (INTEGER, default 0), `is_active`, `created_at`, `updated_at`.

#### Escenario: Regla aplicable a todos los productos de una empresa

- DADO una empresa con `id` conocido
- CUANDO se crea una regla con `company_id` establecido y `product_id` nulo
- ENTONCES la regla DEBE aplicar a todos los productos de esa empresa
- Y el campo `rule_type` DEBE determinar cómo se aplica la regla

### R-P04: Endpoints CRUD

El sistema DEBE exponer endpoints REST para cada modelo:

| Modelo | Métodos |
|--------|---------|
| Product | GET list, POST, GET by id, PUT, DELETE |
| PriceList | GET list, POST, GET by id, PUT, DELETE |
| PriceListItem | GET list (filtrable por price_list_id y product_id), POST, PUT, DELETE |
| PricingRule | GET list (filtrable por company_id y product_id), POST, PUT, DELETE |

El paginado DEBE seguir el mismo formato que companies-crud (items, total, page, per_page).

#### Escenario: Listar items de precio por lista

- DADO que existen 15 items en "Lista Standard" y 5 en "Lista VIP"
- CUANDO se hace GET a `/api/v1/price-list-items?price_list_id=<standard_id>&page=1&per_page=10`
- ENTONCES la respuesta DEBE contener 10 items
- Y `total` DEBE ser 15
- Y todos los items DEBEN pertenecer a "Lista Standard"

#### Escenario: Soft delete en producto

- DADO un producto activo con `id` conocido
- CUANDO se hace DELETE a `/api/v1/products/{id}`
- ENTONCES la respuesta DEBE ser 200 OK
- Y `is_active` DEBE ser `false`
- Y los price_list_items asociados NO DEBEN eliminarse en cascada
