"""Unit tests for OAuth utility modules."""

import pytest

from mcp_oauth_lib.utils.pkce import (
    generate_pkce_pair,
    generate_provider_compatible_pkce,
    validate_code_verifier_format,
    validate_pkce,
)


class TestPKCEUtils:
    """Test cases for PKCE utility functions."""

    def test_generate_pkce_pair_default(self):
        """Test PKCE pair generation with default parameters."""
        verifier, challenge = generate_pkce_pair()

        assert isinstance(verifier, str)
        assert isinstance(challenge, str)
        assert 43 <= len(verifier) <= 128
        assert challenge != verifier  # Should be different for S256

    def test_generate_pkce_pair_s256(self):
        """Test PKCE pair generation with S256 method."""
        verifier, challenge = generate_pkce_pair(method="S256", length=50)

        assert len(verifier) == 50
        assert len(challenge) == 43  # Base64url encoded SHA256 is 43 chars
        assert challenge != verifier

    def test_generate_pkce_pair_plain(self):
        """Test PKCE pair generation with plain method."""
        verifier, challenge = generate_pkce_pair(method="plain", length=50)

        assert len(verifier) == 50
        assert challenge == verifier  # Should be same for plain

    def test_generate_pkce_pair_custom_charset(self):
        """Test PKCE pair generation with custom character set."""
        charset = "abcdefghijklmnopqrstuvwxyz0123456789"
        verifier, challenge = generate_pkce_pair(
            method="S256", length=50, character_set=charset
        )

        assert len(verifier) == 50
        assert all(c in charset for c in verifier)

    def test_generate_pkce_pair_invalid_length(self):
        """Test PKCE pair generation with invalid length."""
        with pytest.raises(ValueError, match="Code verifier length must be between"):
            generate_pkce_pair(length=42)  # Too short

        with pytest.raises(ValueError, match="Code verifier length must be between"):
            generate_pkce_pair(length=129)  # Too long

    def test_generate_pkce_pair_invalid_method(self):
        """Test PKCE pair generation with invalid method."""
        with pytest.raises(ValueError, match="Unsupported PKCE method"):
            generate_pkce_pair(method="invalid")

    def test_generate_provider_compatible_pkce(self):
        """Test provider-compatible PKCE generation."""
        requirements = {
            "min_length": 43,
            "max_length": 128,
            "character_set": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_",
        }

        verifier, challenge = generate_provider_compatible_pkce(requirements, "S256")

        assert 43 <= len(verifier) <= 128
        assert all(c in requirements["character_set"] for c in verifier)
        assert challenge != verifier

    def test_validate_pkce_s256_valid(self):
        """Test PKCE validation with valid S256 challenge."""
        verifier, challenge = generate_pkce_pair(method="S256")

        assert validate_pkce(verifier, challenge, "S256") is True

    def test_validate_pkce_s256_invalid(self):
        """Test PKCE validation with invalid S256 challenge."""
        verifier = "test_verifier_123456789012345678901234567890"
        challenge = "invalid_challenge"

        assert validate_pkce(verifier, challenge, "S256") is False

    def test_validate_pkce_plain_valid(self):
        """Test PKCE validation with valid plain challenge."""
        verifier, challenge = generate_pkce_pair(method="plain")

        assert validate_pkce(verifier, challenge, "plain") is True

    def test_validate_pkce_plain_invalid(self):
        """Test PKCE validation with invalid plain challenge."""
        verifier = "test_verifier_123456789012345678901234567890"
        challenge = "different_challenge"

        assert validate_pkce(verifier, challenge, "plain") is False

    def test_validate_pkce_invalid_method(self):
        """Test PKCE validation with invalid method."""
        verifier = "test_verifier_123456789012345678901234567890"
        challenge = "test_challenge"

        assert validate_pkce(verifier, challenge, "invalid") is False

    def test_validate_code_verifier_format_valid(self):
        """Test code verifier format validation with valid verifier."""
        verifier = "test_verifier_123456789012345678901234567890"

        is_valid, error = validate_code_verifier_format(verifier)
        assert is_valid is True
        assert error is None

    def test_validate_code_verifier_format_too_short(self):
        """Test code verifier format validation with too short verifier."""
        verifier = "short"

        is_valid, error = validate_code_verifier_format(verifier)
        assert is_valid is False
        assert "length must be between" in error

    def test_validate_code_verifier_format_too_long(self):
        """Test code verifier format validation with too long verifier."""
        verifier = "a" * 200

        is_valid, error = validate_code_verifier_format(verifier)
        assert is_valid is False
        assert "length must be between" in error

    def test_validate_code_verifier_format_invalid_chars(self):
        """Test code verifier format validation with invalid characters."""
        # Make it long enough but with invalid chars
        verifier = "test_verifier_with_invalid_chars_at_symbol@#$%^&*()" + "a" * 20

        is_valid, error = validate_code_verifier_format(verifier)
        assert is_valid is False
        assert "invalid characters" in error

    def test_validate_code_verifier_format_custom_requirements(self):
        """Test code verifier format validation with custom requirements."""
        requirements = {
            "min_length": 20,
            "max_length": 50,
            "character_set": "abcdefghijklmnopqrstuvwxyz0123456789",
        }

        verifier = "validverifier12345678901234567890"
        is_valid, error = validate_code_verifier_format(verifier, requirements)
        assert is_valid is True
        assert error is None

        # Test with invalid character
        verifier_invalid = "invalid_verifier_with_underscore"
        is_valid, error = validate_code_verifier_format(verifier_invalid, requirements)
        assert is_valid is False
        assert "invalid characters" in error
