"""MCP server for Plex media discovery, search, and library management."""

from .server import mcp


def main():
    mcp.run(transport="stdio")


__all__ = ["main", "mcp"]
