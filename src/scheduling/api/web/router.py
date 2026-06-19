import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)


web_router = APIRouter()


@web_router.get("/employee")
async def get_employees():
    pass
