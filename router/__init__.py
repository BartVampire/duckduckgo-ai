from .keys import router as keys_router
from .chat import router as chat_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(keys_router)
router.include_router(chat_router)