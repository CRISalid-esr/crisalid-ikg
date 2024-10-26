""" Database error handler. """
from functools import wraps

from neo4j.exceptions import (
    ClientError, DatabaseError as Neo4jDatabaseError,
    TransientError,
    DriverError,
    ServiceUnavailable
)
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


def handle_database_errors(func):
    """
    Decorator to handle various Neo4j exceptions by converting them to a custom DatabaseError.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Neo4jDatabaseError as e:
            raise DatabaseError("A database error occurred.") from e
        except ServiceUnavailable as e:
            raise DatabaseError("The Neo4j service is unavailable or misconfigured.") from e
        except TransientError as e:
            raise DatabaseError("A transient error occurred.") from e
        except ClientError as e:
            raise DatabaseError(
                "A client error occurred, possibly due to an invalid query or constraint.") from e
        except DriverError as e:
            raise DatabaseError(
                "A driver or session error occurred, possibly due to configuration issues.") from e

    return wrapper
