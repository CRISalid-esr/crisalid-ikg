""" Person routes"""
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService

router = APIRouter()

tags_metadata = [
    {
        "name": "source-records",
        "description": "Source Records CRUD operations",
    }
]


@router.post(
    "/",
    name="create-source-record",
)
async def create_source_record(
        source_record_service: Annotated[SourceRecordService, Depends(SourceRecordService)],
        source_record: SourceRecord,
        person: Person,
) -> JSONResponse:
    """
    Creates a source record and attaches it to the person for whom it was harvested

    :param source_record_service: service to handle CRUD operations on source records
    :param source_record: entity built from fields
    :param person: entity built from fields
    :return: json response
    """

    created_source_record = await source_record_service.create_source_record(
        source_record=source_record,
        harvested_for=person)
    response_data = {"message": "Source record created successfully", "source_record":
        created_source_record}
    return JSONResponse(jsonable_encoder(response_data), status_code=status.HTTP_201_CREATED)
