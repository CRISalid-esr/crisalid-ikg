""" Person routes"""
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from app.models.people import Person
from app.services.people.people_service import PeopleService

router = APIRouter()

tags_metadata = [
    {
        "name": "person",
        "description": "People CRUD operations",
    }
]


@router.post(
    "/",
    name="create-person",
)
async def create_person(
        people_service: Annotated[PeopleService, Depends(PeopleService)],
        person: Person | None,
) -> JSONResponse:
    """
    Creates a person

    :param people_service:
    :param person: entity built from fields
    :return: json response
    """

    created_person = await people_service.create_person(person)
    response_data = {"message": "Person created successfully", "person": created_person}
    return JSONResponse(jsonable_encoder(response_data), status_code=status.HTTP_201_CREATED)


@router.put(
    "/",
    name="update-person",
)
async def update_person(
        people_service: Annotated[PeopleService, Depends(PeopleService)],
        person: Person | None,
) -> JSONResponse:
    """
    Updates a person

    :param people_service:
    :param person: entity built from fields
    :return: json response
    """
    updated_person = await people_service.update_person(person)
    response_data = {"message": f"Person with id {person.id} updated successfully",
                     "person": updated_person}
    return JSONResponse(jsonable_encoder(response_data), status_code=status.HTTP_200_OK)
