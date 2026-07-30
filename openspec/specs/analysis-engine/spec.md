# Análisis de Imágenes — Especificación

## Propósito

Pipeline multimodal que analiza imágenes subidas y URLs de competidores usando Gemini Vision API. Genera propuestas de upsert que requieren revisión humana antes de persistir.

## Capacidades

- `analysis-engine`: Pipeline multimodal (imágenes + URLs), cola asíncrona, propuestas revisadas por usuario

## Requisitos

### R-AE01: Pipeline multimodal

El sistema DEBE aceptar dos modos de análisis: (1) subida manual de imágenes optimizadas con Pillow, y (2) URLs de competidores/proveedores con scraping HTML + screenshot PixelRAG. Ambos DEBEN usar Gemini Vision API para extraer datos estructurados validados con Pydantic.

#### Escenario: Imagen válida produce extracción exitosa

- DADO que un usuario sube una imagen de producto válida
- CUANDO el pipeline la optimiza con Pillow y la envía a Gemini Vision
- ENTONCES DEBE retornar JSON estructurado (precio, producto, descripción)
- Y AnalysisJob DEBE quedar en estado "completed"

#### Escenario: URL analizada con scraping + screenshot

- DADO que un usuario envía una URL de competidor
- CUANDO el pipeline procesa la URL
- ENTONCES DEBE scrapear HTML con httpx/BeautifulSoup + capturar screenshot vía PixelRAGService
- Y DEBE enviar ambos a Gemini Vision para extracción combinada

#### Escenario: Archivo inválido rechazado

- DADO que un usuario sube un archivo que no es imagen válida
- CUANDO el pipeline intenta procesarlo
- ENTONCES DEBE retornar error 400
- Y AnalysisJob DEBE quedar en estado "failed"

### R-AE02: Cola asíncrona

El sistema DEBE procesar análisis en segundo plano. Los endpoints DEBEN retornar inmediatamente con un AnalysisJob en estado "pending".

#### Escenario: Job encolado correctamente

- DADO que un usuario envía una imagen o URL
- CUANDO el endpoint recibe la solicitud
- ENTONCES DEBE retornar 202 Accepted
- Y DEBE incluir el job_id en la respuesta

#### Escenario: Consulta de estado del job

- DADO que existe un AnalysisJob creado previamente
- CUANDO se consulta GET /analysis/jobs/{job_id}
- ENTONCES DEBE retornar el estado actual del job

### R-AE03: Modelos de datos

El sistema DEBE implementar AnalysisJob (tracking + estado), AnalysisResult (datos extraídos + confianza), y ScrapedSource (URL monitoreada). Todos DEBEN persistirse con SQLAlchemy 2.0 vía repositorio async.

#### Escenario: ScrapedSource creada para monitoreo

- DADO que un usuario registra una URL para monitoreo automático
- CUANDO se persiste en base de datos
- ENTONCES DEBE incluir url, intervalo, estado, y last_analyzed_at

### R-AE04: Propuesta con revisión humana

El pipeline DEBE generar output como propuesta y NUNCA auto-persistir datos en tablas de pricing/productos. El usuario DEBE aceptar o rechazar cada propuesta desde el frontend.

#### Escenario: Propuesta aceptada por el usuario

- DADO que existe una propuesta pendiente con datos extraídos
- CUANDO el usuario hace clic en "Aceptar"
- ENTONCES el sistema DEBE aplicar los datos al modelo correspondiente

#### Escenario: Propuesta rechazada por el usuario

- DADO que existe una propuesta pendiente con datos extraídos
- CUANDO el usuario hace clic en "Rechazar"
- ENTONCES el sistema DEBE descartar los datos sin persistir

### R-AE05: Monitoreo programado

El sistema DEBE ejecutar análisis periódico de ScrapedSource activas vía APScheduler. Cada URL DEBE respetar su intervalo configurado.

#### Escenario: Scheduler ejecuta análisis programado

- DADO que existen ScrapedSource activas con intervalo definido
- CUANDO el scheduler dispara el job de monitoreo
- ENTONCES DEBE encolar un AnalysisJob por cada URL cuyo last_analyzed_at exceda el intervalo

### R-AE06: Frontend de revisión

El frontend DEBE exponer la página /analysis para subir imágenes, enviar URLs, listar resultados históricos y revisar propuestas.

#### Escenario: Usuario sube imagen desde el frontend

- DADO que el usuario está en la página /analysis
- CUANDO selecciona una imagen y hace clic en "Analizar"
- ENTONCES DEBE mostrar el job encolado
- Y DEBE actualizar el resultado cuando el pipeline complete
