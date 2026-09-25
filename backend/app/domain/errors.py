"""Errors raised by use cases. The API maps them; the model never raises them."""


class AppError(Exception):
    """Base type for expected application failures."""


class NotFoundError(AppError):
    """The caller cannot see the resource, or it does not exist."""


class CompanyNotFoundError(AppError):
    """Shared company catalog miss. Safe to describe as a missing company."""


class DuplicateSubmissionError(AppError):
    def __init__(self, existing_id: str) -> None:
        self.existing_id = existing_id
        super().__init__("Duplicate submission")


class ForbiddenError(AppError):
    """The caller is authenticated but cannot perform this action."""


class InvalidTransitionError(AppError):
    """The submission status does not allow the requested action."""


class RetrievalUnavailableError(AppError):
    """Guideline search could not run. No draft was accepted."""


class ToolTimeoutError(AppError):
    """A tool exceeded its deadline. No draft was accepted."""
