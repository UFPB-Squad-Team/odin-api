from fastapi import APIRouter
from .list_states_controller import router as list_states_router
from .get_state_summary_controller import router as get_state_summary_router

router = APIRouter()
router.include_router(list_states_router)
router.include_router(get_state_summary_router)