from fastapi import APIRouter
from ..api import endpoints

router = APIRouter()
router.include_router(endpoints.router)