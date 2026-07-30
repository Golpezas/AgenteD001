# Delta para PixelRAG Integration

## ADDED Requirements

### R-X04: Screenshot para pipeline de análisis

El sistema DEBE exponer un método `capture_for_analysis(url: str) -> ScreenshotResult` en PixelRAGService. `ScreenshotResult` DEBE contener `image_bytes: bytes`, `url: str`, `timestamp: datetime` y `resolution: tuple[int, int]`. El método DEBE reutilizar la misma instancia de pixelshot que `render_url`.

#### Escenario: Captura exitosa con metadatos

- DADO que PixelRAGService está inicializado
- CUANDO se llama a `capture_for_analysis("https://ejemplo.com")`
- ENTONCES DEBE retornar un ScreenshotResult con PNG y metadatos
- Y `image_bytes` DEBE tener tamaño > 1KB

#### Escenario: Error propagado desde render_url

- DADO que PixelRAGService está inicializado
- CUANDO `capture_for_analysis` recibe una URL inválida
- ENTONCES DEBE propagar la excepción de `render_url`
- Y NO DEBE capturar excepciones silenciosamente

## MODIFIED Requirements

### R-X03: Endpoint de health check con estado del pipeline

El sistema PUEDE exponer `GET /api/v1/pixelrag/test` que renderice una URL de prueba, verifique el servicio y retorne estado incluyendo la integración con el pipeline de análisis. Este endpoint DEBE retornar 200 si el servicio responde. La respuesta DEBE incluir `analysis_pipeline.active`, `analysis_pipeline.last_successful_run` y `analysis_pipeline.pending_jobs` cuando el pipeline esté registrado. Este endpoint NO DEBE estar disponible en producción.
(Previously: Endpoint que solo verificaba disponibilidad del servicio sin estado del pipeline)

#### Escenario: Health check incluye estado del pipeline

- DADO que PixelRAGService funciona correctamente
- Y el pipeline de análisis está registrado
- CUANDO se hace GET a `/api/v1/pixelrag/test`
- ENTONCES la respuesta DEBE ser 200 OK
- Y DEBE contener `{"service": "pixelrag", "status": "available", "analysis_pipeline": {"active": true, "last_successful_run": "..."}}`
