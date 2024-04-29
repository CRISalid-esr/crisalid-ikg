""" References routes"""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.config import get_app_settings
from app.settings.app_settings import AppSettings

router = APIRouter()

tags_metadata = [
    {
        "name": "references",
        "description": "Send informations about bibliographic references",
    }
]


@router.post(
    "/",
    name="references:create",
)
async def create_reference(
        settings: Annotated[AppSettings, Depends(get_app_settings)],
) -> JSONResponse:
    """
    Create a new bibliographic reference

    \f
    :param settings: app settings
    :return: json response
    """
    return JSONResponse(
        {
            "reference_id": 1234
        }
    )
