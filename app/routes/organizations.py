""" Person routes"""
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from app.models.research_structures import ResearchStructure
from app.services.organizations.research_structure_service import ResearchStructureService

router = APIRouter()

tags_metadata = [
    {
        "name": "organizations",
        "description": "Organizations CRUD operations",
    }
]


@router.post(
    "/research-structure",
    name="create-research-structure",
)
async def create_research_structure(
        structure_service: Annotated[ResearchStructureService, Depends(ResearchStructureService)],
        structure: ResearchStructure | None,
) -> JSONResponse:
    """
    Creates a research structure

    :param structure_service:
    :param structure: entity built from fields
    :return: json response
    """

    created_research_structure = await structure_service.create_structure(structure)
    response_data = {"message": "Research structure created successfully",
                     "structure": created_research_structure}
    return JSONResponse(jsonable_encoder(response_data), status_code=status.HTTP_201_CREATED)


@router.put(
    "/research-structure",
    name="update-research-structure",
)
async def update_research_structure(
        structure_service: Annotated[ResearchStructureService, Depends(ResearchStructureService)],
        structure: ResearchStructure | None,
) -> JSONResponse:
    """
    Updates a research structure

    :param structure_service:
    :param structure: entity built from fields
    :return: json response
    """
    updated_structure = await structure_service.update_structure(structure)
    response_data = {"message": f"Research structure with id {structure.id} updated successfully",
                     "structure": updated_structure}
    return JSONResponse(jsonable_encoder(response_data), status_code=status.HTTP_200_OK)
