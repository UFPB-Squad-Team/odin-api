from fastapi import APIRouter

from .get_state_summary_controller import router as get_state_summary_router

router = APIRouter()
router.include_router(get_state_summary_router)