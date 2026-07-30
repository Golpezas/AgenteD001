# Tasks: Análisis de Imágenes y URLs

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~900 new lines across 13 files |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR #1 foundation → PR #2 core → PR #3 integration |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Foundation: models, schemas, repos | PR #1 | pytest tests/models/ | FastAPI test client | Drop Alembic tables |
| 2 | Core: Gemini, scraper, orchestrator, pixelrag ext | PR #2 | pytest tests/services/ | Mock Gemini + PixelRAG | Remove analysis/services/ |
| 3 | Integration: API, scheduler, frontend | PR #3 | pytest tests/api/ | Running app + browser | Remove /analysis route |

## Phase 1: Foundation

- [x] 1.1 Create `backend/app/models/analysis.py` with `AnalysisJob`, `AnalysisResult`, `ScrapedSource` SQLAlchemy models
- [x] 1.2 Create `backend/app/schemas/analysis.py` with Pydantic schemas (`AnalysisProposal`, job/result schemas) and `ScreenshotResult`
- [ ] 1.3 Create `backend/app/repositories/analysis.py` with async SQLAlchemy repos for jobs, results, and scraped sources

## Phase 2: Core

- [ ] 2.1 Create `backend/app/services/analysis/gemini_client.py` — Gemini Vision call with Pillow-optimized image
- [ ] 2.2 Create `backend/app/services/analysis/scraper.py` — HTML scrape via httpx/BS4 + screenshot via PixelRAG
- [ ] 2.3 Create `backend/app/services/analysis/orchestrator.py` — async pipeline: image/URL → extraction → Pydantic validation → proposal
- [ ] 2.4 Modify `backend/app/services/pixelrag.py` — add `capture_for_analysis(url) -> ScreenshotResult` (spec R-X04)

## Phase 3: Integration

- [ ] 3.1 Create `backend/app/api/analysis.py` — POST jobs, GET results, POST accept/reject endpoints
- [ ] 3.2 Modify `backend/app/scheduler.py` — register APScheduler job monitoring active `ScrapedSource` URLs
- [ ] 3.3 Modify `backend/app/main.py` — register analysis router
- [ ] 3.4 Modify `backend/requirements.txt` — add `google-genai`, `Pillow`, `beautifulsoup4`, `lxml`
- [ ] 3.5 Create `frontend/src/pages/Analysis.tsx` — upload image, enter URL, view proposals table
- [ ] 3.6 Create `frontend/src/hooks/useAnalysis.ts` — React hook for job CRUD and proposal acceptance
- [ ] 3.7 Create `frontend/src/components/analysis/` — FileList, ProposalCard, SourceManager components
- [ ] 3.8 Modify `frontend/src/types/index.ts` — add `AnalysisJob`, `AnalysisResult` TypeScript types
- [ ] 3.9 Modify `frontend/src/App.tsx` — add `/analysis` route

## Phase 4: Testing (TDD — RED first)

- [ ] 4.1 RED: Write failing unit test for Gemini extraction with invalid JSON — `tests/unit/test_gemini_client.py`
- [ ] 4.2 RED: Write failing unit test for Pydantic validation of proposals — `tests/unit/test_schemas.py`
- [ ] 4.3 RED: Write failing integration test for `POST /api/v1/analysis/jobs` — `tests/integration/test_analysis_api.py`
- [ ] 4.4 RED: Write failing test for `capture_for_analysis` returning `ScreenshotResult` with PNG ≥1KB — `tests/integration/test_pixelrag_analysis.py`
- [ ] 4.5 Verify scheduler monitoreo runs without blocking API requests — `pytest tests/integration/test_scheduler.py`