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

    Returns collection names, types (smart/regular), item counts, and
    rating keys. Use get_collection_items to see the contents.
    """
    try:
        results = _get_client().get_collections(library_name)
        return json.dumps(results, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_collection_items(rating_key: str) -> str:
    """Get the items in a Plex collection with full collection details.

    Provide the rating_key of a collection. Returns collection metadata
    (title, smart, mode, sort, labels) and the media items it contains.
    """
    try:
        result = _get_client().get_collection_items(rating_key)
        return json.dumps(result, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def create_collection(library_name: str, title: str, rating_keys: list[str]) -> str:
    """Create a new regular collection in a Plex library.

    library_name: exact library name (e.g. "Movies").
    title: name for the collection.
    rating_keys: list of rating keys for items to include.
    """
    try:
        result = _get_client().create_collection(library_name, title, rating_keys)
        return json.dumps(result, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def create_smart_collection(
    library_name: str,
    title: str,
    filters: dict,
    libtype: str = "",
    sort: str = "",
    limit: int = 0,
) -> str:
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
    try:
        result = _get_client().create_smart_collection(
            library_name, title, filters, libtype, sort, limit
        )
        return json.dumps(result, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def edit_collection(
    rating_key: str,
    title: str = "",
    summary: str | None = None,
    sort_order: str = "",
    mode: str = "",
) -> str:
    """Edit a collection's metadata.

    rating_key: the collection's rating key.
    title: new title (empty = no change).
    summary: new summary (None = no change, empty string = clear).
    sort_order: "release", "alpha", or "custom" (empty = no change).
    mode: "default", "hide", "hideItems", or "showItems" (empty = no change).
    """
    try:
        result = _get_client().edit_collection(
            rating_key, title, summary, sort_order, mode
        )
        return json.dumps(result, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def add_to_collection(rating_key: str, item_rating_keys: list[str]) -> str:
    """Add items to a regular (non-smart) collection.

    rating_key: the collection's rating key.
    item_rating_keys: list of rating keys for items to add.
    """
    try:
        result = _get_client().add_to_collection(rating_key, item_rating_keys)
        return json.dumps(result, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def remove_from_collection(rating_key: str, item_rating_keys: list[str]) -> str:
    """Remove items from a regular (non-smart) collection.

    rating_key: the collection's rating key.
    item_rating_keys: list of rating keys for items to remove.
    """
    try:
        result = _get_client().remove_from_collection(rating_key, item_rating_keys)
        return json.dumps(result, indent=2)
    except (PlexError, ValueError) as e:
        return f"Error: {e}"


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
