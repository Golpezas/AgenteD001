# CI Pipeline — Especificación

## Propósito

Definir el pipeline de integración continua con GitHub Actions que ejecuta tests y verifica cobertura en cada push y pull request a main.

## Capacidades

- `ci-pipeline`: Pipeline CI/CD con GitHub Actions para build, test y coverage del backend y frontend

## Requisitos

### R-CI01: Disparo del pipeline

El sistema DEBE ejecutar el pipeline automáticamente en eventos `push` y `pull_request` dirigidos a la rama `main`.

#### Escenario: Push a main

- DADO que se realiza un push a `main`
- CUANDO GitHub Actions procesa el evento
- ENTONCES el pipeline DEBE iniciar automáticamente
- Y DEBE ejecutar todos los jobs definidos

#### Escenario: PR a main

- DADO que se abre un pull request contra `main`
- CUANDO GitHub Actions procesa el evento
- ENTONCES el pipeline DEBE ejecutarse para validar el código propuesto

### R-CI02: Job backend-test

El sistema DEBE ejecutar un job `backend-test` que configure Python 3.12+, instale dependencias desde `backend/requirements.txt`, ejecute `pytest --cov=app --cov-report=term-missing --cov-fail-under=80`, y falle si la cobertura es menor al 80%.

#### Escenario: Cobertura suficiente

- DADO que el pipeline corre para cambios con cobertura ≥ 80%
- CUANDO se ejecuta `pytest --cov=app --cov-fail-under=80`
- ENTONCES el job DEBE pasar con código 0

#### Escenario: Cobertura insuficiente

- DADO que el pipeline corre para cambios con cobertura < 80%
- CUANDO se ejecuta `pytest --cov=app --cov-fail-under=80`
- ENTONCES el job DEBE fallar con código distinto de 0
- Y DEBE mostrar el reporte de cobertura

### R-CI03: Job frontend-test

El sistema DEBE ejecutar un job `frontend-test` que configure Node.js 20+, instale dependencias en `frontend/`, ejecute `npx tsc --noEmit` (verificación de tipos) y `npx vitest run` (tests unitarios). El job DEBE fallar si alguno de los dos comandos falla.

#### Escenario: TypeScript y tests pasan

- DADO que el pipeline corre para cambios frontend válidos
- CUANDO se ejecuta `tsc --noEmit && vitest run`
- ENTONCES ambos comandos DEBEN pasar con código 0

#### Escenario: Error de tipos

- DADO que el pipeline corre para cambios con error de tipos TypeScript
- CUANDO se ejecuta `tsc --noEmit`
- ENTONCES el job DEBE fallar con código distinto de 0
- Y NO DEBE ejecutar `vitest run`
