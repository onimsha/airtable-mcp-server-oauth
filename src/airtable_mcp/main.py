"""Main entry point for the Airtable OAuth MCP Server."""

import logging
import os

from dotenv import load_dotenv

from .mcp.server import AirtableMCPServer

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Reduce noise from third-party libraries
logging.getLogger("sse_starlette.sse").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)
logging.getLogger("mcp.server.streamable_http").setLevel(logging.WARNING)

# Enable debug logging for our API client to see Airtable requests
logging.getLogger("src.airtable_mcp.api.client").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


def create_server(
    name: str | None = None,
    version: str | None = None,
) -> AirtableMCPServer:
    """Create and configure the Airtable MCP server.

    Args:
        name: Server name (defaults to env var or 'airtable-oauth-mcp')
        version: Server version (defaults to env var or '0.1.0')

    Returns:
        Configured AirtableMCPServer instance
    """
    return AirtableMCPServer(
        name=name or os.getenv("MCP_SERVER_NAME", "airtable-oauth-mcp"),
        version=version or os.getenv("MCP_SERVER_VERSION", "0.1.0"),
    )


def main() -> None:
    """Main function to run the server."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Airtable OAuth MCP Server - Model Context Protocol server with OAuth 2.0 authentication for Airtable",
        epilog="Examples:\n"
        "  %(prog)s                          # Run with STDIO transport (default)\n"
        "  %(prog)s http                     # Run with HTTP transport on 0.0.0.0:8000\n"
        "  %(prog)s http localhost 8001      # Run with HTTP transport on localhost:8001\n"
        "  %(prog)s --help                   # Show this help message",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "transport",
        nargs="?",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type: 'stdio' for JSON-RPC over stdin/stdout (default), 'http' for HTTP server",
    )

    parser.add_argument(
        "host",
        nargs="?",
        default="0.0.0.0",
        help="Host to bind to when using HTTP transport (default: 0.0.0.0)",
    )

    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=8000,
        help="Port to bind to when using HTTP transport (default: 8000)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.getenv("LOG_LEVEL", "INFO").upper(),
        help="Set logging level (default: INFO, can also be set via LOG_LEVEL env var)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {os.getenv('MCP_SERVER_VERSION', '0.1.0')}",
    )

    try:
        args = parser.parse_args()

        # Update log level if specified
        current_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if args.log_level != current_log_level:
            logging.getLogger().setLevel(getattr(logging, args.log_level))
            logger.info(f"Log level set to {args.log_level}")

        # Validate HTTP-specific arguments
        if args.transport == "http":
            if not (1 <= args.port <= 65535):
                parser.error("Port must be between 1 and 65535")

        server = create_server()

        if args.transport == "stdio":
            logger.info("Starting Airtable OAuth MCP Server with STDIO transport...")
            server.run(transport="stdio")
        else:  # http
            logger.info(
                f"Starting Airtable OAuth MCP Server with HTTP transport on {args.host}:{args.port}..."
            )
            server.run(transport="http", host=args.host, port=args.port)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except SystemExit:
        # argparse calls sys.exit() for --help, --version, or argument errors
        # Let it propagate normally
        raise
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        raise


if __name__ == "__main__":
    main()
