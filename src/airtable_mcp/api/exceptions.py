"""Custom exceptions for Airtable API operations."""


class AirtableAPIError(Exception):
    """Base exception for Airtable API errors."""

    def __init__(
        self, message: str, status_code: int = None, response_text: str = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(message)


class AirtableRateLimitError(AirtableAPIError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class AirtableAuthError(AirtableAPIError):
    """Exception raised for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AirtableNotFoundError(AirtableAPIError):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class AirtableValidationError(AirtableAPIError):
    """Exception raised for validation errors."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)
