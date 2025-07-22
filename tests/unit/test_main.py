"""Unit tests for main module."""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from airtable_mcp.main import create_server, main


class TestCreateServer:
    """Test cases for create_server function."""

    @patch("airtable_mcp.main.AirtableMCPServer")
    def test_create_server_defaults(self, mock_server_class):
        """Test server creation with default values."""
        mock_server_instance = MagicMock()
        mock_server_class.return_value = mock_server_instance

        result = create_server()

        mock_server_class.assert_called_once_with(
            name="airtable-oauth-mcp", version="0.1.0"
        )
        assert result == mock_server_instance

    @patch("airtable_mcp.main.AirtableMCPServer")
    def test_create_server_with_params(self, mock_server_class):
        """Test server creation with custom parameters."""
        mock_server_instance = MagicMock()
        mock_server_class.return_value = mock_server_instance

        result = create_server(name="custom-server", version="2.0.0")

        mock_server_class.assert_called_once_with(name="custom-server", version="2.0.0")
        assert result == mock_server_instance

    @patch.dict(
        os.environ, {"MCP_SERVER_NAME": "env-server", "MCP_SERVER_VERSION": "1.5.0"}
    )
    @patch("airtable_mcp.main.AirtableMCPServer")
    def test_create_server_from_env(self, mock_server_class):
        """Test server creation with environment variables."""
        mock_server_instance = MagicMock()
        mock_server_class.return_value = mock_server_instance

        result = create_server()

        mock_server_class.assert_called_once_with(name="env-server", version="1.5.0")
        assert result == mock_server_instance

    @patch.dict(os.environ, {"MCP_SERVER_NAME": "env-server"})
    @patch("airtable_mcp.main.AirtableMCPServer")
    def test_create_server_params_override_env(self, mock_server_class):
        """Test that parameters override environment variables."""
        mock_server_instance = MagicMock()
        mock_server_class.return_value = mock_server_instance

        result = create_server(name="param-server", version="3.0.0")

        mock_server_class.assert_called_once_with(name="param-server", version="3.0.0")
        assert result == mock_server_instance


class TestMain:
    """Test cases for main function."""

    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test", "stdio"])
    def test_main_stdio_transport(self, mock_create_server):
        """Test main with STDIO transport."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        main()

        mock_create_server.assert_called_once()
        mock_server.run.assert_called_once_with(transport="stdio")

    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test", "http"])
    def test_main_http_transport_defaults(self, mock_create_server):
        """Test main with HTTP transport using default host/port."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        main()

        mock_create_server.assert_called_once()
        mock_server.run.assert_called_once_with(
            transport="http", host="0.0.0.0", port=8000
        )

    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test", "http", "localhost", "9000"])
    def test_main_http_transport_custom(self, mock_create_server):
        """Test main with HTTP transport using custom host/port."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        main()

        mock_create_server.assert_called_once()
        mock_server.run.assert_called_once_with(
            transport="http", host="localhost", port=9000
        )

    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test"])
    def test_main_default_transport(self, mock_create_server):
        """Test main with default (STDIO) transport."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        main()

        mock_create_server.assert_called_once()
        mock_server.run.assert_called_once_with(transport="stdio")

    @patch("sys.argv", ["test", "http", "localhost", "99999"])
    def test_main_invalid_port_high(self):
        """Test main with invalid port number (too high)."""
        with pytest.raises(SystemExit):
            main()

    @patch("sys.argv", ["test", "http", "localhost", "0"])
    def test_main_invalid_port_low(self):
        """Test main with invalid port number (too low)."""
        with pytest.raises(SystemExit):
            main()

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=False)
    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test", "--log-level", "DEBUG"])
    def test_main_log_level_argument(self, mock_create_server):
        """Test main with log level argument."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("logging.getLogger") as mock_get_logger:
            mock_root_logger = MagicMock()

            # Mock getLogger() to return the root logger when called without arguments
            def get_logger_side_effect(name=None):
                if name is None:
                    return mock_root_logger
                return MagicMock()

            mock_get_logger.side_effect = get_logger_side_effect

            main()

            mock_root_logger.setLevel.assert_called_with(logging.DEBUG)

    @patch.dict(os.environ, {"LOG_LEVEL": "WARNING"})
    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test", "--log-level", "ERROR"])
    def test_main_log_level_override_env(self, mock_create_server):
        """Test that log level argument overrides environment variable."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("logging.getLogger") as mock_get_logger:
            mock_root_logger = MagicMock()

            # Mock getLogger() to return the root logger when called without arguments
            def get_logger_side_effect(name=None):
                if name is None:
                    return mock_root_logger
                return MagicMock()

            mock_get_logger.side_effect = get_logger_side_effect

            main()

            mock_root_logger.setLevel.assert_called_with(logging.ERROR)

    @patch("sys.argv", ["test", "--version"])
    @patch.dict(os.environ, {"MCP_SERVER_VERSION": "2.1.0"})
    def test_main_version_argument(self):
        """Test main with --version argument."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        # argparse exits with code 0 for --version
        assert exc_info.value.code == 0

    @patch("sys.argv", ["test", "--help"])
    def test_main_help_argument(self):
        """Test main with --help argument."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        # argparse exits with code 0 for --help
        assert exc_info.value.code == 0

    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test"])
    def test_main_keyboard_interrupt(self, mock_create_server):
        """Test main handling KeyboardInterrupt."""
        mock_server = MagicMock()
        mock_server.run.side_effect = KeyboardInterrupt()
        mock_create_server.return_value = mock_server

        # Should not raise, should handle gracefully
        main()

    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test"])
    def test_main_generic_exception(self, mock_create_server):
        """Test main handling generic exception."""
        mock_server = MagicMock()
        mock_server.run.side_effect = Exception("Test error")
        mock_create_server.return_value = mock_server

        with pytest.raises(Exception, match="Test error"):
            main()

    @patch("sys.argv", ["test", "invalid"])
    def test_main_invalid_transport(self):
        """Test main with invalid transport argument."""
        with pytest.raises(SystemExit):
            main()

    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test", "http", "localhost"])
    def test_main_http_default_port(self, mock_create_server):
        """Test HTTP transport with default port."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        main()

        mock_server.run.assert_called_once_with(
            transport="http", host="localhost", port=8000
        )

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test"])
    def test_main_same_log_level_no_change(self, mock_create_server):
        """Test that log level is not changed if it's the same as environment."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("logging.getLogger") as mock_get_logger:
            mock_root_logger = MagicMock()

            # Mock getLogger() to return the root logger when called without arguments
            def get_logger_side_effect(name=None):
                if name is None:
                    return mock_root_logger
                return MagicMock()

            mock_get_logger.side_effect = get_logger_side_effect

            main()

            # Should not call setLevel since log level didn't change
            mock_root_logger.setLevel.assert_not_called()

    @patch("airtable_mcp.main.create_server")
    @patch("sys.argv", ["test"])
    def test_main_system_exit_propagates(self, mock_create_server):
        """Test that SystemExit from argparse is propagated."""
        # This would happen with --help or --version
        mock_create_server.side_effect = SystemExit(0)

        with pytest.raises(SystemExit):
            main()
