# API Clientes — Especificación

## Propósito

Definir el API REST CRUD de empresas/clientes con un modelo de datos genérico y sin acoplamiento a plataformas externas.

## Capacidades

- `companies-crud`: API REST CRUD de empresas/clientes (modelo genérico)

## Requisitos

### R-C01: Modelo Company

El sistema DEBE proveer un modelo SQLAlchemy `Company` con los campos: `id` (UUID, PK), `name` (VARCHAR, NOT NULL), `legal_name` (VARCHAR, nullable), `tax_id` (VARCHAR, nullable), `email` (VARCHAR, nullable), `phone` (VARCHAR, nullable), `address` (TEXT, nullable), `metadata` (JSONB, nullable), `is_active` (BOOLEAN, default true), `created_at` (TIMESTAMP, NOT NULL), `updated_at` (TIMESTAMP, NOT NULL). El modelo NO DEBE tener acoplamiento a plataformas CRM/ERP específicas.

### R-C02: Endpoints CRUD

El sistema DEBE exponer los siguientes endpoints REST para `Company`:

| Método | Ruta | Comportamiento |
|--------|------|----------------|
| GET | `/api/v1/companies` | Listar empresas (soporta paginación, búsqueda por `name`) |
| POST | `/api/v1/companies` | Crear empresa |
| GET | `/api/v1/companies/{id}` | Obtener empresa por ID |
| PUT | `/api/v1/companies/{id}` | Actualizar empresa (reemplazo completo) |
| DELETE | `/api/v1/companies/{id}` | Eliminar empresa (soft delete: `is_active = false`) |

#### Escenario: Listar empresas paginado

- DADO que existen 25 empresas activas en la base de datos
- CUANDO se hace GET a `/api/v1/companies?page=1&per_page=10`
- ENTONCES la respuesta DEBE ser 200 OK
- Y DEBE retornar un objeto con `items` (array de 10 empresas), `total` (25), `page` (1), `per_page` (10)

#### Escenario: Crear empresa válida

- DADO un payload JSON con `{"name": "Tech Corp", "tax_id": "30-12345678-9"}`
- CUANDO se hace POST a `/api/v1/companies`
- ENTONCES la respuesta DEBE ser 201 Created
- Y el body DEBE incluir el `id` generado, `name`, `tax_id`, `created_at` y `updated_at`

#### Escenario: Crear empresa sin nombre

- DADO un payload JSON sin el campo `name`
- CUANDO se hace POST a `/api/v1/companies`
- ENTONCES la respuesta DEBE ser 422 Unprocessable Entity
- Y DEBE incluir un mensaje de validación indicando que `name` es requerido

#### Escenario: Obtener empresa inexistente

- DADO un UUID que no corresponde a ninguna empresa
- CUANDO se hace GET a `/api/v1/companies/{uuid}`
- ENTONCES la respuesta DEBE ser 404 Not Found

#### Escenario: Eliminar empresa (soft delete)

- DADO una empresa activa con `id` conocido
- CUANDO se hace DELETE a `/api/v1/companies/{id}`
- ENTONCES la respuesta DEBE ser 200 OK
- Y el campo `is_active` DEBE ser `false`
- Y la empresa NO DEBE aparecer en listados por defecto

### R-C03: Servicio Repository + Service Layer

El sistema DEBE implementar el patrón Repository para acceso a datos y Service Layer para lógica de negocio de Company. El Repository DEBE operar sobre el modelo SQLAlchemy. El Service Layer DEBE ser inyectado en los endpoints de FastAPI.

#### Escenario: Service Layer desacopla endpoint de DB

- DADO un endpoint de companies que usa el Service Layer
- CUANDO se invoca el endpoint
- ENTONCES el endpoint NO DEBE acceder directamente al modelo SQLAlchemy
- Y DEBE hacerlo a través del service correspondiente
