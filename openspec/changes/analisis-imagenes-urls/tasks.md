# Tasks: Análisis de Imágenes y URLs

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | PR1+PR2 merged (~2100). PR3 ≈ 850-1000: PR3a-first ~30-50, PR3a-core ~450-550, PR3b ~350-450 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR3a-first (bookkeeping) → PR3a-core (backend W-1..W-5) → PR3b (frontend W-7..W-10) |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| W-6 | Bookkeeping tasks.md (1.3/3.4/4.1/4.2/4.4 [x], rutas Phase 4) | PR3a-first (base: `feature/analisis-imagenes-urls-pr2`) | `git diff` review | N/A — solo edición de tasks.md, sin runtime | Revert commit; tasks.md no afecta runtime |
| W-1..W-5 | Backend: migración 005, R-X03, API `/analysis`, scheduler | PR3a-core (base: rama PR3a-first) | `cd backend && pytest -q tests/test_api_analysis.py tests/test_scheduler.py tests/test_pixelrag.py tests/repositories/test_analysis_repo.py` | `alembic upgrade head` en Postgres (docker) + suite completa | `alembic downgrade 004` + desregistrar router analysis y job `analysis_monitor` |
| W-7..W-10 | Frontend: types, hook, componentes, página `/analysis` | PR3b (base: rama PR3a-core) | `cd frontend && npx vitest run` | `npm run dev` + navegador `/analysis` | Revert commit frontend; ruta `/analysis` no afecta backend |

## Phase 1: Foundation

- [x] 1.1 Create `backend/app/models/analysis.py` with `AnalysisJob`, `AnalysisResult`, `ScrapedSource` SQLAlchemy models
- [x] 1.2 Create `backend/app/schemas/analysis.py` with Pydantic schemas (`AnalysisProposal`, job/result schemas) and `ScreenshotResult`
- [x] 1.3 Create `backend/app/repositories/analysis.py` with async SQLAlchemy repos for jobs, results, and scraped sources (implementado PR1 — verify W-2; checkbox marcado por W-6)
- [ ] 1.4 **W-1** Migración `005_add_analysis_tables.py` + import de modelos en `migrations/env.py`
- [ ] 1.5 **W-2** `pipeline_state.py` singleton + `AnalysisJobRepository.count_by_status` (base R-X03)

## Phase 2: Core

- [x] 2.1 Create `backend/app/services/analysis/gemini_client.py` — Gemini Vision call with Pillow-optimized image
- [x] 2.2 Create `backend/app/services/analysis/scraper.py` — HTML scrape via httpx/BS4 + screenshot via PixelRAG
- [x] 2.3 Create `backend/app/services/analysis/orchestrator.py` — async pipeline: image/URL → extraction → Pydantic validation → proposal
- [x] 2.4 Modify `backend/app/services/pixelrag.py` — add `capture_for_analysis(url) -> ScreenshotResult` (spec R-X04)

## Phase 3: Integration

- [ ] 3.1 **W-4** Create `backend/app/api/analysis.py` — POST jobs, GET results, POST accept/reject endpoints
- [ ] 3.2 **W-5** Modify `backend/app/scheduler.py` — register APScheduler job monitoring active `ScrapedSource` URLs
- [ ] 3.3 **W-4** Modify `backend/app/main.py` — register analysis router
- [x] 3.4 Modify `backend/requirements.txt` — add `google-generativeai`, `Pillow`, `beautifulsoup4`, `lxml` (hecho en PR2, commit a85aa83 — verify S-3; checkbox marcado por W-6)
- [ ] 3.5 **W-10** Create `frontend/src/pages/Analysis.tsx` — upload image, enter URL, view proposals table
- [ ] 3.6 **W-8** Create `frontend/src/hooks/useAnalysis.ts` — React hook for job CRUD and proposal acceptance
- [ ] 3.7 **W-9** Create `frontend/src/components/analysis/` — FileList, ProposalCard, SourceManager components
- [ ] 3.8 **W-7** Modify `frontend/src/types/index.ts` — add `AnalysisJob`, `AnalysisResult`, `ScrapedSource` TypeScript types
- [ ] 3.9 **W-10** Modify `frontend/src/App.tsx` — add `/analysis` route

## Phase 4: Testing (TDD — RED first)

- [x] 4.1 RED: Write failing unit test for Gemini extraction with invalid JSON — `tests/services/test_gemini_client.py` (ruta corregida por W-6; verify S-1)
- [x] 4.2 RED: Write failing unit test for Pydantic validation of proposals — `tests/schemas/test_analysis.py` (ruta corregida por W-6; verify S-1)
- [ ] 4.3 **W-4** RED: Write failing integration test for `POST /api/v1/analysis/jobs` — `tests/test_api_analysis.py`
- [x] 4.4 RED: Write failing test for `capture_for_analysis` returning `ScreenshotResult` with PNG ≥1KB — `tests/services/test_pixelrag_analysis.py` (ruta corregida por W-6)
- [ ] 4.5 **W-5** Verify scheduler monitoreo runs without blocking API requests — `tests/test_scheduler.py`

## PR3 — Work Units (TDD estricto: RED primero)

| ID | Slice | Fase | Descripción | Archivos | Test-first (RED) | Verificación | Depende de |
|----|-------|------|-------------|----------|------------------|--------------|------------|
| W-6 | PR3a-first | Bookkeeping | Marcar 1.3, 3.4, 4.1, 4.2, 4.4 `[x]`; corregir rutas Phase 4 (S-1); sin cambios de código | `openspec/changes/analisis-imagenes-urls/tasks.md` | N/A (reconciliación de estado; no hay código) | `git diff` revisable | — |
| W-1 | PR3a-core | Fase 1 | Migración `005_add_analysis_tables.py` (tablas `analysis_jobs`/`analysis_results`/`scraped_sources` con UNIQUE url + 4 índices, estilo 004) + `from app.models.analysis import ...` en `env.py` | `backend/migrations/versions/005_add_analysis_tables.py` (create), `backend/migrations/env.py` (modify) | N/A (sin test unitario: conftest usa `create_all`; validar migración) | `cd backend && alembic upgrade head` (Postgres docker) + `pytest -q --cov=app --cov-fail-under=80` | W-6 |
| W-2 | PR3a-core | Fase 1 | Cierre R-X03: `AnalysisPipelineState` (active/last_successful_run/mark_active/mark_success/snapshot) + `count_by_status` + rework `api/pixelrag.py` (404 si `environment=="production"`, bloque `analysis_pipeline` con `pending_jobs` vía `Depends(get_db)`) + `mark_success()` en `orchestrator.process_job` | `backend/app/services/analysis/pipeline_state.py` (create), `backend/app/repositories/analysis.py` (modify), `backend/app/api/pixelrag.py` (modify), `backend/app/services/analysis/orchestrator.py` (modify) | RED ext. `tests/repositories/test_analysis_repo.py` (`test_count_by_status`; NO crear duplicado — archivo existe con 17 tests, S-2) + ext. `tests/test_pixelrag.py` (200+bloque, sin bloque, 404 prod, 500) | `cd backend && pytest -q tests/repositories/test_analysis_repo.py tests/test_pixelrag.py` | W-1 |
| W-3 | PR3a-core | Fase 3 | Schemas `ScrapedSourceCreate/Response/List` (url `str` min 1 max 2048, sin `HttpUrl`) + endpoints `POST/GET/DELETE /api/v1/analysis/sources` (201/200 paginado/204 soft delete; 409 URL duplicada; 404 inexistente; URL validada por SSRF guard D7 → 400 privada/loopback/esquema no-http) | `backend/app/services/analysis/url_guard.py` (create), `backend/app/schemas/analysis.py` (modify), `backend/app/api/analysis.py` (create: router + sources) | RED ext. `tests/schemas/test_analysis.py` + `tests/test_api_analysis.py` (201/409/200/204/404/400) | `cd backend && pytest -q tests/schemas/test_analysis.py tests/test_api_analysis.py` | W-2 |
| W-4 | PR3a-core | Fase 3 | Endpoints jobs/results: `POST /jobs` (202, base64-JSON `image_bytes` ≤8MB → 413; `job_type=url` validado por SSRF guard → 400; 400 inválido) + `GET /jobs` + `GET /jobs/{id}` (404) + `GET /results` + `POST /results/{id}/approve|reject` (404/409 en capa API, sin tocar firma del orchestrator; `reason` ≤500 chars) + BackgroundTasks `_process_job_task` (session factory de módulo inyectable + `build_orchestrator` mockeable) + registrar router en `main.py` | `backend/app/api/analysis.py` (modify/extend), `backend/app/main.py` (modify) | RED ext. `tests/test_api_analysis.py` (patrón `override_get_db` + ASGITransport; wiring con `build_orchestrator` mockeado + 1 test pipeline real con Gemini/PixelRAG/scraper/notifications mockeados, sin red; URL privada → 400; >8MB → 413) | `cd backend && pytest -q tests/test_api_analysis.py` | W-3 |
| W-5 | PR3a-core | Fase 3 | Scheduler `analysis_monitor`: `_run_analysis_monitor_sync` (event loop propio en ThreadPoolExecutor; sweep 15 min `ANALYSIS_MONITOR_INTERVAL_MINUTES`; fuentes `is_active`; valida URL con SSRF guard D7 (fallo → job `failed` sin fetch); salta si `last_analyzed_at` reciente; fallos → job `failed` + notificación) + `mark_active()` al registrar el job | `backend/app/scheduler.py` (modify), `backend/app/services/analysis/pipeline_state.py` (modify) | RED ext. `tests/test_scheduler.py` (job registrado, sweep sin error, filtra inactivas, URL privada → job failed sin fetch) | `cd backend && pytest -q tests/test_scheduler.py` | W-4 |
| W-7 | PR3b | Fase 3 | `types/index.ts`: `AnalysisJob`, `AnalysisResult`, `ScrapedSource` + payloads (snake_case exacto de los schemas backend) | `frontend/src/types/index.ts` (modify) | N/A (tipos; validar con tsc) | `cd frontend && npx tsc --noEmit` | PR3a-core (rama base) |
| W-8 | PR3b | Fase 3 | `hooks/useAnalysis.ts` — patrón `useNotifications`: estado + polling 30s + antd message; submit job imagen/URL, listar, approve/reject, CRUD fuentes | `frontend/src/hooks/useAnalysis.ts` (create) | RED `frontend/src/__tests__/useAnalysis.test.ts` (vi.mock `@/services/api`) | `cd frontend && npx vitest run src/__tests__/useAnalysis.test.ts` | W-7 |
| W-9 | PR3b | Fase 3 | Componentes `components/analysis/`: `ProposalCard`, `SourceManager`, `FileList` (antd Upload → `FileReader.readAsDataURL`, payload base64 sin prefijo) | `frontend/src/components/analysis/{ProposalCard,SourceManager,FileList}.tsx` (create) | RED tests de componentes en `frontend/src/__tests__/` (render + interacciones) | `cd frontend && npx vitest run` | W-8 |
| W-10 | PR3b | Fase 3 | `pages/Analysis.tsx` (antd Table + Upload + gestor de fuentes) + ruta `/analysis` en `App.tsx` | `frontend/src/pages/Analysis.tsx` (create), `frontend/src/App.tsx` (modify) | RED `frontend/src/__tests__/AnalysisPage.test.tsx` (render, flujo submit, tabla) | `cd frontend && npx vitest run && npx tsc --noEmit` | W-9 |

**Orden dentro de PR3a-core**: W-1 (migración) → W-2 (R-X03) → W-3 (sources) → W-4 (jobs API + wiring) → W-5 (scheduler). Sin tarea depende de servicios externos reales: Gemini/PixelRAG/scraper siempre mockeados en tests; BackgroundTasks usa session factory inyectable.

## Fuera de alcance PR3 (NON-goals)

| Ítem | Estado | Razón |
|------|--------|-------|
| Upsert real "a tablas finales" al aprobar (Product/PriceListItem/BusinessPolicy) | DEFERIDO | `approve_proposal` sigue siendo stub (flip de status + notificación); requiere decisión de mapeo de campos → nuevo SDD change follow-up |
| Migración `google-generativeai` → `google-genai` | DEFERIDO | verify follow-up (c); solo FutureWarning EOL; reescribir `gemini_client` expande el slice |
| `datetime.utcnow()` deprecado | DEFERIDO | verify follow-up (b); orchestrator L85/115/143, scraper L118; sin cambio de comportamiento |
| `scraper.py` ≥80% de cobertura | DEFERIDO | verify W-1; gate global 87.48% verde; PR3 no toca scraper |

## Review Workload Forecast

| Slice | Work units | Estimated changed lines | 400-line budget risk |
|-------|-----------|-------------------------|----------------------|
| PR3a-first | W-6 | ~30-50 (solo tasks.md) | Low |
| PR3a-core | W-1..W-5 | ~450-550 | High |
| PR3b | W-7..W-10 | ~350-450 | Medium |
| **Total PR3** | W-1..W-10 | ~850-1000 | High |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

- Cadena: `feature/analisis-imagenes-urls-pr2` ← PR3a-first (W-6) ← PR3a-core (W-1..W-5) ← PR3b (W-7..W-10); cada PR targetea la rama anterior; solo la integración final mergea a main.
- W-6 lands primero para aliviar el diff de PR3a-core (tasks.md deja de aparecer en el diff de código).
- PR3a-core excede el budget (450-550 > 400): si el usuario no lo acepta, split adicional opcional en PR3a-core-1 (W-1..W-3) → PR3a-core-2 (W-4..W-5).
