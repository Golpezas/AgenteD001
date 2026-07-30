# Pricing Engine — Especificación

## Propósito

Modelar factores de licenciamiento que determinan multiplicadores de precio por concepto y technology tier (Express, Advanced, Premium). Cada factor es un valor numérico (x5, x2, x1, x6, x3) que se aplica al precio base de productos según el concepto de licenciamiento.

## Requisitos

### R-PE01: Modelo CalculationFactor

El sistema DEBE proveer un modelo `CalculationFactor` con: `id` (UUID, PK), `concept_key` (VARCHAR, NOT NULL — ej: "accesos_simultaneos"), `concept_name` (VARCHAR, NOT NULL), `technology_tier` (VARCHAR, NOT NULL — "Express", "Advanced", "Premium"), `factor` (DECIMAL, nullable — null si requiere cotización), `is_available` (BOOLEAN, default true), `metadata` (JSONB, nullable), `created_at`, `updated_at`. La tupla (concept_key, technology_tier) DEBE ser única.

#### Escenario: Crear factor de licenciamiento

- DADO que no existe un factor para "accesos_simultaneos" en "Express"
- CUANDO se crea con concept_key="accesos_simultaneos", technology_tier="Express", factor=5.0
- ENTONCES el factor DEBE persistirse con factor=5.0
- Y la tupla (concept_key, technology_tier) DEBE ser única

#### Escenario: Concepto no disponible para un tier

- DADO "alta_nuevo_tintometrico" en "Express" con is_available=false
- CUANDO se consultan factores disponibles para "Express"
- ENTONCES ese factor NO DEBE aparecer en resultados

#### Escenario: Factor requiere cotización

- DADO "horas_dba" con is_available=false y metadata={"requires_quote": true}
- CUANDO se consulta por concept_key + technology_tier
- ENTONCES la respuesta DEBE incluir metadata con requires_quote=true
- Y factor DEBE ser null

### R-PE02: Consulta de factores

El sistema DEBE exponer GET `/api/v1/calculation-factors` con filtros `technology_tier` y `concept_key`. Por defecto DEBE excluir factores con is_available=false. El parámetro `include_unavailable=true` DEBE permitir incluirlos.

#### Escenario: Filtrar por technology_tier

- DADO factores cargados para "Express", "Advanced" y "Premium"
- CUANDO se GET `/api/v1/calculation-factors?technology_tier=Advanced`
- ENTONCES la respuesta DEBE contener solo factores "Advanced"

#### Escenario: Incluir no disponibles

- DADO factores con is_available=false existentes
- CUANDO se GET `/api/v1/calculation-factors?include_unavailable=true`
- ENTONCES la respuesta DEBE incluir factores no disponibles con su metadata

#### Escenario: Paginación estándar

- DADO 20+ factores cargados
- CUANDO se GET `/api/v1/calculation-factors?page=1&per_page=10`
- ENTONCES la respuesta DEBE contener 10 items y total DEBE ser el conteo correcto

### R-PE03: Cálculo de precio con factores

El sistema DEBE calcular el precio final de un producto multiplicando su `base_price` por el factor de cada concepto aplicable. Si un concepto tiene is_available=false, el sistema NO DEBE incluirlo en el cálculo y DEBE advertirlo.

#### Escenario: Precio con factor x5

- DADO un producto con base_price=1000.00 y factor 5.0 para "accesos_simultaneos"
- CUANDO se solicita el cálculo
- ENTONCES el resultado DEBE ser 5000.00

#### Escenario: Concepto no disponible en cálculo

- DADO un concepto con is_available=false para el tier solicitado
- CUANDO se solicita el cálculo incluyendo ese concepto
- ENTONCES el sistema DEBE responder 400 Bad Request
- Y DEBE indicar que el concepto no está disponible
