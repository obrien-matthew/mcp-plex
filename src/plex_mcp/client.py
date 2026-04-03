"""Thin wrapper over plexapi with input validation and clean error handling."""

import sys
from typing import NoReturn

from plexapi.exceptions import BadRequest, NotFound, Unauthorized

from .auth import get_plex_server
from .formatting import (
    format_collection,
    format_library,
    format_media_item,
    format_media_item_detailed,
    format_playlist,
    format_season,
)
from .validation import validate_limit, validate_rating_key


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
                items = section.recentlyAdded(maxresults=limit)
            else:
                items = self._plex.library.recentlyAdded(maxresults=limit)
            return [format_media_item(item) for item in items]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching recently added")

    def get_on_deck(self, limit: int = 10) -> list[dict]:
        limit = validate_limit(limit)
        try:
            items = self._plex.library.onDeck(maxresults=limit)
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

    def _fetch_item(self, rating_key: str, action: str) -> object:
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
            return [format_season(s) for s in show.seasons()]  # type: ignore[union-attr]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching seasons")

    def get_episodes(self, rating_key: str, season_number: int = 0) -> list[dict]:
        rating_key = validate_rating_key(rating_key)
        try:
            item = self._fetch_item(rating_key, "fetching episodes")
            if hasattr(item, "episodes"):
                # It's a show -- get all episodes or filter by season
                if season_number > 0:
                    season = item.season(season_number)  # type: ignore[union-attr]
                    episodes = season.episodes()
                else:
                    episodes = item.episodes()  # type: ignore[union-attr]
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
            return [format_media_item(item) for item in playlist.items()]  # type: ignore[union-attr]
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "fetching playlist items")

    # -- Management --

    def scan_library(self, library_name: str) -> str:
        try:
            section = self._get_library(library_name)
            section.update()
            return f"Library scan started for '{library_name}'."
        except (NotFound, BadRequest, Unauthorized) as e:
            self._handle_error(e, "scanning library")
