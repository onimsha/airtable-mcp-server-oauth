"""Unit tests for API exceptions."""

import pytest

from airtable_mcp.api.exceptions import (
    AirtableAPIError,
    AirtableAuthError,
    AirtableRateLimitError,
)


class TestAirtableAPIError:
    """Test cases for AirtableAPIError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = AirtableAPIError("Test error message")

        assert str(error) == "Test error message"
        assert error.status_code is None
        assert error.error_code is None

    def test_error_with_status_code(self):
        """Test error with status code."""
        error = AirtableAPIError("Test error", status_code=400)

        assert str(error) == "Test error"
        assert error.status_code == 400

    def test_error_with_error_code(self):
        """Test error with error code."""
        error = AirtableAPIError("Test error", error_code="INVALID_REQUEST")

        assert str(error) == "Test error"
        assert error.error_code == "INVALID_REQUEST"

    def test_error_with_all_parameters(self):
        """Test error with all parameters."""
        error = AirtableAPIError(
            "Test error", status_code=422, error_code="INVALID_REQUEST_BODY"
        )

        assert str(error) == "Test error"
        assert error.status_code == 422
        assert error.error_code == "INVALID_REQUEST_BODY"

    def test_error_inheritance(self):
        """Test that AirtableAPIError inherits from Exception."""
        error = AirtableAPIError("Test error")

        assert isinstance(error, Exception)


class TestAirtableAuthError:
    """Test cases for AirtableAuthError."""

    def test_auth_error_creation(self):
        """Test authentication error creation."""
        error = AirtableAuthError("Authentication failed")

        assert str(error) == "Authentication failed"
        assert isinstance(error, AirtableAPIError)

    def test_auth_error_with_status_code(self):
        """Test auth error with status code."""
        error = AirtableAuthError("Invalid token", status_code=401)

        assert str(error) == "Invalid token"
        assert error.status_code == 401

    def test_auth_error_with_error_code(self):
        """Test auth error with error code."""
        error = AirtableAuthError("Token expired", error_code="TOKEN_EXPIRED")

        assert str(error) == "Token expired"
        assert error.error_code == "TOKEN_EXPIRED"


class TestAirtableRateLimitError:
    """Test cases for AirtableRateLimitError."""

    def test_rate_limit_error_creation(self):
        """Test rate limit error creation."""
        error = AirtableRateLimitError("Rate limit exceeded")

        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, AirtableAPIError)

    def test_rate_limit_error_with_status_code(self):
        """Test rate limit error with status code."""
        error = AirtableRateLimitError("Too many requests", status_code=429)

        assert str(error) == "Too many requests"
        assert error.status_code == 429

    def test_rate_limit_error_with_retry_after(self):
        """Test rate limit error with retry after."""
        error = AirtableRateLimitError(
            "Rate limited", status_code=429, error_code="RATE_LIMITED"
        )

        assert str(error) == "Rate limited"
        assert error.status_code == 429
        assert error.error_code == "RATE_LIMITED"


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_inheritance_chain(self):
        """Test that all exceptions follow proper inheritance."""
        # Test AirtableAuthError inheritance
        auth_error = AirtableAuthError("Auth error")
        assert isinstance(auth_error, AirtableAPIError)
        assert isinstance(auth_error, Exception)

        # Test AirtableRateLimitError inheritance
        rate_error = AirtableRateLimitError("Rate error")
        assert isinstance(rate_error, AirtableAPIError)
        assert isinstance(rate_error, Exception)

    def test_exception_catching(self):
        """Test exception catching patterns."""
        # Should be able to catch specific exceptions
        with pytest.raises(AirtableAuthError):
            raise AirtableAuthError("Auth error")

        with pytest.raises(AirtableRateLimitError):
            raise AirtableRateLimitError("Rate error")

        # Should be able to catch base exception
        with pytest.raises(AirtableAPIError):
            raise AirtableAuthError("Auth error")

        with pytest.raises(AirtableAPIError):
            raise AirtableRateLimitError("Rate error")
