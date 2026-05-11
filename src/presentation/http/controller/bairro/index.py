from fastapi import APIRouter

from .bairro_controller import router as bairros_router

router = APIRouter()
router.include_router(bairros_router)

__all__ = ["router"]