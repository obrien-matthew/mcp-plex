"""Plex server connection and authenticated client singleton."""

import os
import sys

from plexapi.server import PlexServer

_server: PlexServer | None = None


def get_plex_server() -> PlexServer:
    """Return a cached, authenticated Plex server connection.

    Reads PLEX_SERVER_URL and PLEX_TOKEN from environment variables.

    Raises RuntimeError if required env vars are missing or connection fails.
    """
    global _server
    if _server is not None:
        return _server

    server_url = os.environ.get("PLEX_SERVER_URL")
    token = os.environ.get("PLEX_TOKEN")

    if not server_url or not token:
        raise RuntimeError(
            "PLEX_SERVER_URL and PLEX_TOKEN environment variables "
            "are required. See README.md for setup instructions."
        )

    # Strip trailing slash for consistency
    server_url = server_url.rstrip("/")

    try:
        _server = PlexServer(server_url, token)
        # Verify connection by fetching library sections
        _server.library.sections()
    except Exception as e:
        _server = None
        print(f"Plex connection failed: {e}", file=sys.stderr)
        raise RuntimeError(
            "Failed to connect to Plex server. Please check your server URL and token."
        ) from e

    return _server
