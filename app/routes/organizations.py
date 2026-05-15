""" Organization routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette import status
from starlette.responses import JSONResponse

from app.models.organization_unit import OrganizationBase, unitAdapter, nonUnitAdapter
from app.services.organizations.organization_unit_service import OrganizationUnitService

router = APIRouter()

tags_metadata = [
    {
        "name": "organizations",
        "description": "Organizations CRUD operations",
    }
]


def _parse_organization_body(data: dict) -> OrganizationBase:
    """Dispatch raw dict to the correct TypeAdapter based on generic_type."""
    try:
        if data.get("generic_type") == "unit":
            return unitAdapter.validate_python(data)
        return nonUnitAdapter.validate_python(data)
    except ValidationError as exc:
        raise RequestValidationError(errors=exc.errors()) from exc


@router.post(
    "/research-unit",
    name="create-research-unit",
)
async def create_research_unit(
        structure_service: Annotated[OrganizationUnitService, Depends(OrganizationUnitService)],
        request: Request,
) -> JSONResponse:
    """
    Creates a research structure.
    """
    structure = _parse_organization_body(await request.json())
    created = await structure_service.create_structure(structure)
    return JSONResponse(
        jsonable_encoder({"message": "Research structure created successfully", "structure": created}),
        status_code=status.HTTP_201_CREATED,
    )


@router.put(
    "/research-unit",
    name="update-research-unit",
)
async def update_research_unit(
        structure_service: Annotated[OrganizationUnitService, Depends(OrganizationUnitService)],
        request: Request,
) -> JSONResponse:
    """
    Updates a research structure.
    """
    structure = _parse_organization_body(await request.json())
    updated = await structure_service.update_structure(structure)
    return JSONResponse(
        jsonable_encoder({
            "message": f"Research structure updated successfully",
            "structure": updated,
        }),
        status_code=status.HTTP_200_OK,
    )
