"""Unit tests for PKCE utilities."""

import string
from unittest.mock import patch

import pytest

from mcp_oauth_lib.utils.pkce import (
    generate_pkce_pair,
    generate_provider_compatible_pkce,
    validate_code_verifier_format,
    validate_pkce,
)


class TestGeneratePkcePair:
    """Test cases for generate_pkce_pair function."""

    def test_generate_pkce_pair_default(self):
        """Test PKCE pair generation with default parameters."""
        code_verifier, code_challenge = generate_pkce_pair()

        # Check code verifier properties
        assert len(code_verifier) == 128
        assert all(
            c in string.ascii_letters + string.digits + "-._~" for c in code_verifier
        )

        # Check code challenge properties (S256 by default)
        assert len(code_challenge) == 43  # SHA256 hash base64url encoded
        assert all(
            c in string.ascii_letters + string.digits + "-_" for c in code_challenge
        )
        assert "=" not in code_challenge  # No padding

    def test_generate_pkce_pair_s256(self):
        """Test PKCE pair generation with S256 method."""
        code_verifier, code_challenge = generate_pkce_pair(method="S256", length=43)

        assert len(code_verifier) == 43
        assert len(code_challenge) == 43

        # Verify the challenge is computed correctly
        import base64
        import hashlib

        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        expected_challenge = (
            base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
        )
        assert code_challenge == expected_challenge

    def test_generate_pkce_pair_plain(self):
        """Test PKCE pair generation with plain method."""
        code_verifier, code_challenge = generate_pkce_pair(method="plain", length=64)

        assert len(code_verifier) == 64
        assert code_verifier == code_challenge

    def test_generate_pkce_pair_custom_character_set(self):
        """Test PKCE pair generation with custom character set."""
        custom_charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        code_verifier, code_challenge = generate_pkce_pair(
            length=50, character_set=custom_charset
        )

        assert len(code_verifier) == 50
        assert all(c in custom_charset for c in code_verifier)

    def test_generate_pkce_pair_invalid_length(self):
        """Test PKCE pair generation with invalid length."""
        with pytest.raises(ValueError, match="length must be between 43 and 128"):
            generate_pkce_pair(length=42)

        with pytest.raises(ValueError, match="length must be between 43 and 128"):
            generate_pkce_pair(length=129)

    def test_generate_pkce_pair_invalid_method(self):
        """Test PKCE pair generation with invalid method."""
        with pytest.raises(ValueError, match="Unsupported PKCE method"):
            generate_pkce_pair(method="invalid")

    def test_generate_pkce_pair_randomness(self):
        """Test that generated PKCE pairs are different each time."""
        pairs = [generate_pkce_pair() for _ in range(5)]
        verifiers = [pair[0] for pair in pairs]
        challenges = [pair[1] for pair in pairs]

        # All verifiers should be unique
        assert len(set(verifiers)) == 5
        # All challenges should be unique
        assert len(set(challenges)) == 5


class TestGenerateProviderCompatiblePkce:
    """Test cases for generate_provider_compatible_pkce function."""

    def test_generate_provider_compatible_pkce_default(self):
        """Test provider-compatible PKCE generation with minimal requirements."""
        requirements = {}
        code_verifier, code_challenge = generate_provider_compatible_pkce(requirements)

        # Should use defaults
        assert len(code_verifier) == 128  # max_length default
        assert len(code_challenge) == 43

    def test_generate_provider_compatible_pkce_airtable(self):
        """Test provider-compatible PKCE generation for Airtable requirements."""
        requirements = {
            "min_length": 43,
            "max_length": 128,
            "character_set": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_",
            "methods_supported": ["S256", "plain"],
        }

        code_verifier, code_challenge = generate_provider_compatible_pkce(requirements)

        assert len(code_verifier) == 128  # Uses max length
        assert all(c in requirements["character_set"] for c in code_verifier)
        assert "~" not in code_verifier  # Airtable doesn't allow ~

    def test_generate_provider_compatible_pkce_custom_length(self):
        """Test provider-compatible PKCE generation with custom length constraints."""
        requirements = {
            "min_length": 50,
            "max_length": 80,
            "character_set": "ABC123",
        }

        code_verifier, code_challenge = generate_provider_compatible_pkce(requirements)

        assert len(code_verifier) == 80  # Uses max length
        assert all(c in "ABC123" for c in code_verifier)

    def test_generate_provider_compatible_pkce_plain_method(self):
        """Test provider-compatible PKCE generation with plain method."""
        requirements = {"max_length": 60}

        code_verifier, code_challenge = generate_provider_compatible_pkce(
            requirements, method="plain"
        )

        assert len(code_verifier) == 60
        assert code_verifier == code_challenge


class TestValidatePkce:
    """Test cases for validate_pkce function."""

    def test_validate_pkce_s256_valid(self):
        """Test PKCE validation with valid S256 parameters."""
        code_verifier = "test_verifier_12345"

        import base64
        import hashlib

        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

        assert validate_pkce(code_verifier, code_challenge, "S256")

    def test_validate_pkce_s256_invalid(self):
        """Test PKCE validation with invalid S256 parameters."""
        code_verifier = "test_verifier"
        code_challenge = "invalid_challenge"

        assert not validate_pkce(code_verifier, code_challenge, "S256")

    def test_validate_pkce_plain_valid(self):
        """Test PKCE validation with valid plain parameters."""
        code_verifier = "test_verifier_plain"
        code_challenge = "test_verifier_plain"

        assert validate_pkce(code_verifier, code_challenge, "plain")

    def test_validate_pkce_plain_invalid(self):
        """Test PKCE validation with invalid plain parameters."""
        code_verifier = "test_verifier"
        code_challenge = "different_challenge"

        assert not validate_pkce(code_verifier, code_challenge, "plain")

    def test_validate_pkce_unsupported_method(self):
        """Test PKCE validation with unsupported method."""
        with patch("mcp_oauth_lib.utils.pkce.logger") as mock_logger:
            result = validate_pkce("verifier", "challenge", "invalid_method")

            assert not result
            mock_logger.error.assert_called_once()

    def test_validate_pkce_exception_handling(self):
        """Test PKCE validation with exception during processing."""
        with patch("mcp_oauth_lib.utils.pkce.hashlib.sha256") as mock_sha256:
            mock_sha256.side_effect = Exception("Hash error")

            with patch("mcp_oauth_lib.utils.pkce.logger") as mock_logger:
                result = validate_pkce("verifier", "challenge", "S256")

                assert not result
                mock_logger.error.assert_called_once()

    def test_validate_pkce_generated_pair(self):
        """Test PKCE validation with generated pair."""
        code_verifier, code_challenge = generate_pkce_pair(method="S256")
        assert validate_pkce(code_verifier, code_challenge, "S256")

        code_verifier, code_challenge = generate_pkce_pair(method="plain")
        assert validate_pkce(code_verifier, code_challenge, "plain")


class TestValidateCodeVerifierFormat:
    """Test cases for validate_code_verifier_format function."""

    def test_validate_code_verifier_format_valid_default(self):
        """Test code verifier format validation with valid default format."""
        code_verifier = "a" * 43  # Minimum length
        is_valid, error = validate_code_verifier_format(code_verifier)

        assert is_valid
        assert error is None

    def test_validate_code_verifier_format_valid_max_length(self):
        """Test code verifier format validation with maximum length."""
        code_verifier = "a" * 128
        is_valid, error = validate_code_verifier_format(code_verifier)

        assert is_valid
        assert error is None

    def test_validate_code_verifier_format_too_short(self):
        """Test code verifier format validation with too short verifier."""
        code_verifier = "a" * 42
        is_valid, error = validate_code_verifier_format(code_verifier)

        assert not is_valid
        assert "length must be between 43 and 128" in error
        assert "got 42" in error

    def test_validate_code_verifier_format_too_long(self):
        """Test code verifier format validation with too long verifier."""
        code_verifier = "a" * 129
        is_valid, error = validate_code_verifier_format(code_verifier)

        assert not is_valid
        assert "length must be between 43 and 128" in error
        assert "got 129" in error

    def test_validate_code_verifier_format_invalid_characters(self):
        """Test code verifier format validation with invalid characters."""
        code_verifier = "a" * 42 + "@"  # @ is not in RFC 7636 character set
        is_valid, error = validate_code_verifier_format(code_verifier)

        assert not is_valid
        assert "invalid characters" in error
        assert "@" in error

    def test_validate_code_verifier_format_custom_requirements(self):
        """Test code verifier format validation with custom requirements."""
        requirements = {
            "min_length": 50,
            "max_length": 80,
            "character_set": "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789",
        }

        # Valid case
        code_verifier = "A" * 60
        is_valid, error = validate_code_verifier_format(code_verifier, requirements)
        assert is_valid
        assert error is None

        # Invalid length
        code_verifier = "A" * 49
        is_valid, error = validate_code_verifier_format(code_verifier, requirements)
        assert not is_valid
        assert "length must be between 50 and 80" in error

        # Invalid character
        code_verifier = "A" * 59 + "a"  # lowercase not in character set
        is_valid, error = validate_code_verifier_format(code_verifier, requirements)
        assert not is_valid
        assert "invalid characters" in error

    def test_validate_code_verifier_format_rfc7636_characters(self):
        """Test code verifier format validation with RFC 7636 compliant characters."""
        # Test all allowed characters
        rfc_chars = string.ascii_letters + string.digits + "-._~"
        code_verifier = rfc_chars[:43]  # Use first 43 characters

        is_valid, error = validate_code_verifier_format(code_verifier)
        assert is_valid
        assert error is None

    def test_validate_code_verifier_format_none_requirements(self):
        """Test code verifier format validation with None requirements."""
        code_verifier = "a" * 43
        is_valid, error = validate_code_verifier_format(code_verifier, None)

        assert is_valid
        assert error is None

    def test_validate_code_verifier_format_empty_character_set(self):
        """Test code verifier format validation with empty character set requirement."""
        requirements = {"character_set": None}
        code_verifier = "a@#$%^&*()" * 5  # Contains special characters

        # Should pass since character_set is None (no restriction)
        is_valid, error = validate_code_verifier_format(code_verifier, requirements)
        assert is_valid
        assert error is None


class TestPkceIntegration:
    """Integration tests for PKCE utilities."""

    def test_full_pkce_flow_s256(self):
        """Test complete PKCE flow with S256 method."""
        # Generate pair
        code_verifier, code_challenge = generate_pkce_pair(method="S256")

        # Validate format
        is_valid, error = validate_code_verifier_format(code_verifier)
        assert is_valid
        assert error is None

        # Validate PKCE
        assert validate_pkce(code_verifier, code_challenge, "S256")

    def test_full_pkce_flow_plain(self):
        """Test complete PKCE flow with plain method."""
        # Generate pair
        code_verifier, code_challenge = generate_pkce_pair(method="plain")

        # Validate format
        is_valid, error = validate_code_verifier_format(code_verifier)
        assert is_valid
        assert error is None

        # Validate PKCE
        assert validate_pkce(code_verifier, code_challenge, "plain")

    def test_airtable_compatible_pkce_flow(self):
        """Test PKCE flow with Airtable-compatible requirements."""
        airtable_requirements = {
            "min_length": 43,
            "max_length": 128,
            "character_set": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_",
            "methods_supported": ["S256", "plain"],
        }

        # Generate Airtable-compatible pair
        code_verifier, code_challenge = generate_provider_compatible_pkce(
            airtable_requirements, method="S256"
        )

        # Validate format against Airtable requirements
        is_valid, error = validate_code_verifier_format(
            code_verifier, airtable_requirements
        )
        assert is_valid
        assert error is None

        # Validate PKCE
        assert validate_pkce(code_verifier, code_challenge, "S256")

        # Ensure no tilde character (Airtable restriction)
        assert "~" not in code_verifier

    def test_cross_validation_failure(self):
        """Test that PKCE validation fails with mismatched pairs."""
        code_verifier1, code_challenge1 = generate_pkce_pair(method="S256")
        code_verifier2, code_challenge2 = generate_pkce_pair(method="S256")

        # Cross-validation should fail
        assert not validate_pkce(code_verifier1, code_challenge2, "S256")
        assert not validate_pkce(code_verifier2, code_challenge1, "S256")
