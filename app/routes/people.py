""" Person routes"""
from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from app.config import get_app_settings
from app.models.people import Person
from app.services.people.people_service import PeopleService
from app.settings.app_settings import AppSettings

router = APIRouter()

tags_metadata = [
    {
        "name": "person",
        "description": "People CRUD operations",
    }
]


@router.post(
    "/",
    name="references:create-person",
)
async def create_person(
        settings: Annotated[AppSettings, Depends(get_app_settings)],
        people_service: Annotated[PeopleService, Depends(PeopleService)],
        person: Person | None,
) -> JSONResponse:
    """
    Creates a person

    \f
    :param settings: app settings
    :param people_service:
    :param person: entity built from fields
    :return: json response
    """

    created_person = people_service.create_person(person)
    response_data = {"message": "Person created successfully", "person": created_person}
    return JSONResponse(content=response_data, status_code=status.HTTP_201_CREATED)
