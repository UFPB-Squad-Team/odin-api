from fastapi import APIRouter
from .list_all_schools_controller import router as list_all_router

router = APIRouter()
router.include_router(list_all_router)

__all__ = ["router"]
