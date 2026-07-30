# Delta para backend-testing

## ADDED Requirements

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
