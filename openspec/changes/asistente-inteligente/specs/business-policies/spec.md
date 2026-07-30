# Business Policies — Especificación

## Propósito

Modelar políticas comerciales: descuentos, beneficios, financiamiento y reglas generales. Cada política se tipifica y puede incluir condiciones en JSONB para flexibilidad. Aplica a productos y segmentos de clientes con vigencia temporal.

## Requisitos

### R-BP01: Modelo BusinessPolicy

El sistema DEBE proveer un modelo `BusinessPolicy` con: `id` (UUID, PK), `name` (VARCHAR, NOT NULL), `policy_type` (VARCHAR, NOT NULL — "discount", "benefit", "financing", "policy"), `description` (TEXT, nullable), `value` (DECIMAL, nullable), `value_type` (VARCHAR, nullable — "percentage", "fixed_amount"), `conditions` (JSONB, nullable), `client_type` (VARCHAR, nullable — "pre-sep-2025", "post-sep-2025"), `is_active` (BOOLEAN, default true), `effective_from` (TIMESTAMP, nullable), `effective_to` (TIMESTAMP, nullable), `created_at`, `updated_at`.

#### Escenario: Crear descuento porcentual

- DADO que se define "Canal Digital" 10% OFF
- CUANDO se crea BusinessPolicy con policy_type="discount", value=10.0, value_type="percentage"
- ENTONCES la respuesta DEBE ser 201 Created
- Y is_active DEBE ser true por defecto

#### Escenario: Política con vigencia acotada

- DADO una política con effective_from y effective_to definidos
- CUANDO se consultan políticas vigentes fuera de ese rango
- ENTONCES la política NO DEBE aparecer

#### Escenario: Condiciones de financiamiento en JSONB

- DADO una política financing con conditions={"installments": 4, "interest_free": true}
- CUANDO se consulta por id
- ENTONCES conditions DEBE contener el JSON completo

### R-BP02: Consulta de políticas

El sistema DEBE exponer GET `/api/v1/business-policies` con filtros por `policy_type`, `is_active` y `client_type`. Paginación estándar (items, total, page, per_page).

#### Escenario: Filtrar por tipo descuento

- DADO políticas "discount", "benefit" y "financing"
- CUANDO se GET `/api/v1/business-policies?policy_type=discount`
- ENTONCES la respuesta DEBE contener solo descuentos

#### Escenario: Políticas para clientes legacy

- DADO políticas con client_type="pre-sep-2025" y "post-sep-2025"
- CUANDO se GET `/api/v1/business-policies?client_type=pre-sep-2025`
- ENTONCES la respuesta DEBE incluir solo políticas para ese segmento

#### Escenario: Política inactiva excluida por defecto

- DADO una política con is_active=false
- CUANDO se GET `/api/v1/business-policies` sin filtro is_active
- ENTONCES la política inactiva NO DEBE aparecer

### R-BP03: Seed data de políticas

El sistema DEBE incluir seed data con al menos 10 políticas que cubran los cuatro tipos:

| Nombre | Tipo | Valor |
|--------|------|-------|
| Canal Digital | discount | 10% OFF |
| Alianza | discount | 20% OFF |
| Corporativo MB10 | discount | 15% OFF |
| Pago anual anticipado | benefit | 10% OFF |
| Bonificación nuevos clientes | benefit | 30% OFF licenciamiento |
| 4 pagos sin interés | financing | conditions JSON |
| 25% TF + 75% IPC 12 meses | financing | conditions JSON |
| Débito automático mandatorio | policy | — |
| Permanencia mínima 6 meses | policy | — |
| Precio asegurado 4 meses | policy | — |

#### Escenario: Seed cargada correctamente

- DADO que la migración con seed se ejecutó
- CUANDO se GET `/api/v1/business-policies?per_page=50`
- ENTONCES la respuesta DEBE contener al menos 10 políticas
- Y "Canal Digital" DEBE tener value=10.0 y value_type="percentage"
