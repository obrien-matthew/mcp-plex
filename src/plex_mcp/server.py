"""MCP server with Plex tools for media discovery, search, and library management."""

import json

from mcp.server.fastmcp import FastMCP

from .client import PlexClient, PlexError

mcp = FastMCP("mcp-plex")

_client: PlexClient | None = None


def _get_client() -> PlexClient:
    global _client
    if _client is None:
        _client = PlexClient()
    return _client


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


@mcp.tool()
def search_media(query: str, media_type: str = "", limit: int = 20) -> str:
    """Search for media across all Plex libraries.

    Searches movies, shows, music, and other media by title.

    Optional media_type filter: "movie", "show", "episode", "artist",
    "album", "track".

    Returns titles, years, ratings, and rating keys for further lookup.
    """
    try:
        results = _get_client().search_media(query, media_type, limit)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_recently_added(limit: int = 20, library_name: str = "") -> str:
    """Get recently added media from Plex.

    Returns the most recently added items across all libraries, or
    filtered to a specific library by name (e.g. "Movies", "TV Shows").
    """
    try:
        results = _get_client().get_recently_added(limit, library_name)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_on_deck(limit: int = 10) -> str:
    """Get the "On Deck" continue-watching list from Plex.

    Returns items that are partially watched or next episodes in a series.
    """
    try:
        results = _get_client().get_on_deck(limit)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Library Browsing
# ---------------------------------------------------------------------------


@mcp.tool()
def get_libraries() -> str:
    """List all library sections on the Plex server.

    Returns library names, types (movie, show, artist), item counts, and
    last updated timestamps.
    """
    try:
        results = _get_client().get_libraries()
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_library_contents(
    library_name: str, sort: str = "titleSort", limit: int = 50
) -> str:
    """Browse the contents of a specific Plex library.

    library_name must match exactly (e.g. "Movies", "TV Shows").
    Use get_libraries to see available names.

    Sort options: "titleSort" (default), "addedAt:desc", "year:desc",
    "rating:desc", "audienceRating:desc".
    """
    try:
        results = _get_client().get_library_contents(library_name, sort, limit)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_media_details(rating_key: str) -> str:
    """Get detailed information about a specific media item.

    Use the rating_key from search or browse results. Returns full
    details including summary, genres, cast, directors, and ratings.
    """
    try:
        result = _get_client().get_media_details(rating_key)
        return json.dumps(result, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_library_stats(library_name: str = "") -> str:
    """Get statistics for Plex libraries.

    Without library_name: returns item counts for all libraries.
    With library_name: returns detailed stats for that library.
    """
    try:
        result = _get_client().get_library_stats(library_name)
        return json.dumps(result, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Shows
# ---------------------------------------------------------------------------


@mcp.tool()
def get_seasons(rating_key: str) -> str:
    """Get the seasons of a TV show.

    Provide the rating_key of a show (from search or browse). Returns
    season numbers, episode counts, and rating keys.
    """
    try:
        results = _get_client().get_seasons(rating_key)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_episodes(rating_key: str, season_number: int = 0) -> str:
    """Get episodes for a TV show or season.

    Provide the rating_key of a show. Optionally filter by season_number
    (0 = all seasons). Returns episode titles, numbers, and durations.
    """
    try:
        results = _get_client().get_episodes(rating_key, season_number)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Collections & Playlists
# ---------------------------------------------------------------------------


@mcp.tool()
def get_collections(library_name: str) -> str:
    """List collections in a Plex library.

    Returns collection names, item counts, and rating keys.
    """
    try:
        results = _get_client().get_collections(library_name)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_playlists() -> str:
    """List all playlists on the Plex server.

    Returns playlist names, types, item counts, and durations.
    """
    try:
        results = _get_client().get_playlists()
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_playlist_items(rating_key: str) -> str:
    """Get the items in a Plex playlist.

    Provide the rating_key of a playlist. Returns the media items
    contained in the playlist.
    """
    try:
        results = _get_client().get_playlist_items(rating_key)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Management
# ---------------------------------------------------------------------------


@mcp.tool()
def scan_library(library_name: str) -> str:
    """Trigger a library scan on the Plex server.

    This refreshes the library to pick up new or changed media files.
    The scan runs in the background on the server.
    """
    try:
        result = _get_client().scan_library(library_name)
        return result
    except (PlexError, ValueError) as e:
        return f"Error: {e}"
