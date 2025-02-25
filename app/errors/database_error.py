""" Database error handler. """
import asyncio
import traceback
from functools import wraps
from random import random

from loguru import logger

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from neo4j.exceptions import (
    ClientError, DatabaseError as Neo4jDatabaseError,
    TransientError,
    DriverError,
    ServiceUnavailable
)

MAX_RETRIES = 3
RETRY_DELAY = 2


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
    Includes retry logic for TransientError with deadlock detection.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                return await func(*args, **kwargs)
            except TransientError as e:
                if e.code == 'Neo.TransientError.Transaction.DeadlockDetected':
                    if retries < MAX_RETRIES:
                        retries += 1
                        # add a random delay to avoid contention
                        await asyncio.sleep(RETRY_DELAY + int(random() * 10) / 10)
                        continue
                    raise DatabaseError(
                        f"Max retries reached for deadlock detected: {e.code}"
                    ) from e
                raise DatabaseError("A transient error occurred.") from e
            except Neo4jDatabaseError as e:
                logger.error(traceback.format_exc())
                raise DatabaseError("A database error occurred.") from e
            except ServiceUnavailable as e:
                raise DatabaseError("The Neo4j service is unavailable or misconfigured."
                                    ) from e
            except ClientError as e:
                logger.error(traceback.format_exc())
                raise DatabaseError(
                    "A client error occurred, possibly due to an invalid query or constraint."
                ) from e
            except DriverError as e:
                logger.error(traceback.format_exc())
                raise DatabaseError(
                    "A driver or session error occurred, possibly due to configuration issues."
                ) from e

    return wrapper
