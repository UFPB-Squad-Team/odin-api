from fastapi import APIRouter

from .universal_search_controller import router as universal_search_router


router = APIRouter()
router.include_router(universal_search_router)

__all__ = ["router"]