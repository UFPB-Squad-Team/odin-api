from fastapi import APIRouter

from .municipios_controller import router as municipios_router


router = APIRouter()
router.include_router(municipios_router)

__all__ = ["router"]
