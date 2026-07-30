# Propuesta: Análisis de Imágenes y URLs

## Intención

Extraer automáticamente información de productos, servicios, precios y políticas comerciales desde imágenes subidas y URLs de competidores/proveedores. Sin esto, el equipo captura datos manualmente, retrasando el motor de precios y perdiendo monitoreo competitivo.

## Scope

### In Scope
- Subida manual de imágenes → extracción Gemini Vision → propuesta de cambios
- Análisis de URLs: scraping HTML + screenshot PixelRAG + Gemini Vision → JSON
- Monitoreo automático programado de URLs vía APScheduler
- Pipeline asíncrono con cola de procesamiento (no bloquea requests)
- Output como propuesta → usuario acepta/rechaza (NO auto-persistir)
- Modelos: AnalysisJob, AnalysisResult, ScrapedSource

### Out of Scope
- OCR puro sin IA, integración n8n (Fase 2+), auto-persistencia, dashboard de tendencias

## Capacidades

### Nuevas
- `analysis-engine`: Pipeline multimodal (imágenes + URLs) con Gemini, cola asíncrona, propuestas de upsert revisadas por usuario

### Modificadas
- `pixelrag-integracion`: PixelRAGService se extiende como fuente del pipeline (screenshot → Gemini Vision)

## Approach

Pipeline híbrido: (1) Imagen → Pillow optimiza → Gemini Vision → JSON validado con Pydantic. (2) URL → httpx/BeautifulSoup scrapea HTML + PixelRAG captura screenshot → Gemini Vision analiza ambos. Resultados alimentan propuesta de upsert revisable desde frontend. APScheduler ejecuta jobs periódicos sobre ScrapedSource activas.

## Áreas Afectadas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `backend/app/api/analysis.py` | Nuevo | Endpoints subir imagen, enviar URL, listar resultados |
| `backend/app/services/analysis/` | Nuevo | Servicios Gemini, scraper, extractor |
| `backend/app/services/pixelrag.py` | Modificado | Integrar con pipeline de análisis |
| `backend/app/models/analysis.py` | Nuevo | AnalysisJob, AnalysisResult, ScrapedSource |
| `backend/app/schemas/analysis.py` | Nuevo | Schemas Pydantic |
| `backend/app/repositories/analysis.py` | Nuevo | Repos async SQLAlchemy |
| `backend/requirements.txt` | Modificado | +Pillow, +beautifulsoup4, +lxml, +google-genai |
| `backend/app/scheduler.py` | Modificado | Job monitoreo URLs activas |
| `frontend/src/pages/Analysis.tsx` | Nuevo | Página subir imagen/URL, ver propuestas |
| `frontend/src/hooks/useAnalysis.ts` | Nuevo | Hook React |
| `frontend/src/components/analysis/` | Nuevo | Componentes contenedor/presentacionales |
| `frontend/src/App.tsx` | Modificado | Ruta /analysis |
| `frontend/src/types/index.ts` | Modificado | Tipos AnalysisJob, AnalysisResult |

## Riesgos

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| Costo Gemini (imágenes) | Media | Capa gratuita 60 req/min, cachear resultados |
| Alucinaciones en extracción | Alta | Validación Pydantic + revisión humana obligatoria |
| Privacidad datos cliente en API externa | Alta | No enviar datos sensibles, informar en UI, opt-out |
| Mantenimiento scraping (HTML cambiante) | Alta | Selectors resilientes + fallback a solo screenshot |
| PixelRAG no probado en producción | Media | Monitoreo + timeout configurable |

## Plan de Rollback

1. Deshabilitar scheduler: remover job de monitoreo
2. Eliminar rutas de analysis.py del router principal
3. Revertir requirements.txt (quitar Pillow, bs4, google-genai)
4. Revertir cambios en pixelrag.py
5. Drop tablas vía Alembic downgrade

## Criterios de Éxito

- [ ] Imagen subida → extracción ≥80% de campos esperados en dataset conocido
- [ ] URL analizada → extracción combinada (scraping + screenshot) supera a solo scraping
- [ ] Propuesta generada sin auto-persistir datos
- [ ] Scheduler ejecuta monitoreo sin bloquear requests del API
- [ ] Frontend permite revisar, aceptar/rechazar propuestas
