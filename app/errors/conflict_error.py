""" Validation error handler. """

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_409_CONFLICT


class ConflictError(ValueError):
    """
    Conflict error
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


async def conflicting_entity_error_handler(
        _: Request,
        exc: ConflictError,
) -> JSONResponse:
    """

    :param _: request
    :param exc: validation error
    :return: json response with the validation errors
    """
    return JSONResponse(
        {"error": str(exc)},
        status_code=HTTP_409_CONFLICT,
    )
