"""
API redirection router
"""

from fastapi import APIRouter

from app.routes import people

router = APIRouter()
router.include_router(people.router, tags=["people"], prefix="/person")
