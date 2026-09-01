"""MCP server with Plex tools for media discovery, search, and library management.

Tool return-type conventions:
- Data tools return real `dict` or `list[dict]` so FastMCP serializes them as
  proper structured content (no json.dumps wrapping).
- Action/status tools return human-readable `str` confirmations.
- Errors are raised as exceptions; FastMCP translates them into MCP error
  responses with `isError=true`.
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import PlexClient, PlexError

mcp = FastMCP("mcp-plex")


@mcp.tool()
def get_server_version() -> str:
    """Return the installed version of the mcp-plex-server package."""
    try:
        return version("mcp-plex-server")
    except PackageNotFoundError:
        return "unknown"


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
def search_media(query: str, media_type: str = "", limit: int = 20) -> list[dict]:
    """Search for media across all Plex libraries.

    Searches movies, shows, music, and other media by title.

    Optional media_type filter: "movie", "show", "episode", "artist",
    "album", "track".

    Returns titles, years, ratings, and rating keys for further lookup.
    """
    return _get_client().search_media(query, media_type, limit)


@mcp.tool()
def get_recently_added(limit: int = 20, library_name: str = "") -> list[dict]:
    """Get recently added media from Plex.

    Returns the most recently added items across all libraries, or
    filtered to a specific library by name (e.g. "Movies", "TV Shows").
    """
    return _get_client().get_recently_added(limit, library_name)


@mcp.tool()
def get_on_deck(limit: int = 10) -> list[dict]:
    """Get the "On Deck" continue-watching list from Plex.

    Returns items that are partially watched or next episodes in a series.
    """
    return _get_client().get_on_deck(limit)


# ---------------------------------------------------------------------------
# Library Browsing
# ---------------------------------------------------------------------------


@mcp.tool()
def get_libraries() -> list[dict]:
    """List all library sections on the Plex server.

    Returns library names, types (movie, show, artist), item counts, and
    last updated timestamps.
    """
    return _get_client().get_libraries()


@mcp.tool()
def get_library_contents(
    library_name: str, sort: str = "titleSort", limit: int = 50
) -> list[dict]:
    """Browse the contents of a specific Plex library.

    library_name must match exactly (e.g. "Movies", "TV Shows").
    Use get_libraries to see available names.

    Sort options: "titleSort" (default), "addedAt:desc", "year:desc",
    "rating:desc", "audienceRating:desc".
    """
    return _get_client().get_library_contents(library_name, sort, limit)


@mcp.tool()
def get_media_details(rating_key: str) -> dict[str, Any]:
    """Get detailed information about a specific media item.

    Use the rating_key from search or browse results. Returns full
    details including summary, genres, cast, directors, and ratings.
    """
    return _get_client().get_media_details(rating_key)


@mcp.tool()
def get_library_stats(library_name: str = "") -> dict | list[dict]:
    """Get statistics for Plex libraries.

    Without library_name: returns item counts for all libraries.
    With library_name: returns detailed stats for that library.
    """
    return _get_client().get_library_stats(library_name)


# ---------------------------------------------------------------------------
# Shows
# ---------------------------------------------------------------------------


@mcp.tool()
def get_seasons(rating_key: str) -> list[dict]:
    """Get the seasons of a TV show.

    Provide the rating_key of a show (from search or browse). Returns
    season numbers, episode counts, and rating keys.
    """
    return _get_client().get_seasons(rating_key)


@mcp.tool()
def get_episodes(rating_key: str, season_number: int = 0) -> list[dict]:
    """Get episodes for a TV show or season.

    Provide the rating_key of a show. Optionally filter by season_number
    (0 = all seasons). Returns episode titles, numbers, and durations.
    """
    return _get_client().get_episodes(rating_key, season_number)


# ---------------------------------------------------------------------------
# Collections & Playlists
# ---------------------------------------------------------------------------


@mcp.tool()
def get_collections(library_name: str) -> list[dict]:
    """List collections in a Plex library.

    Returns collection names, types (smart/regular), item counts, and
    rating keys. Use get_collection_items to see the contents.
    """
    return _get_client().get_collections(library_name)


@mcp.tool()
def get_collection_items(rating_key: str) -> dict[str, Any]:
    """Get the items in a Plex collection with full collection details.

    Provide the rating_key of a collection. Returns collection metadata
    (title, smart, mode, sort, labels) and the media items it contains.
    """
    return _get_client().get_collection_items(rating_key)


@mcp.tool()
def create_collection(
    library_name: str, title: str, rating_keys: list[str]
) -> dict[str, Any]:
    """Create a new regular collection in a Plex library.

    library_name: exact library name (e.g. "Movies").
    title: name for the collection.
    rating_keys: list of rating keys for items to include.
    """
    return _get_client().create_collection(library_name, title, rating_keys)


@mcp.tool()
def create_smart_collection(
    library_name: str,
    title: str,
    filters: dict,
    libtype: str = "",
    sort: str = "",
    limit: int = 0,
) -> dict[str, Any]:
    """Create a smart (filter-based) collection that auto-updates.

    library_name: exact library name (e.g. "Movies").
    title: name for the collection.
    filters: dict of field/value pairs with optional operators.
      Operators are appended to the key:
        ">>" = greater than, "<<" = less than, "!" = not.
      Examples:
        {"genre": "Action"} -- genre is Action
        {"year>>": 2000} -- year greater than 2000
        {"genre!": "Horror"} -- genre is not Horror
        {"genre": "Action", "year>>": 2000} -- both conditions
      Common fields: genre, year, decade, rating, audienceRating,
        contentRating, resolution, studio, label, director, actor.
    libtype: content type to filter (required for show libraries).
      "movie", "show", "episode", "season", "artist", "album", "track".
    sort: sort order (e.g. "titleSort", "year:desc", "rating:desc").
    limit: max items (0 = unlimited).
    """
    return _get_client().create_smart_collection(
        library_name, title, filters, libtype, sort, limit
    )


@mcp.tool()
def edit_collection(
    rating_key: str,
    title: str = "",
    summary: str | None = None,
    sort_order: str = "",
    mode: str = "",
) -> dict[str, Any]:
    """Edit a collection's metadata.

    rating_key: the collection's rating key.
    title: new title (empty = no change).
    summary: new summary (None = no change, empty string = clear).
    sort_order: "release", "alpha", or "custom" (empty = no change).
    mode: "default", "hide", "hideItems", or "showItems" (empty = no change).
    """
    return _get_client().edit_collection(rating_key, title, summary, sort_order, mode)


@mcp.tool()
def add_to_collection(rating_key: str, item_rating_keys: list[str]) -> dict[str, Any]:
    """Add items to a regular (non-smart) collection.

    rating_key: the collection's rating key.
    item_rating_keys: list of rating keys for items to add.
    """
    return _get_client().add_to_collection(rating_key, item_rating_keys)


@mcp.tool()
def remove_from_collection(
    rating_key: str, item_rating_keys: list[str]
) -> dict[str, Any]:
    """Remove items from a regular (non-smart) collection.

    rating_key: the collection's rating key.
    item_rating_keys: list of rating keys for items to remove.
    """
    return _get_client().remove_from_collection(rating_key, item_rating_keys)


@mcp.tool()
def delete_collection(rating_key: str) -> str:
    """Delete a collection from the Plex library.

    This permanently removes the collection. The media items themselves
    are not affected.
    """
    try:
        return _get_client().delete_collection(rating_key)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Watch State
# ---------------------------------------------------------------------------


@mcp.tool()
def mark_watched(rating_key: str) -> str:
    """Mark a media item as fully watched.

    Works on movies, episodes, and tracks.
    """
    try:
        return _get_client().mark_watched(rating_key)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def mark_unwatched(rating_key: str) -> str:
    """Mark a media item as unwatched, resetting its watch progress.

    Works on movies, episodes, and tracks.
    """
    try:
        return _get_client().mark_unwatched(rating_key)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def remove_from_continue_watching(rating_key: str) -> str:
    """Remove a partially-watched item from the Continue Watching / On Deck list.

    Only works on movies and episodes. Does not change the item's
    watched/unwatched state.
    """
    try:
        return _get_client().remove_from_continue_watching(rating_key)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def set_playback_progress(rating_key: str, progress_ms: int) -> str:
    """Set the playback progress for a media item to a specific position.

    rating_key: the item's rating key.
    progress_ms: position in milliseconds (must be > 0).
      To reset progress to zero, use mark_unwatched instead.
    """
    try:
        return _get_client().set_playback_progress(rating_key, progress_ms)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_playlists() -> list[dict]:
    """List all playlists on the Plex server.

    Returns playlist names, types, item counts, and durations.
    """
    return _get_client().get_playlists()


@mcp.tool()
def get_playlist_items(rating_key: str) -> list[dict]:
    """Get the items in a Plex playlist.

    Provide the rating_key of a playlist. Returns the media items
    contained in the playlist.
    """
    return _get_client().get_playlist_items(rating_key)


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
        return _get_client().scan_library(library_name)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"
