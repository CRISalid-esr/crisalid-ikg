""" Database error handler. """

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR


class DatabaseError(Exception):
    """
    Database error
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


async def database_error_handler(
        _: Request,
        exc: DatabaseError,
) -> JSONResponse:
    """

    :param _: request
    :param exc: validation error
    :return: json response with the validation errors
    """
    return JSONResponse(
        {"error": str(exc)},
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )
