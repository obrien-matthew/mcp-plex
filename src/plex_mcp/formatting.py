"""Response formatters that produce clean, LLM-friendly dicts.

Only includes fields useful for an LLM -- no images, file paths, or internal IDs.
"""

from datetime import datetime
from typing import Any


def _safe_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Get an attribute safely, returning default if missing or None."""
    return getattr(obj, attr, default) or default


def _format_datetime(dt: datetime | None) -> str | None:
    """Format a datetime as an ISO string, or return None."""
    if dt is None:
        return None
    return dt.isoformat()


def _format_duration(ms: int | None) -> str | None:
    """Format milliseconds as a human-readable duration."""
    if ms is None:
        return None
    total_seconds = ms // 1000
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {seconds}s"


def format_media_item(item: Any) -> dict:
    """Format any Plex media item into an LLM-friendly dict.

    Routes to the appropriate formatter based on item type.
    """
    item_type = str(_safe_attr(item, "type", "unknown"))
    formatters = {
        "movie": _format_movie,
        "show": _format_show,
        "season": _format_season_item,
        "episode": _format_episode,
        "artist": _format_artist,
        "album": _format_album,
        "track": _format_track,
    }
    formatter = formatters.get(item_type, _format_generic)
    return formatter(item)


def format_media_item_detailed(item: Any) -> dict:
    """Format a media item with full detail (for get_media_details)."""
    result = format_media_item(item)
    # Add extended fields
    summary = _safe_attr(item, "summary")
    if summary:
        result["summary"] = str(summary)

    genres = _safe_attr(item, "genres", [])
    if genres:
        result["genres"] = [str(g.tag) for g in genres]

    roles = _safe_attr(item, "roles", [])
    if roles:
        result["cast"] = [str(r.tag) for r in roles[:10]]

    directors = _safe_attr(item, "directors", [])
    if directors:
        result["directors"] = [str(d.tag) for d in directors]

    writers = _safe_attr(item, "writers", [])
    if writers:
        result["writers"] = [str(w.tag) for w in writers]

    studio = _safe_attr(item, "studio")
    if studio:
        result["studio"] = str(studio)

    content_rating = _safe_attr(item, "contentRating")
    if content_rating:
        result["content_rating"] = str(content_rating)

    return result


def _format_movie(item: Any) -> dict:
    return {
        "type": "movie",
        "title": str(_safe_attr(item, "title", "")),
        "year": _safe_attr(item, "year"),
        "rating": _safe_attr(item, "rating"),
        "audience_rating": _safe_attr(item, "audienceRating"),
        "duration": _format_duration(_safe_attr(item, "duration")),
        "rating_key": str(_safe_attr(item, "ratingKey", "")),
        "added_at": _format_datetime(_safe_attr(item, "addedAt")),
    }


def _format_show(item: Any) -> dict:
    return {
        "type": "show",
        "title": str(_safe_attr(item, "title", "")),
        "year": _safe_attr(item, "year"),
        "rating": _safe_attr(item, "rating"),
        "audience_rating": _safe_attr(item, "audienceRating"),
        "season_count": _safe_attr(item, "childCount"),
        "episode_count": _safe_attr(item, "leafCount"),
        "rating_key": str(_safe_attr(item, "ratingKey", "")),
        "added_at": _format_datetime(_safe_attr(item, "addedAt")),
    }


def _format_season_item(item: Any) -> dict:
    return {
        "type": "season",
        "title": str(_safe_attr(item, "title", "")),
        "show_title": str(_safe_attr(item, "parentTitle", "")),
        "season_number": _safe_attr(item, "index"),
        "episode_count": _safe_attr(item, "leafCount"),
        "rating_key": str(_safe_attr(item, "ratingKey", "")),
    }


def _format_episode(item: Any) -> dict:
    return {
        "type": "episode",
        "title": str(_safe_attr(item, "title", "")),
        "show_title": str(_safe_attr(item, "grandparentTitle", "")),
        "season_number": _safe_attr(item, "parentIndex"),
        "episode_number": _safe_attr(item, "index"),
        "duration": _format_duration(_safe_attr(item, "duration")),
        "rating_key": str(_safe_attr(item, "ratingKey", "")),
    }


def _format_artist(item: Any) -> dict:
    return {
        "type": "artist",
        "title": str(_safe_attr(item, "title", "")),
        "rating_key": str(_safe_attr(item, "ratingKey", "")),
        "added_at": _format_datetime(_safe_attr(item, "addedAt")),
    }


def _format_album(item: Any) -> dict:
    return {
        "type": "album",
        "title": str(_safe_attr(item, "title", "")),
        "artist": str(_safe_attr(item, "parentTitle", "")),
        "year": _safe_attr(item, "year"),
        "track_count": _safe_attr(item, "leafCount"),
        "rating_key": str(_safe_attr(item, "ratingKey", "")),
        "added_at": _format_datetime(_safe_attr(item, "addedAt")),
    }


def _format_track(item: Any) -> dict:
    return {
        "type": "track",
        "title": str(_safe_attr(item, "title", "")),
        "artist": str(_safe_attr(item, "grandparentTitle", "")),
        "album": str(_safe_attr(item, "parentTitle", "")),
        "track_number": _safe_attr(item, "index"),
        "duration": _format_duration(_safe_attr(item, "duration")),
        "rating_key": str(_safe_attr(item, "ratingKey", "")),
    }


def _format_generic(item: Any) -> dict:
    return {
        "type": str(_safe_attr(item, "type", "unknown")),
        "title": str(_safe_attr(item, "title", "")),
        "rating_key": str(_safe_attr(item, "ratingKey", "")),
    }


def format_library(section: Any) -> dict:
    """Format a library section for listing."""
    return {
        "title": str(_safe_attr(section, "title", "")),
        "type": str(_safe_attr(section, "type", "")),
        "key": str(_safe_attr(section, "key", "")),
        "total_items": _safe_attr(section, "totalSize"),
        "updated_at": _format_datetime(_safe_attr(section, "updatedAt")),
    }


def format_season(season: Any) -> dict:
    """Format a season for listing."""
    return _format_season_item(season)


def format_playlist(playlist: Any) -> dict:
    """Format a playlist for listing."""
    return {
        "title": str(_safe_attr(playlist, "title", "")),
        "playlist_type": str(_safe_attr(playlist, "playlistType", "")),
        "item_count": _safe_attr(playlist, "leafCount"),
        "duration": _format_duration(_safe_attr(playlist, "duration")),
        "rating_key": str(_safe_attr(playlist, "ratingKey", "")),
    }


def format_collection(collection: Any) -> dict:
    """Format a collection for listing."""
    result = {
        "title": str(_safe_attr(collection, "title", "")),
        "smart": bool(_safe_attr(collection, "smart", False)),
        "item_count": _safe_attr(collection, "childCount"),
        "rating_key": str(_safe_attr(collection, "ratingKey", "")),
    }
    summary = _safe_attr(collection, "summary")
    if summary:
        result["summary"] = str(summary)
    return result


def format_collection_detailed(collection: Any) -> dict:
    """Format a collection with full detail."""
    result = format_collection(collection)
    mode_map = {
        -1: "default",
        0: "default",
        1: "hide",
        2: "hideItems",
        3: "showItems",
    }
    mode_val = _safe_attr(collection, "collectionMode")
    if mode_val is not None:
        result["mode"] = mode_map.get(mode_val, "default")
    else:
        result["mode"] = "default"
    sort_map = {0: "release", 1: "alpha", 2: "custom"}
    sort_val = _safe_attr(collection, "collectionSort")
    if sort_val is not None:
        result["sort"] = sort_map.get(sort_val, "release")
    else:
        result["sort"] = "release"
    labels = _safe_attr(collection, "labels", [])
    if labels:
        result["labels"] = [str(lab.tag) for lab in labels]
    return result
