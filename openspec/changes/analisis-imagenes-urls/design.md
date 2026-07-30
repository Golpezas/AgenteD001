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
