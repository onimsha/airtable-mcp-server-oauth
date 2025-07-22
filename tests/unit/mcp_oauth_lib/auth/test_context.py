"""Unit tests for authentication context management."""

import threading
from unittest.mock import patch

import pytest
from starlette.exceptions import HTTPException

from mcp_oauth_lib.auth.context import AuthContext


class TestAuthContext:
    """Test cases for AuthContext class."""

    def setup_method(self):
        """Setup method to clear context before each test."""
        AuthContext.clear_access_token()

    def teardown_method(self):
        """Cleanup method to clear context after each test."""
        AuthContext.clear_access_token()

    def test_set_and_get_access_token(self):
        """Test setting and getting access token."""
        test_token = "test_access_token_123"

        # Set token
        AuthContext.set_access_token(test_token)

        # Get token
        retrieved_token = AuthContext.get_access_token()
        assert retrieved_token == test_token

    def test_get_access_token_none_when_not_set(self):
        """Test getting access token returns None when not set."""
        token = AuthContext.get_access_token()
        assert token is None

    def test_require_access_token_success(self):
        """Test requiring access token when token is available."""
        test_token = "required_token_456"

        AuthContext.set_access_token(test_token)
        retrieved_token = AuthContext.require_access_token()

        assert retrieved_token == test_token

    def test_require_access_token_raises_when_none(self):
        """Test requiring access token raises HTTPException when not available."""
        with pytest.raises(HTTPException) as exc_info:
            AuthContext.require_access_token()

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Access token required"
        assert "WWW-Authenticate" in exc_info.value.headers
        assert "Bearer realm=" in exc_info.value.headers["WWW-Authenticate"]
        assert "invalid_token" in exc_info.value.headers["WWW-Authenticate"]

    def test_clear_access_token(self):
        """Test clearing access token."""
        test_token = "token_to_clear"

        # Set token
        AuthContext.set_access_token(test_token)
        assert AuthContext.get_access_token() == test_token

        # Clear token
        AuthContext.clear_access_token()
        assert AuthContext.get_access_token() is None

    def test_context_and_thread_local_sync(self):
        """Test that context variable and thread-local storage stay in sync."""
        test_token = "sync_token_789"

        # Set token (should set both context and thread-local)
        AuthContext.set_access_token(test_token)

        # Verify both storage mechanisms have the token
        assert AuthContext.get_access_token() == test_token

        # Clear and verify both are cleared
        AuthContext.clear_access_token()
        assert AuthContext.get_access_token() is None

    def test_thread_local_fallback(self):
        """Test that thread-local storage works as fallback."""
        test_token = "thread_local_token"

        # Set token first (this sets both context and thread-local)
        AuthContext.set_access_token(test_token)

        # Manually clear the context variable to force fallback to thread-local
        import mcp_oauth_lib.auth.context as context_module

        context_module._access_token_context.set(None)

        # Now get token should fall back to thread-local storage
        retrieved_token = AuthContext.get_access_token()

        # Should retrieve from thread-local storage
        assert retrieved_token == test_token

    def test_multiple_token_updates(self):
        """Test multiple token updates overwrite previous values."""
        token1 = "first_token"
        token2 = "second_token"
        token3 = "third_token"

        # Set first token
        AuthContext.set_access_token(token1)
        assert AuthContext.get_access_token() == token1

        # Update to second token
        AuthContext.set_access_token(token2)
        assert AuthContext.get_access_token() == token2

        # Update to third token
        AuthContext.set_access_token(token3)
        assert AuthContext.get_access_token() == token3

    def test_concurrent_thread_isolation(self):
        """Test that different threads can have different tokens."""
        results = {}

        def thread_worker(thread_id: str, token: str):
            """Worker function for testing thread isolation."""
            AuthContext.set_access_token(token)
            # Small delay to allow context switching
            import time

            time.sleep(0.01)
            results[thread_id] = AuthContext.get_access_token()

        # Create and start multiple threads
        threads = []
        for i in range(3):
            token = f"thread_{i}_token"
            thread = threading.Thread(target=thread_worker, args=(f"thread_{i}", token))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify each thread maintained its own token
        assert results["thread_0"] == "thread_0_token"
        assert results["thread_1"] == "thread_1_token"
        assert results["thread_2"] == "thread_2_token"

    def test_logging_on_set_token(self):
        """Test that setting token logs debug message."""
        test_token = "logged_token"

        with patch("mcp_oauth_lib.auth.context.logger") as mock_logger:
            AuthContext.set_access_token(test_token)

            mock_logger.debug.assert_called_once_with(
                "Set access token in both context and thread-local storage"
            )

    def test_logging_on_clear_token(self):
        """Test that clearing token logs debug message."""
        test_token = "token_to_log_clear"

        # Set token first
        AuthContext.set_access_token(test_token)

        with patch("mcp_oauth_lib.auth.context.logger") as mock_logger:
            AuthContext.clear_access_token()

            mock_logger.debug.assert_called_once_with(
                "Cleared access token from context and thread-local storage"
            )

    def test_logging_on_require_token_failure(self):
        """Test that requiring unavailable token logs error message."""
        with patch("mcp_oauth_lib.auth.context.logger") as mock_logger:
            with pytest.raises(HTTPException):
                AuthContext.require_access_token()

            mock_logger.error.assert_called_once_with(
                "No access token found in context or thread-local storage"
            )

    def test_clear_token_when_thread_local_not_set(self):
        """Test clearing token when thread-local attribute doesn't exist."""
        # Ensure clean state
        AuthContext.clear_access_token()

        # Manually clear thread-local to simulate case where it was never set
        import mcp_oauth_lib.auth.context as context_module

        if hasattr(context_module._thread_local, "access_token"):
            delattr(context_module._thread_local, "access_token")

        # This should not raise an exception
        AuthContext.clear_access_token()

        # Verify state is still clean
        assert AuthContext.get_access_token() is None

    def test_token_persistence_across_context_var_reset(self):
        """Test that token persists in thread-local even if context var is reset."""
        test_token = "persistent_token"

        # Set token
        AuthContext.set_access_token(test_token)

        # Manually reset context variable (simulating context boundary)
        import mcp_oauth_lib.auth.context as context_module

        context_module._access_token_context.set(None)

        # Token should still be available via thread-local fallback
        assert AuthContext.get_access_token() == test_token

    def test_empty_string_token_handling(self):
        """Test handling of empty string as token."""
        # Empty string should be treated as no token
        AuthContext.set_access_token("")

        with pytest.raises(HTTPException):
            AuthContext.require_access_token()

    def test_whitespace_token_handling(self):
        """Test handling of whitespace-only token."""
        # Whitespace-only string should be treated as valid token
        whitespace_token = "   "
        AuthContext.set_access_token(whitespace_token)

        retrieved_token = AuthContext.require_access_token()
        assert retrieved_token == whitespace_token


class TestAuthContextStaticMethods:
    """Test that AuthContext methods work correctly as static methods."""

    def test_all_methods_are_static(self):
        """Test that all AuthContext methods can be called without instance."""
        # This test verifies the methods are properly decorated as @staticmethod
        # by calling them directly on the class

        # Test set_access_token
        AuthContext.set_access_token("test_token")

        # Test get_access_token
        token = AuthContext.get_access_token()
        assert token == "test_token"

        # Test require_access_token
        required_token = AuthContext.require_access_token()
        assert required_token == "test_token"

        # Test clear_access_token
        AuthContext.clear_access_token()
        assert AuthContext.get_access_token() is None

    def test_no_instance_state(self):
        """Test that AuthContext doesn't maintain instance state."""
        # Creating instances should not affect static behavior
        context1 = AuthContext()
        context2 = AuthContext()

        # Set token using class method
        AuthContext.set_access_token("class_token")

        # Both instances should see the same token (since it's static)
        assert context1.get_access_token() == "class_token"
        assert context2.get_access_token() == "class_token"

        # Clear using instance method
        context1.clear_access_token()

        # All should see the cleared state
        assert AuthContext.get_access_token() is None
        assert context2.get_access_token() is None
