""" Person routes"""
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from app.models.research_units import ResearchUnit
from app.services.organizations.research_unit_service import ResearchUnitService

router = APIRouter()

tags_metadata = [
    {
        "name": "organizations",
        "description": "Organizations CRUD operations",
    }
]


@router.post(
    "/research-unit",
    name="create-research-unit",
)
async def create_research_unit(
        structure_service: Annotated[ResearchUnitService, Depends(ResearchUnitService)],
        structure: ResearchUnit | None,
) -> JSONResponse:
    """
    Creates a research structure

    :param structure_service:
    :param structure: entity built from fields
    :return: json response
    """

    created_research_unit = await structure_service.create_structure(structure)
    response_data = {"message": "Research structure created successfully",
                     "structure": created_research_unit}
    return JSONResponse(jsonable_encoder(response_data), status_code=status.HTTP_201_CREATED)


@router.put(
    "/research-unit",
    name="update-research-unit",
)
async def update_research_unit(
        structure_service: Annotated[ResearchUnitService, Depends(ResearchUnitService)],
        structure: ResearchUnit | None,
) -> JSONResponse:
    """
    Updates a research structure

    :param structure_service:
    :param structure: entity built from fields
    :return: json response
    """
    updated_structure = await structure_service.update_structure(structure)
    response_data = {"message": f"Research structure with id {structure.uid} updated successfully",
                     "structure": updated_structure}
    return JSONResponse(jsonable_encoder(response_data), status_code=status.HTTP_200_OK)
