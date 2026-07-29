"""
Endpoint PixelRAG — prueba de integración con renderizado.

Expone un endpoint de prueba para verificar que
PixelRAGService está disponible.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/v1/pixelrag", tags=["pixelrag"])


@router.get("/test")
async def pixelrag_test():
    """
    Endpoint de prueba para verificar disponibilidad de PixelRAG.

    Retorna el estado del servicio de renderizado.
    """
    try:
        from app.services.pixelrag import PixelRAGService

        service = PixelRAGService()
        status_info = await service.health()
        return {
            "service": "pixelrag",
            **status_info,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PixelRAG error: {str(e)}",
        )
