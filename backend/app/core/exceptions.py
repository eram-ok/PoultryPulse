class ApplicationError(Exception):
    """Base exception for expected PoultryPulse application errors."""

    status_code: int = 500
    error_code: str = "application_error"

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message

        if error_code is not None:
            self.error_code = error_code


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""

    status_code = 401
    error_code = "authentication_failed"


class AuthorizationError(ApplicationError):
    """Raised when a user lacks permission for an action."""

    status_code = 403
    error_code = "permission_denied"


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested record does not exist."""

    status_code = 404
    error_code = "resource_not_found"


class ResourceConflictError(ApplicationError):
    """Raised when a record conflicts with an existing record."""

    status_code = 409
    error_code = "resource_conflict"


class BusinessRuleError(ApplicationError):
    """Raised when an operation violates a business rule."""

    status_code = 422
    error_code = "business_rule_violation"
