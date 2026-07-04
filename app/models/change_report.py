from pydantic import BaseModel, Field


class ChangeWarning(BaseModel):
    """
    A per-item problem encountered while applying a Change: the change was applied
    but this particular element was skipped or degraded.
    """

    code: str
    message: str
    context: dict = Field(default_factory=dict)


class ChangeApplicationReport(BaseModel):
    """
    Outcome report of a change application, accumulated by change processors.
    An empty warnings list means a clean success.
    """

    warnings: list[ChangeWarning] = []

    def add_warning(self, code: str, message: str, **context) -> None:
        """
        Record a per-item warning.
        :param code: machine-readable warning code (e.g. "UNRESOLVABLE_PERSON")
        :param message: human-readable description
        :param context: JSON-serializable details (names, identifiers, error strings)
        """
        self.warnings.append(ChangeWarning(code=code, message=message, context=context))
