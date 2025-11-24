from fastapi import APIRouter
from .list_all_schools_controller import router as list_all_router
from .get_school_by_id_controller import router as get_by_id_router

router = APIRouter()
router.include_router(list_all_router)
router.include_router(get_by_id_router)

__all__ = ["router"]
