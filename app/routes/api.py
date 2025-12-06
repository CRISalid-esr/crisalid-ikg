"""
API redirection router
"""

from fastapi import APIRouter

from app.routes import people, organizations, source_records, healthness

router = APIRouter()
router.include_router(people.router, tags=["people"], prefix="/person")
router.include_router(organizations.router, tags=["organizations"], prefix="/organization")
router.include_router(source_records.router, tags=["source_records"], prefix="/source_records")
router.include_router(healthness.router, tags=["healthness"], prefix="/healthness")
