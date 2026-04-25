from fastapi import APIRouter

from .aggregations_controller import router as aggregations_router


router = APIRouter()
router.include_router(aggregations_router)

__all__ = ["router"]
