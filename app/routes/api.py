"""
API redirection router
"""

from fastapi import APIRouter

from app.routes import references

router = APIRouter()
router.include_router(references.router, tags=["references"], prefix="/references")
