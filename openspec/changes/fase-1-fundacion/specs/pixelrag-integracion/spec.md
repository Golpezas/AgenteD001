# PixelRAG — Especificación

## Propósito

Definir la instalación de PixelRAG como dependencia del backend y el wrapper service para renderizado con pixelshot.

## Capacidades

- `pixelrag-base`: Instalación de PixelRAG + wrapper service para renderizado

## Requisitos

### R-X01: PixelRAG como dependencia

El sistema DEBE incluir `pixelrag` en `backend/requirements.txt`. El backend DEBE instalar PixelRAG y sus dependencias durante `docker compose build`. Chrome/Chromium DEBE estar disponible en la imagen del backend para que pixelshot pueda capturar pantallas.

#### Escenario: PixelRAG instalado en build

- DADO que el Dockerfile del backend incluye PixelRAG en requirements.txt
- CUANDO se ejecuta `docker compose build backend`
- ENTONCES el comando DEBE finalizar sin errores
- Y `pip show pixelrag` DEBE mostrar la versión instalada

#### Escenario: Chromium disponible para pixelshot

- DADO que la imagen del backend está construida
- CUANDO se ejecuta `which chromium-browser || which chromium || which google-chrome`
- ENTONCES al menos uno DEBE existir en el PATH

### R-X02: Wrapper Service de Renderizado

El sistema DEBE implementar un servicio `PixelRAGService` en `backend/app/services/pixelrag.py` que exponga métodos para inicializar el motor y renderizar URLs. El servicio DEBE usar `pixelshot` para capturar pantallas. La inicialización DEBE ser lazy (primer uso, no al arrancar la app).

#### Escenario: Servicio wrapper disponible

- DADO que el backend ha iniciado
- CUANDO se importa `PixelRAGService` desde `app.services.pixelrag`
- ENTONCES el import DEBE ser exitoso
- Y la instancia DEBE tener al menos un método `render_url(url: str) -> bytes`

#### Escenario: Renderizado con URL válida

- DADO que PixelRAGService está inicializado
- CUANDO se llama a `render_url("https://example.com")`
- ENTONCES DEBE retornar un `bytes` que representa una imagen PNG
- Y la imagen NO DEBE estar vacía (tamaño > 1KB)

#### Escenario: Error en renderizado con URL inválida

- DADO que PixelRAGService está inicializado
- CUANDO se llama a `render_url("")`
- ENTONCES DEBE lanzar una excepción `ValueError` con mensaje "URL cannot be empty"

### R-X03: Endpoint de prueba de renderizado (opcional)

El systema PUEDE exponer `GET /api/v1/pixelrag/test` que renderice el dashboard del frontend y retorne estado del servicio. Este endpoint DEBE retornar 200 si el servicio responde. Este endpoint NO DEBE estar disponible en producción.

#### Escenario: Prueba de integración exitosa

- DADO que PixelRAGService funciona correctamente
- CUANDO se hace GET a `/api/v1/pixelrag/test`
- ENTONCES la respuesta DEBE ser 200 OK
- Y DEBE contener `{"service": "pixelrag", "status": "available"}`
