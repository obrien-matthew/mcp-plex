"""Thin wrapper over plexapi with input validation and clean error handling."""

import sys
from typing import Any, NoReturn

from plexapi.exceptions import BadRequest, NotFound, Unauthorized

from .auth import get_plex_server
from .formatting import (
    format_collection,
    format_collection_detailed,
    format_library,
    format_media_item,
    format_media_item_detailed,
    format_playlist,
    format_season,
)
from .validation import validate_limit, validate_rating_key, validate_rating_keys


class PlexError(Exception):
    """User-facing Plex API error."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class PlexClient:
    """Validated, formatted interface to the Plex API."""

    def __init__(self) -> None:
        self._plex = get_plex_server()

    def _handle_error(self, e: Exception, action: str) -> NoReturn:
        msg = f"Plex API error while {action}"
        status_code: int | None = None
        if isinstance(e, NotFound):
            msg = f"Not found while {action}"
            status_code = 404
        elif isinstance(e, Unauthorized):
            msg = f"Unauthorized while {action}"
            status_code = 401
        elif isinstance(e, BadRequest):
            msg = f"Bad request while {action}"
            status_code = 400
        print(f"{msg}: {e}", file=sys.stderr)
        raise PlexError(msg, status_code) from e

    def _get_library(self, library_name: str):
        """Get a library section by name."""
        try:
            return self._plex.library.section(library_name)
        except NotFound as e:
            available = [s.title for s in self._plex.library.sections()]
            raise PlexError(
                f"Library '{library_name}' not found. "
                f"Available libraries: {', '.join(available)}"
            ) from e

    # -- Discovery --

    def search_media(
        self, query: str, media_type: str = "", limit: int = 20
    ) -> list[dict]:
        limit = validate_limit(limit)
        try:
            if media_type:
                results = self._plex.search(query, mediatype=media_type, limit=limit)
            else:
                results = self._plex.search(query, limit=limit)
            return [format_media_item(item) for item in results[:limit]]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "searching media")

    def get_recently_added(self, limit: int = 20, library_name: str = "") -> list[dict]:
        limit = validate_limit(limit)
        try:
            if library_name:
                section = self._get_library(library_name)
                items = section.recentlyAdded()[:limit]
            else:
                items = self._plex.library.recentlyAdded()[:limit]
            return [format_media_item(item) for item in items]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching recently added")

    def get_on_deck(self, limit: int = 10) -> list[dict]:
        limit = validate_limit(limit)
        try:
            items = self._plex.library.onDeck()[:limit]
            return [format_media_item(item) for item in items]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching on deck")

    # -- Library Browsing --

    def get_libraries(self) -> list[dict]:
        try:
            sections = self._plex.library.sections()
            return [format_library(s) for s in sections]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching libraries")

    def get_library_contents(
        self, library_name: str, sort: str = "titleSort", limit: int = 50
    ) -> list[dict]:
        limit = validate_limit(limit, max_val=100)
        try:
            section = self._get_library(library_name)
            items = section.all(sort=sort)[:limit]
            return [format_media_item(item) for item in items]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching library contents")

    def get_media_details(self, rating_key: str) -> dict:
        rating_key = validate_rating_key(rating_key)
        try:
            item = self._fetch_item(rating_key, "fetching media details")
            return format_media_item_detailed(item)
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching media details")

    def get_library_stats(self, library_name: str = "") -> dict | list[dict]:
        try:
            if library_name:
                section = self._get_library(library_name)
                return {
                    "title": section.title,
                    "type": section.type,
                    "total_items": section.totalSize,
                    "total_viewable": section.totalViewSize(),
                }
            sections = self._plex.library.sections()
            return [
                {
                    "title": s.title,
                    "type": s.type,
                    "total_items": s.totalSize,
                }
                for s in sections
            ]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching library stats")

    # -- Shows --

    def _fetch_item(self, rating_key: str, action: str) -> Any:
        """Fetch an item by rating key, raising PlexError if not found."""
        item = self._plex.fetchItem(int(rating_key))
        if item is None:
            raise PlexError(f"Item {rating_key} not found")
        return item

    def get_seasons(self, rating_key: str) -> list[dict]:
        rating_key = validate_rating_key(rating_key)
        try:
            show = self._fetch_item(rating_key, "fetching seasons")
            if not hasattr(show, "seasons"):
                raise PlexError(
                    f"Item {rating_key} is not a TV show"
                    f" (type: {getattr(show, 'type', 'unknown')})"
                )
            return [format_season(s) for s in show.seasons()]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching seasons")

    def get_episodes(self, rating_key: str, season_number: int = 0) -> list[dict]:
        rating_key = validate_rating_key(rating_key)
        try:
            item = self._fetch_item(rating_key, "fetching episodes")
            if hasattr(item, "episodes"):
                # It's a show -- get all episodes or filter by season
                if season_number > 0:
                    season = item.season(season_number)
                    episodes = season.episodes()
                else:
                    episodes = item.episodes()
            else:
                raise PlexError(
                    f"Item {rating_key} is not a show or season"
                    f" (type: {getattr(item, 'type', 'unknown')})"
                )
            return [format_media_item(ep) for ep in episodes]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching episodes")

    # -- Collections & Playlists --

    def get_collections(self, library_name: str) -> list[dict]:
        try:
            section = self._get_library(library_name)
            collections = section.collections()
            return [format_collection(c) for c in collections]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching collections")

    def get_collection_items(self, rating_key: str) -> dict:
        rating_key = validate_rating_key(rating_key)
        try:
            collection = self._fetch_item(rating_key, "fetching collection items")
            if getattr(collection, "type", None) != "collection":
                raise PlexError(
                    f"Item {rating_key} is not a collection"
                    f" (type: {getattr(collection, 'type', 'unknown')})"
                )
            detail = format_collection_detailed(collection)
            detail["items"] = [format_media_item(item) for item in collection.items()]
            return detail
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching collection items")

    def create_collection(
        self, library_name: str, title: str, rating_keys: list[str]
    ) -> dict:
        rating_keys = validate_rating_keys(rating_keys)
        try:
            section = self._get_library(library_name)
            items = [self._plex.fetchItem(int(rk)) for rk in rating_keys]
            collection = section.createCollection(title=title, items=items)
            return format_collection_detailed(collection)
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "creating collection")

    def create_smart_collection(
        self,
        library_name: str,
        title: str,
        filters: dict,
        libtype: str = "",
        sort: str = "",
        limit: int = 0,
    ) -> dict:
        try:
            section = self._get_library(library_name)
            kwargs: dict = {"title": title, "smart": True, "filters": filters}
            if libtype:
                kwargs["libtype"] = libtype
            if sort:
                kwargs["sort"] = sort
            if limit > 0:
                kwargs["limit"] = limit
            collection = section.createCollection(**kwargs)
            return format_collection_detailed(collection)
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "creating smart collection")

    def edit_collection(
        self,
        rating_key: str,
        title: str = "",
        summary: str | None = None,
        sort_order: str = "",
        mode: str = "",
    ) -> dict:
        rating_key = validate_rating_key(rating_key)
        try:
            collection = self._fetch_item(rating_key, "editing collection")
            if getattr(collection, "type", None) != "collection":
                raise PlexError(f"Item {rating_key} is not a collection")
            if title:
                collection.editTitle(title)
            if summary is not None:
                collection.editSummary(summary)
            if sort_order:
                collection.sortUpdate(sort_order)
            if mode:
                collection.modeUpdate(mode)
            collection.reload()
            return format_collection_detailed(collection)
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "editing collection")

    def add_to_collection(self, rating_key: str, item_rating_keys: list[str]) -> dict:
        rating_key = validate_rating_key(rating_key)
        item_rating_keys = validate_rating_keys(item_rating_keys)
        try:
            collection = self._fetch_item(rating_key, "adding to collection")
            if getattr(collection, "type", None) != "collection":
                raise PlexError(f"Item {rating_key} is not a collection")
            if getattr(collection, "smart", False):
                raise PlexError("Cannot manually add items to a smart collection")
            items = [self._plex.fetchItem(int(rk)) for rk in item_rating_keys]
            collection.addItems(items)
            collection.reload()
            return format_collection_detailed(collection)
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "adding to collection")

    def remove_from_collection(
        self, rating_key: str, item_rating_keys: list[str]
    ) -> dict:
        rating_key = validate_rating_key(rating_key)
        item_rating_keys = validate_rating_keys(item_rating_keys)
        try:
            collection = self._fetch_item(rating_key, "removing from collection")
            if getattr(collection, "type", None) != "collection":
                raise PlexError(f"Item {rating_key} is not a collection")
            if getattr(collection, "smart", False):
                raise PlexError("Cannot manually remove items from a smart collection")
            items = [self._plex.fetchItem(int(rk)) for rk in item_rating_keys]
            collection.removeItems(items)
            collection.reload()
            return format_collection_detailed(collection)
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "removing from collection")

    def delete_collection(self, rating_key: str) -> str:
        rating_key = validate_rating_key(rating_key)
        try:
            collection = self._fetch_item(rating_key, "deleting collection")
            if getattr(collection, "type", None) != "collection":
                raise PlexError(f"Item {rating_key} is not a collection")
            title = getattr(collection, "title", rating_key)
            collection.delete()
            return f"Collection '{title}' deleted."
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "deleting collection")

    def get_playlists(self) -> list[dict]:
        try:
            playlists = self._plex.playlists()
            return [format_playlist(p) for p in playlists]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching playlists")

    def get_playlist_items(self, rating_key: str) -> list[dict]:
        rating_key = validate_rating_key(rating_key)
        try:
            playlist = self._fetch_item(rating_key, "fetching playlist items")
            if not hasattr(playlist, "items"):
                raise PlexError(
                    f"Item {rating_key} is not a playlist"
                    f" (type: {getattr(playlist, 'type', 'unknown')})"
                )
            return [format_media_item(item) for item in playlist.items()]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching playlist items")

    # -- Watch State --

    def mark_watched(self, rating_key: str) -> str:
        rating_key = validate_rating_key(rating_key)
        try:
            item = self._fetch_item(rating_key, "marking watched")
            if not hasattr(item, "markWatched"):
                raise PlexError(
                    f"Item {rating_key} does not support watch state"
                    f" (type: {getattr(item, 'type', 'unknown')})"
                )
            item.markWatched()
            return f"Marked '{getattr(item, 'title', rating_key)}' as watched."
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "marking watched")

    def mark_unwatched(self, rating_key: str) -> str:
        rating_key = validate_rating_key(rating_key)
        try:
            item = self._fetch_item(rating_key, "marking unwatched")
            if not hasattr(item, "markUnwatched"):
                raise PlexError(
                    f"Item {rating_key} does not support watch state"
                    f" (type: {getattr(item, 'type', 'unknown')})"
                )
            item.markUnwatched()
            return f"Marked '{getattr(item, 'title', rating_key)}' as unwatched."
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "marking unwatched")

    def remove_from_continue_watching(self, rating_key: str) -> str:
        rating_key = validate_rating_key(rating_key)
        try:
            item = self._fetch_item(rating_key, "removing from continue watching")
            if not hasattr(item, "removeFromContinueWatching"):
                raise PlexError(
                    f"Item {rating_key} does not support continue watching removal"
                    f" (type: {getattr(item, 'type', 'unknown')})"
                )
            item.removeFromContinueWatching()
            title = getattr(item, "title", rating_key)
            return f"Removed '{title}' from continue watching."
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "removing from continue watching")

    def set_playback_progress(self, rating_key: str, progress_ms: int) -> str:
        rating_key = validate_rating_key(rating_key)
        if progress_ms <= 0:
            raise ValueError(
                "progress_ms must be > 0. Use mark_unwatched to reset progress."
            )
        try:
            item = self._fetch_item(rating_key, "setting playback progress")
            if not hasattr(item, "updateProgress"):
                raise PlexError(
                    f"Item {rating_key} does not support playback progress"
                    f" (type: {getattr(item, 'type', 'unknown')})"
                )
            item.updateProgress(progress_ms, state="stopped")
            return (
                f"Set playback progress for '{getattr(item, 'title', rating_key)}'"
                f" to {progress_ms}ms."
            )
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "setting playback progress")

    # -- Management --

    def scan_library(self, library_name: str) -> str:
        try:
            section = self._get_library(library_name)
            section.update()
            return f"Library scan started for '{library_name}'."
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "scanning library")
