from fastapi import APIRouter

from .report_controller import router as report_router

router = APIRouter()
router.include_router(report_router)

__all__ = ["router"]