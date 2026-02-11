""" Not found error handler. """

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT


class ReferenceOwnerNotFoundError(ValueError):
    """
    Raised when the person on behalf of whom a source record was harvested is not found
    """

async def not_found_reference_owner_error_handler(
        _: Request,
        exc: ReferenceOwnerNotFoundError,
) -> JSONResponse:
    """

    :param _: request
    :param exc: validation error
    :return: json response with the validation errors
    """
    return JSONResponse(
        {"error": str(exc)},
        status_code=HTTP_422_UNPROCESSABLE_CONTENT,
    )
