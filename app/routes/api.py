"""
API redirection router
"""

from fastapi import APIRouter

from app.routes import people, organizations

router = APIRouter()
router.include_router(people.router, tags=["people"], prefix="/person")
router.include_router(organizations.router, tags=["organizations"], prefix="/organization")
