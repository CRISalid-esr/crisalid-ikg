""" Not found error handler. """

from app.errors.not_found_error import NotFoundError


class ReferenceOwnerNotFoundError(NotFoundError):
    """
    Raised when the person on behalf of whom a source record was harvested is not found
    """
