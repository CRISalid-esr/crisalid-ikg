# Description: Custom errors for unreadable messages
class UnreadableMessageError(ValueError):
    """
    Unreadable message error
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
