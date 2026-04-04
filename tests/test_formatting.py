"""Tests for response formatters."""

from datetime import datetime
from types import SimpleNamespace

from plex_mcp.formatting import (
    format_collection,
    format_collection_detailed,
    format_library,
    format_media_item,
    format_media_item_detailed,
    format_playlist,
    format_season,
)


def _mock(**kwargs):
    """Create a SimpleNamespace mock with given attributes."""
    return SimpleNamespace(**kwargs)


def _mock_tag(name: str):
    """Create a mock tag object (genre, role, etc.)."""
    return _mock(tag=name)


# -- format_media_item routing --


class TestFormatMediaItemRouting:
    def test_routes_movie(self):
        item = _mock(
            type="movie",
            title="Inception",
            year=2010,
            rating=8.8,
            audienceRating=9.0,
            duration=8880000,
            ratingKey=123,
            addedAt=datetime(2024, 1, 15),
        )
        result = format_media_item(item)
        assert result["type"] == "movie"
        assert result["title"] == "Inception"
        assert result["year"] == 2010
        assert result["rating_key"] == "123"

    def test_routes_show(self):
        item = _mock(
            type="show",
            title="Breaking Bad",
            year=2008,
            rating=9.5,
            audienceRating=9.7,
            childCount=5,
            leafCount=62,
            ratingKey=456,
            addedAt=datetime(2024, 2, 1),
        )
        result = format_media_item(item)
        assert result["type"] == "show"
        assert result["season_count"] == 5
        assert result["episode_count"] == 62

    def test_routes_episode(self):
        item = _mock(
            type="episode",
            title="Pilot",
            grandparentTitle="Breaking Bad",
            parentIndex=1,
            index=1,
            duration=3480000,
            ratingKey=789,
        )
        result = format_media_item(item)
        assert result["type"] == "episode"
        assert result["show_title"] == "Breaking Bad"
        assert result["season_number"] == 1

    def test_routes_track(self):
        item = _mock(
            type="track",
            title="Bohemian Rhapsody",
            grandparentTitle="Queen",
            parentTitle="A Night at the Opera",
            index=11,
            duration=354000,
            ratingKey=101,
        )
        result = format_media_item(item)
        assert result["type"] == "track"
        assert result["artist"] == "Queen"
        assert result["album"] == "A Night at the Opera"

    def test_unknown_type_uses_generic(self):
        item = _mock(type="photo", title="Sunset", ratingKey=999)
        result = format_media_item(item)
        assert result["type"] == "photo"
        assert result["title"] == "Sunset"
        assert result["rating_key"] == "999"

    def test_missing_attributes_use_defaults(self):
        item = _mock(type="movie", title="Bare Minimum", ratingKey=1)
        result = format_media_item(item)
        assert result["title"] == "Bare Minimum"
        assert result["year"] is None
        assert result["rating"] is None


# -- format_media_item_detailed --


class TestFormatMediaItemDetailed:
    def test_includes_extended_fields(self):
        item = _mock(
            type="movie",
            title="Inception",
            year=2010,
            rating=8.8,
            audienceRating=9.0,
            duration=8880000,
            ratingKey=123,
            addedAt=datetime(2024, 1, 15),
            summary="A mind-bending thriller.",
            genres=[_mock_tag("Sci-Fi"), _mock_tag("Action")],
            roles=[_mock_tag("Leonardo DiCaprio"), _mock_tag("Tom Hardy")],
            directors=[_mock_tag("Christopher Nolan")],
            writers=[_mock_tag("Christopher Nolan")],
            studio="Warner Bros.",
            contentRating="PG-13",
        )
        result = format_media_item_detailed(item)
        assert result["summary"] == "A mind-bending thriller."
        assert result["genres"] == ["Sci-Fi", "Action"]
        assert "Leonardo DiCaprio" in result["cast"]
        assert result["directors"] == ["Christopher Nolan"]
        assert result["studio"] == "Warner Bros."
        assert result["content_rating"] == "PG-13"

    def test_omits_empty_extended_fields(self):
        item = _mock(
            type="movie",
            title="Bare",
            year=None,
            rating=None,
            audienceRating=None,
            duration=None,
            ratingKey=1,
            addedAt=None,
        )
        result = format_media_item_detailed(item)
        assert "summary" not in result
        assert "genres" not in result
        assert "cast" not in result


# -- Duration formatting --


class TestDurationFormatting:
    def test_movie_duration_hours(self):
        item = _mock(
            type="movie",
            title="Long",
            year=None,
            rating=None,
            audienceRating=None,
            duration=9000000,  # 2h 30m
            ratingKey=1,
            addedAt=None,
        )
        result = format_media_item(item)
        assert result["duration"] == "2h 30m"

    def test_episode_duration_minutes(self):
        item = _mock(
            type="episode",
            title="Short",
            grandparentTitle="Show",
            parentIndex=1,
            index=1,
            duration=1800000,  # 30m 0s
            ratingKey=1,
        )
        result = format_media_item(item)
        assert result["duration"] == "30m 0s"

    def test_none_duration(self):
        item = _mock(
            type="movie",
            title="NoDur",
            year=None,
            rating=None,
            audienceRating=None,
            duration=None,
            ratingKey=1,
            addedAt=None,
        )
        result = format_media_item(item)
        assert result["duration"] is None


# -- format_library --


class TestFormatLibrary:
    def test_formats_library(self):
        section = _mock(
            title="Movies",
            type="movie",
            key="1",
            totalSize=500,
            updatedAt=datetime(2024, 6, 15, 12, 0),
        )
        result = format_library(section)
        assert result["title"] == "Movies"
        assert result["type"] == "movie"
        assert result["total_items"] == 500
        assert result["updated_at"] is not None


# -- format_season --


class TestFormatSeason:
    def test_formats_season(self):
        s = _mock(
            type="season",
            title="Season 1",
            parentTitle="Breaking Bad",
            index=1,
            leafCount=7,
            ratingKey=10,
        )
        result = format_season(s)
        assert result["type"] == "season"
        assert result["season_number"] == 1
        assert result["episode_count"] == 7


# -- format_playlist --


class TestFormatPlaylist:
    def test_formats_playlist(self):
        p = _mock(
            title="My Playlist",
            playlistType="video",
            leafCount=10,
            duration=7200000,
            ratingKey=50,
        )
        result = format_playlist(p)
        assert result["title"] == "My Playlist"
        assert result["playlist_type"] == "video"
        assert result["item_count"] == 10
        assert result["duration"] == "2h 0m"


# -- format_collection --


class TestFormatCollection:
    def test_regular_collection(self):
        c = _mock(
            title="Marvel",
            smart=False,
            childCount=23,
            ratingKey=100,
        )
        result = format_collection(c)
        assert result["title"] == "Marvel"
        assert result["smart"] is False
        assert result["item_count"] == 23
        assert "summary" not in result

    def test_smart_collection_with_summary(self):
        c = _mock(
            title="Best of 2024",
            smart=True,
            childCount=50,
            ratingKey=200,
            summary="Top rated movies from 2024",
        )
        result = format_collection(c)
        assert result["smart"] is True
        assert result["summary"] == "Top rated movies from 2024"


class TestFormatCollectionDetailed:
    def test_includes_mode_sort_labels(self):
        c = _mock(
            title="Marvel",
            smart=False,
            childCount=23,
            ratingKey=100,
            collectionMode=2,
            collectionSort=1,
            labels=[_mock_tag("featured"), _mock_tag("curated")],
        )
        result = format_collection_detailed(c)
        assert result["mode"] == "hideItems"
        assert result["sort"] == "alpha"
        assert result["labels"] == ["featured", "curated"]

    def test_defaults_when_missing(self):
        c = _mock(
            title="Bare",
            smart=False,
            childCount=0,
            ratingKey=1,
            collectionMode=None,
            collectionSort=None,
        )
        result = format_collection_detailed(c)
        assert result["mode"] == "default"
        assert result["sort"] == "release"
        assert "labels" not in result
