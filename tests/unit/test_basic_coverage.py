"""Basic tests to improve coverage on core modules."""

from airtable_mcp.api import (
    AirtableAPIError,
    AirtableAuthError,
    AirtableClient,
    AirtableRateLimitError,
)


class TestBasicImports:
    """Test basic imports and initialization to improve coverage."""

    def test_exception_imports(self):
        """Test that exceptions can be imported and created."""
        # Test basic exception creation
        api_error = AirtableAPIError("Test error")
        assert str(api_error) == "Test error"

        auth_error = AirtableAuthError("Auth error")
        assert str(auth_error) == "Auth error"
        assert isinstance(auth_error, AirtableAPIError)

        rate_error = AirtableRateLimitError("Rate error")
        assert str(rate_error) == "Rate error"
        assert isinstance(rate_error, AirtableAPIError)

    def test_client_import(self):
        """Test that client can be imported."""
        # Just test that we can reference the class
        assert AirtableClient is not None
        assert hasattr(AirtableClient, "__init__")


class TestBasicModuleInitialization:
    """Test basic module initialization."""

    def test_airtable_mcp_init(self):
        """Test airtable_mcp module initialization."""
        import airtable_mcp

        assert hasattr(airtable_mcp, "__version__")
        assert airtable_mcp.__version__ == "0.1.0"

    def test_api_init(self):
        """Test API module initialization."""
        from airtable_mcp import api

        assert hasattr(api, "AirtableClient")
        assert hasattr(api, "AirtableAPIError")

    def test_mcp_oauth_lib_utils_init(self):
        """Test mcp_oauth_lib utils initialization."""
        import mcp_oauth_lib.utils

        # Just verify the module loads
        assert mcp_oauth_lib.utils is not None
