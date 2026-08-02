# Design: Análisis de Imágenes y URLs

## Technical Approach

Pipeline multimodal que procesa imágenes (optimización Pillow + Gemini Vision API) y URLs (scraping HTML con BeautifulSoup + screenshot con PixelRAGService + Gemini Vision). La ejecución es asíncrona mediante FastAPI `BackgroundTasks` y jobs en segundo plano encolados, complementados con APScheduler para monitoreo periódico de `ScrapedSource` activas. Los resultados se guardan como propuestas en estado pendiente que el usuario puede aceptar o rechazar desde el frontend (`/analysis`), evitando auto-persistencia en datos de producción.

## Architecture Decisions

| Decisión | Alternativas | Rationale |
|---|---|---|
| **Gemini Vision sobre OpenAI** | OpenAI GPT-4o, Anthropic Claude | Costo (capa gratuita 60 req/min), calidad multimodal nativa y alineación con stack del proyecto. |
| **BackgroundTasks vs Celery** | Celery con Redis, In-process Queue | Menor complejidad de infraestructura, reutiliza el patrón existente del scheduler y no requiere workers adicionales. |
| **Modelos dedicados vs Reutilizar Notification** | Reutilizar Notification | Modelos específicos (`AnalysisJob`, `AnalysisResult`, `ScrapedSource`) permiten tracking de estados, confianza y datos estructurados. |
| **Propuesta intermedia vs Auto-persistir** | Auto-persistir directo | Evita contaminación de catálogos con datos alucinados; el usuario revisa y aprueba explícitamente. |
| **Frontend: Página nueva vs Modal** | Modal flotante | Permite visualización tabular de historial, vista previa de propuestas y gestión de fuentes de scraping en una interfaz dedicada (`/analysis`). |

## Data Flow

```
Usuario → Frontend (/analysis - Subir imagen / Registrar URL)
      → API POST /api/v1/analysis/jobs
      → AnalysisService.create_job() (Estado: pending)
      → BackgroundTasks (Ejecución asíncrona)
           ├─ Imagen: Pillow optimize → Gemini Vision API → JSON Pydantic
           ├─ URL: httpx/BS4 scrape + PixelRAG capture_for_analysis() → Gemini Vision API
           └─ Validación & Guardado → AnalysisResult (status=proposal)
      → NotificationService.create("Nueva propuesta de análisis disponible")
      → Usuario revisa en UI → Acepta / Rechaza → Upsert condicional a tablas finales
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/analysis.py` | Create | Modelos SQLAlchemy: `AnalysisJob`, `AnalysisResult`, `ScrapedSource`. |
| `backend/app/schemas/analysis.py` | Create | Schemas Pydantic para validación de entrada/salida y contratos Gemini. |
| `backend/app/repositories/analysis.py` | Create | Repositorios async para jobs, resultados y fuentes. |
| `backend/app/services/pixelrag.py` | Modify | Agregar método `capture_for_analysis(url) -> ScreenshotResult`. |
| `backend/app/services/analysis/` | Create | Servicios de pipeline: `gemini_client.py`, `scraper.py`, `orchestrator.py`. |
| `backend/app/api/analysis.py` | Create | Endpoints FastAPI para jobs, subida, URLs y aceptación de propuestas. |
| `backend/app/scheduler.py` | Modify | Integrar job periódico de APScheduler para monitorear `ScrapedSource` activas. |
| `backend/app/main.py` | Modify | Registrar router de analysis. |
| `backend/requirements.txt` | Modify | Añadir dependencias (`google-genai`, `Pillow`, `beautifulsoup4`, `lxml`). |
| `frontend/src/types/index.ts` | Modify | Tipos TypeScript para jobs, resultados y propuestas. |
| `frontend/src/hooks/useAnalysis.ts` | Create | Hook React para consultar estado, crear jobs y aceptar propuestas. |
| `frontend/src/components/analysis/` | Create | Componentes UI (FileList, ProposalCard, SourceManager). |
| `frontend/src/pages/Analysis.tsx` | Create | Página principal de análisis y revisión. |
| `frontend/src/App.tsx` | Modify | Agregar ruta `/analysis`. |

## Interfaces / Contracts

```python
# Pydantic schema principal de extracción
class AnalysisProposal(BaseModel):
    product_name: str
    extracted_price: float
    confidence_score: float = Field(ge=0.0, le=1.0)
    raw_data: dict
```

```typescript
// TypeScript interface para propuestas
export interface AnalysisResult {
  id: string;
  jobId: string;
  status: 'proposal' | 'accepted' | 'rejected';
  extractedData: {
    productName: string;
    price: number;
    confidenceScore: number;
  };
  createdAt: string;
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Extracción Gemini & Pydantic | Mocks de Gemini API con respuestas JSON válidas e inválidas. |
| Integration | Endpoints y BackgroundTasks | Test client de FastAPI verificando respuesta 202 y creación de jobs. |
| Integration | PixelRAG `capture_for_analysis` | Verificando retorno de `ScreenshotResult` con metadatos y bytes PNG. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundaries.

## Migration / Rollout

Tabla nueva (`analysis_jobs`, `analysis_results`, `scraped_sources`) mediante Alembic automigrations en lifespan. Sin migración de datos previos.

---

# PR3 — Diseño del slice (API + scheduler + frontend)

**Contexto**: PR1 (foundation: modelos/schemas/repos) merged; PR2 (core services: gemini, scraper, orchestrator, `capture_for_analysis`) aprobado en `feature/analisis-imagenes-urls-pr2`. PR3 integra la capa HTTP, el scheduler de monitoreo, el cierre de R-X03 y el frontend. Este diseño resuelve los gaps detectados en la exploración PR3 (Engram obs #83).

## D1. Migración Alembic 005

**Decisión**: migración manual `005_add_analysis_tables.py` (estilo de `004_add_notifications.py`) + import de modelos en `migrations/env.py`. Las tablas hoy solo existen vía `create_all` en tests; la API fallaría en Postgres real sin esto.

- `analysis_jobs`: `id` UUID PK (default Python `gen_uuid`, sin server_default — patrón 004), `job_type` String(20) NOT NULL, `input_data` JSON NOT NULL, `status` String(20) server_default `'pending'`, `started_at`/`completed_at` DateTime(tz) NULL, `result_id` UUID NULL, `error_message` Text NULL, `is_active` server_default true, `created_at`/`updated_at` server_default `func.now()`.
- `analysis_results`: `id` UUID PK, `job_id` UUID FK→`analysis_jobs.id` ON DELETE CASCADE NOT NULL, `status` String(20) server_default `'proposal'`, `product_name` String(255) NULL, `extracted_price` Float NULL, `currency` String(3) NULL, `confidence_score` Float NULL, `raw_data`/`proposal_data` JSON NULL, mixins.
- `scraped_sources`: `id` UUID PK, `url` String(2048) NOT NULL **UNIQUE** (constraint de `unique=True` del modelo), `name` String(255) NULL, `schedule_interval_minutes` Integer NULL, `last_analyzed_at` DateTime(tz) NULL, mixins.
- Índices por patrón de consulta real (no declarados en el modelo, se agregan solo en migración): `ix_analysis_jobs_status`, `ix_analysis_results_status`, `ix_analysis_results_job_id`, `ix_scraped_sources_is_active`.
- `env.py`: agregar `from app.models.analysis import AnalysisJob, AnalysisResult, ScrapedSource  # noqa: F401`.
- **Validación**: sin test unitario (el conftest usa `create_all` sobre sqlite con `TEST_DATABASE_URL` hardcodeada, ignorando `DATABASE_URL`); se valida con `alembic upgrade head` contra Postgres real (docker) y suite completa verde. El quirk del conftest queda documentado como follow-up (a).

## D2. Cierre de R-X03 — gating de producción + registry de estado

**Decisión**: nuevo singleton `backend/app/services/analysis/pipeline_state.py` + `count_by_status` en el repo + rework de `api/pixelrag.py`.

- `AnalysisPipelineState`: `active: bool = False`, `last_successful_run: datetime | None = None`; métodos `mark_active()`, `mark_success(when=None)`, `is_registered()` (`active or last_successful_run is not None`), `snapshot() -> dict | None`. Instancia de módulo `pipeline_state`.
- Escritores: `start_scheduler()` llama `mark_active()` al registrar el job `analysis_monitor`; `AnalysisOrchestrator.process_job()` llama `mark_success()` al completar con éxito (1 línea + import en código PR2).
- `AnalysisJobRepository.count_by_status(status: str) -> int` — `SELECT count(*) FROM analysis_jobs WHERE status = ? AND is_active = true`. RED en `tests/repositories/test_analysis_repo.py` (NO duplicar el archivo — ya existe con 17 tests, S-2).
- `GET /api/v1/pixelrag/test` (modificar): si `settings.environment == "production"` → `HTTPException(404)`; si no, comportamiento actual (200/500) y, cuando `pipeline_state.is_registered()`, agregar bloque `analysis_pipeline` con `active`, `last_successful_run` (ISO string) y `pending_jobs` (vía `count_by_status("pending")` con `Depends(get_db)`). Pipeline no registrado → bloque omitido.
- Tests (extender `tests/test_pixelrag.py` con fixtures `override_get_db` + `client` del patrón de `test_api_notifications.py`, y reset del singleton por test): 200 + campos presentes con pipeline registrado; campos ausentes sin registro; 404 con `environment=production` (monkeypatch `settings.environment`); 500 existente se mantiene.

## D3. Schemas y endpoints ScrapedSource

**Decisión**: agregar a `schemas/analysis.py` `ScrapedSourceCreate`, `ScrapedSourceResponse`, `ScrapedSourceList` (lista paginada, mismo shape que `AnalysisJobList`). `url` como `str` validado (min_length 1, max 2048), **no** `HttpUrl`: Pydantic normalizaría (slash final, punycode) y rompería el match exacto de `get_by_url` sobre la columna UNIQUE.

- `POST /api/v1/analysis/sources` → 201 `ScrapedSourceResponse`; 409 si `get_by_url` ya existe.
- `GET /api/v1/analysis/sources` → 200 `ScrapedSourceList` paginado (`page`, `per_page`).
- `DELETE /api/v1/analysis/sources/{id}` → 204 soft delete (`soft_delete`); 404 si no existe.

## D4. Transporte de subida de imagen: base64-JSON

**Decisión**: **base64-JSON** (descartado multipart).

| Opción | Tradeoff | Decisión |
|---|---|---|
| base64-JSON | +33% tamaño; `input_data` JSON ya soporta base64 str (`_process_image` lo decodifica); `api.ts` frontend es solo JSON (no hay FormData); tests httpx/ASGITransport más simples; sin dep `python-multipart` | ✅ |
| multipart | streaming eficiente, pero exige reescribir `request<T>` de `api.ts` (content-type condicional + FormData), dep nueva en backend, manejo `UploadFile` y más casos de test; sin beneficio real porque Pillow ya optimiza en servidor (≤1024px, JPEG q85 → típico < 300KB) | ❌ |

Contrato: `POST /api/v1/analysis/jobs` con `{"job_type": "image", "input_data": {"image_bytes": "<base64>"}}`. El frontend lee el archivo con `FileReader.readAsDataURL` y envía solo el payload base64 (sin prefijo `data:...;base64,`). **Límite**: `image_bytes` ≤ 8 MB (base64, ~6 MB decodificado) → 413 si excede (alineado con el cap de 10M de nginx); `input_data.url` ≤ 2048 chars y validado por el SSRF guard (D7).

## D5. Deferidos explícitos (NON-goals de PR3)

| Ítem | Estado | Razón |
|---|---|---|
| Upsert real "a tablas finales" al aprobar (Product/PriceListItem/BusinessPolicy) | **DEFERIDO** — `approve_proposal` sigue siendo stub (flip de status + notificación); requiere decisión de mapeo de campos | Cambio follow-up (nuevo SDD change); aprobar en PR3 = transición de estado + notificación |
| Migración `google-generativeai` → `google-genai` | **DEFERIDO** (follow-up c del verify) | Reescribir `gemini_client` expande el slice sin necesidad; solo FutureWarning EOL |
| `datetime.utcnow()` deprecado (orchestrator L85/115/143, scraper L118) | **DEFERIDO** (follow-up b) | Opcional barato, pero sin cambio de comportamiento; mantener slice mínimo |
| `scraper.py` ≥80% cobertura (W-1) | **DEFERIDO** | Gate global verde (87.48%); PR3 no toca scraper |

## D6. Sub-split PR3a/PR3b (guard 400 líneas)

Backend+frontend ≈ 900+ líneas → excede el budget de review. **PR3a backend → PR3b frontend**, en cadena sobre la rama PR2 (auto-chain ya activo, feature-branch-chain: PR3b targetea la rama de PR3a).

**PR3a (backend)** — work units con tests RED junto al código (TDD estricto):

| WU | Contenido | Tarea SDD | RED tests |
|---|---|---|---|
| W-1 | Migración `005_add_analysis_tables.py` + import en `env.py` | nueva | `alembic upgrade head` en Postgres (no pytest) + suite completa |
| W-2 | `pipeline_state.py` + `count_by_status` + rework `api/pixelrag.py` (R-X03) | nueva | ext. `tests/test_pixelrag.py`, ext. `tests/repositories/test_analysis_repo.py` |
| W-3 | Schemas `ScrapedSource*` + endpoints sources | nueva | ext. `tests/schemas/test_analysis.py`, `tests/test_api_analysis.py` |
| W-4 | `api/analysis.py` (jobs/results/approve/reject + BackgroundTasks) + router en `main.py` | 3.1, 3.3 | `tests/test_api_analysis.py` (nuevo) |
| W-5 | Scheduler `analysis_monitor` + `mark_active()` | 3.2 | ext. `tests/test_scheduler.py` |
| W-6 | Bookkeeping: marcar 1.3 [x], 3.4 [x] (commit a85aa83), corregir rutas Phase 4 (4.1→`tests/services/test_gemini_client.py`, 4.2→`tests/schemas/test_analysis.py`, 4.4→`tests/services/test_pixelrag_analysis.py`, 4.3→`tests/test_api_analysis.py`, 4.5→`tests/test_scheduler.py`) | — | — |

**PR3b (frontend)** — `types` → hook → componentes → página:

| WU | Contenido | Tarea SDD | RED tests |
|---|---|---|---|
| W-7 | `types/index.ts`: `AnalysisJob`, `AnalysisResult`, `ScrapedSource`, payloads (snake_case exacto de los schemas backend) | 3.8 | — (tipos) |
| W-8 | `hooks/useAnalysis.ts` (patrón `useNotifications`: estado + polling 30s + antd message) | 3.6 | `__tests__/useAnalysis.test.ts` (vi.mock `@/services/api`) |
| W-9 | `components/analysis/`: `ProposalCard`, `SourceManager`, `FileList` (antd Upload → base64) | 3.7 | tests de componentes |
| W-10 | `pages/Analysis.tsx` (antd Table + Upload) + ruta `/analysis` en `App.tsx` | 3.5, 3.9 | `__tests__/AnalysisPage.test.tsx` |

**Nota**: `frontend/src/store/` está vacío; la convención de estado es hooks (no zustand/redux) — se mantiene.

## D7. Seguridad del slice — SSRF guard y posture de auth (R1-001)

**Decisión**: los endpoints `/api/v1/analysis/*` aceptan URLs y el servidor las fetchea (PixelRAG/scraper) → sin controles esto es SSRF. La app NO tiene auth en ningún router (decisión existente); este slice NO introduce auth, pero SÍ exige validación estricta de entrada en todo punto que acepte URLs:

- **SSRF guard** (nuevo helper `backend/app/services/analysis/url_guard.py`): `validate_external_url(url: str) -> str` — (1) esquema http/https únicamente; (2) resolución DNS y rechazo de rangos IP privados/loopback/link-local/metadata (169.254.169.254, ::1, 127.0.0.0/8, 10/8, 172.16/12, 192.168/16, 100.64/10); (3) nota explícita: resolver y re-chequear en la conexión para mitigar DNS rebinding. Falla → `HTTPException(400)` en API; en el scheduler → job `failed` con `error_message`.
- **Puntos de aplicación**: `POST /analysis/jobs` (job_type=url) y `POST /analysis/sources` (antes de `get_by_url`/create); el scheduler valida la URL de cada fuente activa antes de crear el job.
- **Límites**: `image_bytes` ≤ 8 MB (413); `url` ≤ 2048 chars; `job_type` enum cerrado; `reason` de reject ≤ 500 chars.
- **RED tests**: `tests/test_api_analysis.py` — URL privada/loopback → 400; esquema no-http (ftp, file) → 400; image_bytes >8MB → 413; `tests/test_scheduler.py` — fuente con URL privada → job failed sin fetch.
- **Auth**: se mantiene `none` por consistencia con la app (sin dependencias de auth existentes); el SSRF guard + límites son la mitigación de este slice. Introducir auth real queda como follow-up explícito (fuera de PR3).

## Contratos de API (PR3)

Prefijo `/api/v1/analysis`. **Auth: ninguna** — consistente con todos los routers existentes (sin dependencias de auth en la app); mitigado por el SSRF guard y límites de D7.

| Método | Path | Request | Response | Auth |
|---|---|---|---|---|
| POST | `/analysis/jobs` | `{"job_type": "image\|url", "input_data": {...}}`; imagen → `input_data.image_bytes` base64 str; URL → `input_data.url` | **202** `AnalysisJobResponse` (status `pending`); 400 si falta clave requerida o `job_type` inválido | none |
| GET | `/analysis/jobs` | query `page`, `per_page`, `status?` | 200 `AnalysisJobList` | none |
| GET | `/analysis/jobs/{id}` | — | 200 job status dict (de `orchestrator.get_job_status`); 404 inexistente | none |
| GET | `/analysis/results` | query `page`, `per_page`, `status?` | 200 `AnalysisResultList` | none |
| POST | `/analysis/results/{id}/approve` | — | 200 `{"id": str, "status": "accepted"}`; 404 inexistente; 409 ya resuelto | none |
| POST | `/analysis/results/{id}/reject` | `{"reason": str}` (opcional) | 200 `{"id": str, "status": "rejected", "reason": str}`; 404; 409 | none |
| POST | `/analysis/sources` | `ScrapedSourceCreate` | 201 `ScrapedSourceResponse`; 409 URL duplicada | none |
| GET | `/analysis/sources` | query `page`, `per_page` | 200 `ScrapedSourceList` | none |
| DELETE | `/analysis/sources/{id}` | — | 204 (soft delete); 404 | none |
| GET | `/api/v1/pixelrag/test` (R-X03) | — | 200 `{service, status, analysis_pipeline?: {active, last_successful_run, pending_jobs}}`; 404 si `environment == "production"`; 500 error servicio | none |

**Wiring de BackgroundTasks (clave)**: `POST /jobs` crea el job con la sesión del request y agenda `_process_job_task(job_id)`. La bg task NO puede reusar la sesión de `Depends(get_db)` (se cierra al terminar el request) → abre **su propia** `AsyncSession` desde un session factory a nivel de módulo (`app.api.analysis.async_session`), inyectable en tests (monkeypatch para usar el engine de test). `build_orchestrator(session)` — factory a nivel de módulo que arma `AnalysisOrchestrator` con servicios reales (GeminiClient etc.) — es el punto de mockeo: tests de wiring patchean `build_orchestrator` con un mock (`process_job` AsyncMock); el test de integración real usa el factory con Gemini/PixelRAG/scraper/notifications mockeados (sin red real). Con ASGITransport las bg tasks completan antes de que retorne `client.post` → determinista. La discriminación 404/409 de approve/reject se hace en la capa API (`result_repo.get_by_id` + chequeo de status) **antes** de delegar en `orchestrator.approve_proposal/reject_proposal` (que retornan bool y no distinguen no-existe vs ya-resuelto); el orchestrator de PR2 no se modifica en firma.

**Scheduler `analysis_monitor`** (patrón `_run_commercial_check_sync`): sweep cada 15 min (`ANALYSIS_MONITOR_INTERVAL_MINUTES = 15`) en `ThreadPoolExecutor` existente; `_run_analysis_monitor_sync` crea event loop propio, consulta `ScrapedSourceRepository.get_all(filters={"is_active": True})` y por cada fuente (respetando `schedule_interval_minutes` o default 15 min — salta si `last_analyzed_at` es reciente) crea `AnalysisJob(job_type="url", input_data={"url": ...})` y lo procesa con `build_orchestrator` (fallos → job `failed` + notificación, sin retry-storm; `last_analyzed_at` se actualiza tras el intento).

## Data Flow PR3

```
Frontend /analysis ──POST /api/v1/analysis/jobs (base64-JSON)──▶ api/analysis.py
      │                                                          │ valida + crea AnalysisJob(pending)
      │                                                          ▼
      │                             BackgroundTasks → _process_job_task(job_id)
      │                                nueva AsyncSession (factory inyectable)
      │                                build_orchestrator → process_job()
      │                                → Gemini/PixelRAG/scraper → AnalysisResult(proposal)
      │                                → pipeline_state.mark_success() → notificación
      │                                                          │
      ├── GET /jobs|/jobs/{id}|/results (polling 30s) ◄───────────┘
      ├── POST /results/{id}/approve|reject → orchestrator (flip status + notif; upsert DEFERIDO)
      └── POST|GET|DELETE /sources → ScrapedSourceRepository (soft delete)

APScheduler analysis_monitor (15 min) → _run_analysis_monitor_sync → fuentes activas → jobs URL → orchestrator
GET /api/v1/pixelrag/test (R-X03) → pipeline_state.snapshot() + count_by_status("pending"); 404 en producción
```

## File Changes PR3

| File | Action | Description |
|---|---|---|
| `backend/migrations/versions/005_add_analysis_tables.py` | Create | Tablas `analysis_jobs`/`analysis_results`/`scraped_sources` + índices |
| `backend/migrations/env.py` | Modify | Import `app.models.analysis` |
| `backend/app/services/analysis/pipeline_state.py` | Create | Singleton `AnalysisPipelineState` (R-X03) |
| `backend/app/services/analysis/url_guard.py` | Create | SSRF guard `validate_external_url` (D7) — aplicado en jobs url, sources y scheduler |
| `backend/app/repositories/analysis.py` | Modify | `count_by_status` en `AnalysisJobRepository` |
| `backend/app/api/pixelrag.py` | Modify | Gating 404 producción + bloque `analysis_pipeline` |
| `backend/app/schemas/analysis.py` | Modify | `ScrapedSourceCreate/Response/List` |
| `backend/app/api/analysis.py` | Create | Router `/api/v1/analysis` + `build_orchestrator` + `_process_job_task` |
| `backend/app/main.py` | Modify | Registrar router de analysis |
| `backend/app/scheduler.py` | Modify | `_run_analysis_monitor_sync` + job `analysis_monitor` + `mark_active()` |
| `backend/app/services/analysis/orchestrator.py` | Modify | `mark_success()` en `process_job` (1 línea) |
| `frontend/src/types/index.ts` | Modify | `AnalysisJob`, `AnalysisResult`, `ScrapedSource`, payloads |
| `frontend/src/hooks/useAnalysis.ts` | Create | Hook (patrón `useNotifications`) |
| `frontend/src/components/analysis/{ProposalCard,SourceManager,FileList}.tsx` | Create | Componentes UI |
| `frontend/src/pages/Analysis.tsx` | Create | Página `/analysis` |
| `frontend/src/App.tsx` | Modify | Ruta `/analysis` |
| `backend/tests/test_api_analysis.py` | Create | RED: jobs/results/approve/reject/sources (wiring + integración mockeada) |
| `backend/tests/test_pixelrag.py`, `test_scheduler.py`, `tests/repositories/test_analysis_repo.py`, `tests/schemas/test_analysis.py` | Modify | RED: R-X03, sweep, `count_by_status`, schemas sources |
| `frontend/src/__tests__/useAnalysis.test.ts`, `AnalysisPage.test.tsx`, tests componentes | Create | RED frontend |

## Testing Strategy PR3

| Layer | What to Test | Approach |
|---|---|---|
| Unit | `count_by_status`, schemas `ScrapedSource*` | RED en `tests/repositories/test_analysis_repo.py` y `tests/schemas/test_analysis.py` |
| Integration | Endpoints `/api/v1/analysis/*` | `tests/test_api_analysis.py`: patrón `override_get_db` + ASGITransport; wiring con `build_orchestrator` mockeado; 1 test de pipeline real con Gemini/PixelRAG/scraper/notifications mockeados (sin red); approve/reject 404/409; sources 201/409/204/404 |
| Integration | R-X03 | `tests/test_pixelrag.py`: 200+bloque, 200 sin bloque, 404 producción, 500 servicio |
| Integration | Scheduler | `tests/test_scheduler.py`: job `analysis_monitor` registrado, sweep sin error, filtra inactivas |
| E2E frontend | Hook + página + componentes | vitest + @testing-library/react; vi.mock `@/services/api`; TS estricto (snake_case exacto) |

## Migration / Rollout PR3

Migración `005` (idempotente vía `alembic upgrade head` en lifespan). Rollback: `alembic downgrade 004` (drop de las 3 tablas); desregistrar router de analysis; remover job `analysis_monitor` del scheduler; sin migración de datos (tablas nuevas).

## Open Questions PR3

- [ ] Ninguna bloqueante. Pendientes de decisión de negocio (mapeo de campos del upsert a tablas finales) → follow-up, fuera de PR3. El quirk `TEST_DATABASE_URL` del conftest y el EOL de `google.generativeai` quedan registrados como follow-ups (a, b, c) del verify-report.
