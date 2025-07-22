"""Unit tests for OAuth configuration classes."""

from dataclasses import fields
from typing import Any

import pytest

from mcp_oauth_lib.core.config import OAuthConfig, ProviderConfig


class MockProviderConfig(ProviderConfig):
    """Mock implementation of ProviderConfig for testing."""

    def get_authorization_url(self) -> str:
        return "https://example.com/auth"

    def get_token_url(self) -> str:
        return "https://example.com/token"

    def get_pkce_requirements(self) -> dict[str, Any]:
        return {
            "min_length": 43,
            "max_length": 128,
            "character_set": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~",
            "methods_supported": ["S256", "plain"],
            "required": True,
        }

    def get_supported_scopes(self) -> list[str]:
        return ["read", "write", "admin"]


class TestProviderConfig:
    """Test cases for ProviderConfig abstract base class."""

    def test_provider_config_instantiation(self):
        """Test that ProviderConfig can be instantiated with concrete implementation."""
        config = MockProviderConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            scope="read write",
            provider_name="test_provider",
        )

        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"
        assert config.redirect_uri == "http://localhost:8080/callback"
        assert config.scope == "read write"
        assert config.provider_name == "test_provider"

    def test_provider_config_abstract_methods(self):
        """Test that abstract methods are implemented in concrete class."""
        config = MockProviderConfig(
            client_id="test",
            client_secret="secret",
            redirect_uri="http://localhost/callback",
            scope="read",
            provider_name="mock",
        )

        # Test all abstract methods work
        assert config.get_authorization_url() == "https://example.com/auth"
        assert config.get_token_url() == "https://example.com/token"

        pkce_req = config.get_pkce_requirements()
        assert isinstance(pkce_req, dict)
        assert "min_length" in pkce_req

        scopes = config.get_supported_scopes()
        assert isinstance(scopes, list)
        assert "read" in scopes

    def test_provider_config_dataclass_fields(self):
        """Test that ProviderConfig has correct dataclass fields."""
        config_fields = {field.name for field in fields(ProviderConfig)}
        expected_fields = {
            "client_id",
            "client_secret",
            "redirect_uri",
            "scope",
            "provider_name",
        }

        assert config_fields == expected_fields

    def test_provider_config_cannot_instantiate_directly(self):
        """Test that ProviderConfig cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ProviderConfig(
                client_id="test",
                client_secret="secret",
                redirect_uri="http://localhost/callback",
                scope="read",
                provider_name="abstract",
            )


class TestOAuthConfig:
    """Test cases for OAuthConfig dataclass."""

    def test_oauth_config_defaults(self):
        """Test OAuthConfig instantiation with default values."""
        config = OAuthConfig()

        # Test default values
        assert config.server_name == "mcp-oauth-server"
        assert config.server_version == "0.1.0"
        assert config.mcp_version == "2024-11-05"
        assert config.host == "localhost"
        assert config.port == 8000
        assert config.base_url is None
        assert config.state_expiry_seconds == 600
        assert config.auth_code_expiry_seconds == 600
        assert config.enable_pkce is True
        assert config.require_pkce is False
        assert config.enable_dynamic_registration is True
        assert config.registration_access_token is None
        assert config.token_manager is None

    def test_oauth_config_custom_values(self):
        """Test OAuthConfig instantiation with custom values."""
        config = OAuthConfig(
            server_name="custom-server",
            server_version="2.0.0",
            mcp_version="2025-01-01",
            host="0.0.0.0",
            port=9000,
            base_url="https://custom.example.com",
            state_expiry_seconds=1200,
            auth_code_expiry_seconds=900,
            enable_pkce=False,
            require_pkce=True,
            enable_dynamic_registration=False,
            registration_access_token="custom_token",
        )

        assert config.server_name == "custom-server"
        assert config.server_version == "2.0.0"
        assert config.mcp_version == "2025-01-01"
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.base_url == "https://custom.example.com"
        assert config.state_expiry_seconds == 1200
        assert config.auth_code_expiry_seconds == 900
        assert config.enable_pkce is False
        assert config.require_pkce is True
        assert config.enable_dynamic_registration is False
        assert config.registration_access_token == "custom_token"

    def test_oauth_config_default_lists(self):
        """Test OAuthConfig default list values."""
        config = OAuthConfig()

        # Test default lists
        assert config.supported_response_types == ["code"]
        assert config.supported_grant_types == ["authorization_code", "refresh_token"]
        assert config.supported_auth_methods == [
            "client_secret_basic",
            "client_secret_post",
            "none",
        ]
        assert config.cors_origins == ["*"]
        assert config.cors_methods == ["GET", "POST", "OPTIONS"]
        assert config.cors_headers == ["Content-Type", "Authorization"]

    def test_oauth_config_custom_lists(self):
        """Test OAuthConfig with custom list values."""
        config = OAuthConfig(
            supported_response_types=["code", "token"],
            supported_grant_types=["authorization_code", "client_credentials"],
            supported_auth_methods=["client_secret_basic"],
            cors_origins=["https://example.com"],
            cors_methods=["GET", "POST"],
            cors_headers=["Content-Type", "X-Custom-Header"],
        )

        assert config.supported_response_types == ["code", "token"]
        assert config.supported_grant_types == [
            "authorization_code",
            "client_credentials",
        ]
        assert config.supported_auth_methods == ["client_secret_basic"]
        assert config.cors_origins == ["https://example.com"]
        assert config.cors_methods == ["GET", "POST"]
        assert config.cors_headers == ["Content-Type", "X-Custom-Header"]

    def test_get_base_url_with_custom_base_url(self):
        """Test get_base_url when custom base_url is provided."""
        config = OAuthConfig(base_url="https://custom.example.com:9443")

        base_url = config.get_base_url()
        assert base_url == "https://custom.example.com:9443"

    def test_get_base_url_constructed_from_host_port(self):
        """Test get_base_url constructed from host and port."""
        config = OAuthConfig(host="api.example.com", port=8443)

        base_url = config.get_base_url()
        assert base_url == "http://api.example.com:8443"

    def test_get_base_url_default_localhost(self):
        """Test get_base_url with default localhost configuration."""
        config = OAuthConfig()

        base_url = config.get_base_url()
        assert base_url == "http://localhost:8000"

    def test_get_metadata_endpoint(self):
        """Test get_metadata_endpoint URL construction."""
        config = OAuthConfig(host="auth.example.com", port=8080)

        metadata_endpoint = config.get_metadata_endpoint()
        expected = "http://auth.example.com:8080/.well-known/oauth-authorization-server"
        assert metadata_endpoint == expected

    def test_get_metadata_endpoint_with_custom_base_url(self):
        """Test get_metadata_endpoint with custom base URL."""
        config = OAuthConfig(base_url="https://secure.auth.com")

        metadata_endpoint = config.get_metadata_endpoint()
        expected = "https://secure.auth.com/.well-known/oauth-authorization-server"
        assert metadata_endpoint == expected

    def test_get_authorization_endpoint(self):
        """Test get_authorization_endpoint URL construction."""
        config = OAuthConfig(host="oauth.example.com", port=9000)

        auth_endpoint = config.get_authorization_endpoint()
        expected = "http://oauth.example.com:9000/auth/authorize"
        assert auth_endpoint == expected

    def test_get_authorization_endpoint_with_custom_base_url(self):
        """Test get_authorization_endpoint with custom base URL."""
        config = OAuthConfig(base_url="https://auth.myservice.io")

        auth_endpoint = config.get_authorization_endpoint()
        expected = "https://auth.myservice.io/auth/authorize"
        assert auth_endpoint == expected

    def test_get_token_endpoint(self):
        """Test get_token_endpoint URL construction."""
        config = OAuthConfig(host="token.example.com", port=8443)

        token_endpoint = config.get_token_endpoint()
        expected = "http://token.example.com:8443/token"
        assert token_endpoint == expected

    def test_get_token_endpoint_with_custom_base_url(self):
        """Test get_token_endpoint with custom base URL."""
        config = OAuthConfig(base_url="https://tokens.secure.net")

        token_endpoint = config.get_token_endpoint()
        expected = "https://tokens.secure.net/token"
        assert token_endpoint == expected

    def test_get_registration_endpoint(self):
        """Test get_registration_endpoint URL construction."""
        config = OAuthConfig(host="register.example.com", port=7000)

        registration_endpoint = config.get_registration_endpoint()
        expected = "http://register.example.com:7000/oauth/register"
        assert registration_endpoint == expected

    def test_get_registration_endpoint_with_custom_base_url(self):
        """Test get_registration_endpoint with custom base URL."""
        config = OAuthConfig(base_url="https://dyn-reg.oauth.com")

        registration_endpoint = config.get_registration_endpoint()
        expected = "https://dyn-reg.oauth.com/oauth/register"
        assert registration_endpoint == expected

    def test_all_endpoints_consistency(self):
        """Test that all endpoint methods use the same base URL."""
        config = OAuthConfig(base_url="https://consistent.oauth.server")

        base_url = config.get_base_url()
        metadata_endpoint = config.get_metadata_endpoint()
        auth_endpoint = config.get_authorization_endpoint()
        token_endpoint = config.get_token_endpoint()
        registration_endpoint = config.get_registration_endpoint()

        # All endpoints should start with the same base URL
        assert metadata_endpoint.startswith(base_url)
        assert auth_endpoint.startswith(base_url)
        assert token_endpoint.startswith(base_url)
        assert registration_endpoint.startswith(base_url)

    def test_oauth_config_dataclass_fields(self):
        """Test that OAuthConfig has expected dataclass fields."""
        config_fields = {field.name for field in fields(OAuthConfig)}
        expected_fields = {
            "server_name",
            "server_version",
            "mcp_version",
            "host",
            "port",
            "base_url",
            "state_expiry_seconds",
            "auth_code_expiry_seconds",
            "enable_pkce",
            "require_pkce",
            "supported_response_types",
            "supported_grant_types",
            "supported_auth_methods",
            "enable_dynamic_registration",
            "registration_access_token",
            "token_manager",
            "cors_origins",
            "cors_methods",
            "cors_headers",
        }

        assert config_fields == expected_fields

    def test_oauth_config_with_token_manager(self):
        """Test OAuthConfig with custom token manager."""
        mock_token_manager = object()  # Simple object as placeholder

        config = OAuthConfig(token_manager=mock_token_manager)

        assert config.token_manager is mock_token_manager

    def test_oauth_config_security_settings(self):
        """Test OAuth security-related configuration settings."""
        # Test secure configuration
        secure_config = OAuthConfig(
            enable_pkce=True,
            require_pkce=True,
            supported_auth_methods=["client_secret_basic"],
            cors_origins=["https://trusted-domain.com"],
        )

        assert secure_config.enable_pkce is True
        assert secure_config.require_pkce is True
        assert secure_config.supported_auth_methods == ["client_secret_basic"]
        assert secure_config.cors_origins == ["https://trusted-domain.com"]

    def test_oauth_config_timeout_settings(self):
        """Test OAuth timeout configuration settings."""
        config = OAuthConfig(
            state_expiry_seconds=300,  # 5 minutes
            auth_code_expiry_seconds=120,  # 2 minutes
        )

        assert config.state_expiry_seconds == 300
        assert config.auth_code_expiry_seconds == 120

    def test_oauth_config_dynamic_registration_settings(self):
        """Test dynamic client registration configuration."""
        # With dynamic registration enabled
        config_enabled = OAuthConfig(
            enable_dynamic_registration=True,
            registration_access_token="secure_token_123",
        )

        assert config_enabled.enable_dynamic_registration is True
        assert config_enabled.registration_access_token == "secure_token_123"

        # With dynamic registration disabled
        config_disabled = OAuthConfig(enable_dynamic_registration=False)

        assert config_disabled.enable_dynamic_registration is False
        assert config_disabled.registration_access_token is None  # Default


class TestConfigIntegration:
    """Integration tests for configuration classes."""

    def test_provider_config_with_oauth_config(self):
        """Test integration between ProviderConfig and OAuthConfig."""
        oauth_config = OAuthConfig(
            host="integration.test.com",
            port=8888,
            enable_pkce=True,
        )

        provider_config = MockProviderConfig(
            client_id="integration_client",
            client_secret="integration_secret",
            redirect_uri=f"{oauth_config.get_base_url()}/callback",
            scope="read write admin",
            provider_name="integration_provider",
        )

        # Test that provider config can use OAuth config base URL
        assert (
            provider_config.redirect_uri == "http://integration.test.com:8888/callback"
        )

        # Test provider methods
        assert provider_config.get_authorization_url() == "https://example.com/auth"
        assert provider_config.get_token_url() == "https://example.com/token"

        # Test PKCE compatibility
        pkce_requirements = provider_config.get_pkce_requirements()
        assert pkce_requirements["required"] == oauth_config.enable_pkce

    def test_endpoint_url_consistency(self):
        """Test that all endpoint URLs are consistent across different configurations."""
        configs = [
            OAuthConfig(),  # Default
            OAuthConfig(host="custom.host.com", port=9999),
            OAuthConfig(base_url="https://completely.custom.domain"),
        ]

        for config in configs:
            base_url = config.get_base_url()

            # All endpoints should be properly formed URLs
            assert config.get_metadata_endpoint().startswith(base_url)
            assert config.get_authorization_endpoint().startswith(base_url)
            assert config.get_token_endpoint().startswith(base_url)
            assert config.get_registration_endpoint().startswith(base_url)

            # Each endpoint should have its specific path
            assert (
                "/.well-known/oauth-authorization-server"
                in config.get_metadata_endpoint()
            )
            assert "/auth/authorize" in config.get_authorization_endpoint()
            assert "/token" in config.get_token_endpoint()
            assert "/oauth/register" in config.get_registration_endpoint()

    def test_config_immutability_simulation(self):
        """Test that configurations behave as expected when modified."""
        config = OAuthConfig(server_name="original")

        # Test that we can modify the configuration
        config.server_name = "modified"
        assert config.server_name == "modified"

        # Test that list fields can be modified
        original_cors_origins = config.cors_origins.copy()
        config.cors_origins.append("https://new-origin.com")

        assert len(config.cors_origins) > len(original_cors_origins)
        assert "https://new-origin.com" in config.cors_origins
