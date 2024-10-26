""" Not found error handler. """


class ReferenceOwnerNotFoundError(ValueError):
    """
    Raised when the person on behalf of whom a source record was harvested is not found
    """
