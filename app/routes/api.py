"""
API redirection router
"""

from fastapi import APIRouter

from app.routes import references, people

router = APIRouter()
router.include_router(references.router, tags=["references"], prefix="/reference")
router.include_router(people.router, tags=["people"], prefix="/people")
