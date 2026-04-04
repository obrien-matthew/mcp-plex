"""Tests for PlexClient -- all plexapi calls are mocked."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from plexapi.exceptions import BadRequest, NotFound, Unauthorized

from plex_mcp.client import PlexClient, PlexError


def _mock(**kwargs):
    return SimpleNamespace(**kwargs)


def _make_client():
    """Create a PlexClient with a mocked PlexServer."""
    with patch("plex_mcp.client.get_plex_server") as mock_get:
        mock_server = MagicMock()
        mock_get.return_value = mock_server
        client = PlexClient()
    return client, mock_server


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestHandleError:
    def test_not_found_raises_with_404(self):
        client, _ = _make_client()
        with pytest.raises(PlexError) as exc_info:
            client._handle_error(NotFound("gone"), "testing")
        assert exc_info.value.status_code == 404
        assert "Not found" in exc_info.value.message

    def test_unauthorized_raises_with_401(self):
        client, _ = _make_client()
        with pytest.raises(PlexError) as exc_info:
            client._handle_error(Unauthorized("nope"), "testing")
        assert exc_info.value.status_code == 401

    def test_bad_request_raises_with_400(self):
        client, _ = _make_client()
        with pytest.raises(PlexError) as exc_info:
            client._handle_error(BadRequest("bad"), "testing")
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# Library lookup
# ---------------------------------------------------------------------------


class TestGetLibrary:
    def test_returns_section(self):
        client, server = _make_client()
        section = MagicMock()
        server.library.section.return_value = section
        assert client._get_library("Movies") is section

    def test_not_found_lists_available(self):
        client, server = _make_client()
        server.library.section.side_effect = NotFound("nope")
        s1 = _mock(title="Movies")
        s2 = _mock(title="TV Shows")
        server.library.sections.return_value = [s1, s2]
        with pytest.raises(PlexError, match="Movies, TV Shows"):
            client._get_library("Nonexistent")


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


class TestSearchMedia:
    def test_returns_formatted_results(self):
        client, server = _make_client()
        item = _mock(
            type="movie",
            title="Inception",
            year=2010,
            rating=8.8,
            audienceRating=9.0,
            duration=8880000,
            ratingKey=123,
            addedAt=None,
        )
        server.search.return_value = [item]
        results = client.search_media("inception")
        assert len(results) == 1
        assert results[0]["title"] == "Inception"

    def test_with_media_type(self):
        client, server = _make_client()
        server.search.return_value = []
        client.search_media("test", media_type="movie")
        server.search.assert_called_once_with("test", mediatype="movie", limit=20)

    def test_api_error_raises_plex_error(self):
        client, server = _make_client()
        server.search.side_effect = NotFound("nope")
        with pytest.raises(PlexError):
            client.search_media("test")


class TestGetOnDeck:
    def test_returns_items(self):
        client, server = _make_client()
        item = _mock(
            type="movie",
            title="Half Watched",
            year=2024,
            rating=7.0,
            audienceRating=7.5,
            duration=7200000,
            ratingKey=55,
            addedAt=None,
        )
        server.library.onDeck.return_value = [item]
        results = client.get_on_deck()
        assert len(results) == 1
        assert results[0]["title"] == "Half Watched"


class TestGetRecentlyAdded:
    def test_global(self):
        client, server = _make_client()
        item = _mock(
            type="movie",
            title="New",
            year=2024,
            rating=None,
            audienceRating=None,
            duration=None,
            ratingKey=1,
            addedAt=None,
        )
        server.library.recentlyAdded.return_value = [item]
        results = client.get_recently_added()
        assert len(results) == 1

    def test_filtered_by_library(self):
        client, server = _make_client()
        section = MagicMock()
        server.library.section.return_value = section
        item = _mock(
            type="movie",
            title="New",
            year=2024,
            rating=None,
            audienceRating=None,
            duration=None,
            ratingKey=1,
            addedAt=None,
        )
        section.recentlyAdded.return_value = [item]
        results = client.get_recently_added(library_name="Movies")
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Library browsing
# ---------------------------------------------------------------------------


class TestGetLibraries:
    def test_returns_formatted(self):
        client, server = _make_client()
        section = _mock(
            title="Movies",
            type="movie",
            key="1",
            totalSize=500,
            updatedAt=None,
        )
        server.library.sections.return_value = [section]
        results = client.get_libraries()
        assert results[0]["title"] == "Movies"


class TestGetMediaDetails:
    def test_returns_detailed(self):
        client, server = _make_client()
        item = _mock(
            type="movie",
            title="Inception",
            year=2010,
            rating=8.8,
            audienceRating=9.0,
            duration=8880000,
            ratingKey=123,
            addedAt=None,
            summary="Dreams within dreams.",
            genres=[],
            roles=[],
            directors=[],
            writers=[],
        )
        server.fetchItem.return_value = item
        result = client.get_media_details("123")
        assert result["title"] == "Inception"
        assert result["summary"] == "Dreams within dreams."

    def test_invalid_rating_key(self):
        client, _ = _make_client()
        with pytest.raises(ValueError):
            client.get_media_details("abc")


# ---------------------------------------------------------------------------
# Shows
# ---------------------------------------------------------------------------


class TestGetSeasons:
    def test_returns_seasons(self):
        client, server = _make_client()
        season = _mock(
            type="season",
            title="Season 1",
            parentTitle="Show",
            index=1,
            leafCount=10,
            ratingKey=20,
        )
        show = MagicMock()
        show.seasons.return_value = [season]
        server.fetchItem.return_value = show
        results = client.get_seasons("100")
        assert len(results) == 1
        assert results[0]["season_number"] == 1

    def test_non_show_raises(self):
        client, server = _make_client()
        movie = _mock(type="movie", title="Not a show")
        server.fetchItem.return_value = movie
        with pytest.raises(PlexError, match="not a TV show"):
            client.get_seasons("100")


class TestGetEpisodes:
    def test_all_episodes(self):
        client, server = _make_client()
        ep = _mock(
            type="episode",
            title="Pilot",
            grandparentTitle="Show",
            parentIndex=1,
            index=1,
            duration=2700000,
            ratingKey=30,
        )
        show = MagicMock()
        show.episodes.return_value = [ep]
        server.fetchItem.return_value = show
        results = client.get_episodes("100")
        assert results[0]["title"] == "Pilot"

    def test_by_season_number(self):
        client, server = _make_client()
        ep = _mock(
            type="episode",
            title="Ep1",
            grandparentTitle="Show",
            parentIndex=2,
            index=1,
            duration=2700000,
            ratingKey=31,
        )
        season = MagicMock()
        season.episodes.return_value = [ep]
        show = MagicMock()
        show.season.return_value = season
        server.fetchItem.return_value = show
        results = client.get_episodes("100", season_number=2)
        show.season.assert_called_once_with(2)
        assert results[0]["season_number"] == 2


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


class TestGetCollections:
    def test_returns_formatted(self):
        client, server = _make_client()
        section = MagicMock()
        server.library.section.return_value = section
        col = _mock(
            title="Marvel",
            smart=False,
            childCount=23,
            ratingKey=100,
        )
        section.collections.return_value = [col]
        results = client.get_collections("Movies")
        assert results[0]["title"] == "Marvel"
        assert results[0]["smart"] is False


class TestGetCollectionItems:
    def test_returns_detail_with_items(self):
        client, server = _make_client()
        movie = _mock(
            type="movie",
            title="Iron Man",
            year=2008,
            rating=7.9,
            audienceRating=8.0,
            duration=7560000,
            ratingKey=50,
            addedAt=None,
        )
        col = MagicMock()
        col.type = "collection"
        col.title = "Marvel"
        col.smart = False
        col.childCount = 1
        col.ratingKey = 100
        col.collectionMode = 0
        col.collectionSort = 0
        col.items.return_value = [movie]
        server.fetchItem.return_value = col
        result = client.get_collection_items("100")
        assert result["title"] == "Marvel"
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Iron Man"

    def test_non_collection_raises(self):
        client, server = _make_client()
        movie = _mock(type="movie", title="Not a collection")
        server.fetchItem.return_value = movie
        with pytest.raises(PlexError, match="not a collection"):
            client.get_collection_items("50")


class TestCreateCollection:
    def test_creates_and_returns_detail(self):
        client, server = _make_client()
        section = MagicMock()
        server.library.section.return_value = section
        item = _mock(type="movie", title="Item", ratingKey=1)
        server.fetchItem.return_value = item
        col = _mock(
            title="New Collection",
            smart=False,
            childCount=1,
            ratingKey=200,
            collectionMode=0,
            collectionSort=0,
        )
        section.createCollection.return_value = col
        result = client.create_collection("Movies", "New Collection", ["1"])
        assert result["title"] == "New Collection"
        section.createCollection.assert_called_once()

    def test_empty_rating_keys_raises(self):
        client, _ = _make_client()
        with pytest.raises(ValueError, match="At least one"):
            client.create_collection("Movies", "Empty", [])


class TestCreateSmartCollection:
    def test_creates_with_filters(self):
        client, server = _make_client()
        section = MagicMock()
        server.library.section.return_value = section
        col = _mock(
            title="Action 2024",
            smart=True,
            childCount=10,
            ratingKey=300,
            collectionMode=0,
            collectionSort=0,
        )
        section.createCollection.return_value = col
        result = client.create_smart_collection(
            "Movies", "Action 2024", {"genre": "Action", "year>>": 2023}
        )
        assert result["smart"] is True
        kwargs = section.createCollection.call_args[1]
        assert kwargs["smart"] is True
        assert kwargs["filters"] == {"genre": "Action", "year>>": 2023}

    def test_optional_params_omitted(self):
        client, server = _make_client()
        section = MagicMock()
        server.library.section.return_value = section
        col = _mock(
            title="Test",
            smart=True,
            childCount=0,
            ratingKey=301,
            collectionMode=0,
            collectionSort=0,
        )
        section.createCollection.return_value = col
        client.create_smart_collection("Movies", "Test", {"genre": "Drama"})
        kwargs = section.createCollection.call_args[1]
        assert "libtype" not in kwargs
        assert "sort" not in kwargs
        assert "limit" not in kwargs

    def test_optional_params_included(self):
        client, server = _make_client()
        section = MagicMock()
        server.library.section.return_value = section
        col = _mock(
            title="Test",
            smart=True,
            childCount=0,
            ratingKey=301,
            collectionMode=0,
            collectionSort=0,
        )
        section.createCollection.return_value = col
        client.create_smart_collection(
            "TV Shows",
            "Recent Episodes",
            {"year>>": 2023},
            libtype="episode",
            sort="year:desc",
            limit=50,
        )
        kwargs = section.createCollection.call_args[1]
        assert kwargs["libtype"] == "episode"
        assert kwargs["sort"] == "year:desc"
        assert kwargs["limit"] == 50


class TestEditCollection:
    def test_applies_all_edits(self):
        client, server = _make_client()
        col = MagicMock()
        col.type = "collection"
        col.title = "Updated"
        col.smart = False
        col.childCount = 5
        col.ratingKey = 100
        col.collectionMode = 0
        col.collectionSort = 1
        server.fetchItem.return_value = col
        client.edit_collection(
            "100",
            title="Updated",
            summary="New desc",
            sort_order="alpha",
            mode="hide",
        )
        col.editTitle.assert_called_once_with("Updated")
        col.editSummary.assert_called_once_with("New desc")
        col.sortUpdate.assert_called_once_with("alpha")
        col.modeUpdate.assert_called_once_with("hide")
        col.reload.assert_called_once()

    def test_skips_unset_fields(self):
        client, server = _make_client()
        col = MagicMock()
        col.type = "collection"
        col.title = "Unchanged"
        col.smart = False
        col.childCount = 5
        col.ratingKey = 100
        col.collectionMode = 0
        col.collectionSort = 0
        server.fetchItem.return_value = col
        client.edit_collection("100")
        col.editTitle.assert_not_called()
        col.editSummary.assert_not_called()
        col.sortUpdate.assert_not_called()
        col.modeUpdate.assert_not_called()

    def test_clear_summary_with_empty_string(self):
        client, server = _make_client()
        col = MagicMock()
        col.type = "collection"
        col.title = "Test"
        col.smart = False
        col.childCount = 0
        col.ratingKey = 100
        col.collectionMode = 0
        col.collectionSort = 0
        server.fetchItem.return_value = col
        client.edit_collection("100", summary="")
        col.editSummary.assert_called_once_with("")


class TestAddToCollection:
    def test_adds_items(self):
        client, server = _make_client()
        col = MagicMock()
        col.type = "collection"
        col.smart = False
        col.title = "Marvel"
        col.childCount = 24
        col.ratingKey = 100
        col.collectionMode = 0
        col.collectionSort = 0
        item = _mock(type="movie")
        server.fetchItem.side_effect = [col, item]
        client.add_to_collection("100", ["50"])
        col.addItems.assert_called_once()
        col.reload.assert_called_once()

    def test_smart_collection_raises(self):
        client, server = _make_client()
        col = MagicMock()
        col.type = "collection"
        col.smart = True
        server.fetchItem.return_value = col
        with pytest.raises(PlexError, match="smart collection"):
            client.add_to_collection("100", ["50"])


class TestRemoveFromCollection:
    def test_removes_items(self):
        client, server = _make_client()
        col = MagicMock()
        col.type = "collection"
        col.smart = False
        col.title = "Marvel"
        col.childCount = 22
        col.ratingKey = 100
        col.collectionMode = 0
        col.collectionSort = 0
        item = _mock(type="movie")
        server.fetchItem.side_effect = [col, item]
        client.remove_from_collection("100", ["50"])
        col.removeItems.assert_called_once()

    def test_smart_collection_raises(self):
        client, server = _make_client()
        col = MagicMock()
        col.type = "collection"
        col.smart = True
        server.fetchItem.return_value = col
        with pytest.raises(PlexError, match="smart collection"):
            client.remove_from_collection("100", ["50"])


class TestDeleteCollection:
    def test_deletes_and_confirms(self):
        client, server = _make_client()
        col = MagicMock()
        col.type = "collection"
        col.title = "Old Collection"
        server.fetchItem.return_value = col
        result = client.delete_collection("100")
        col.delete.assert_called_once()
        assert "Old Collection" in result
        assert "deleted" in result

    def test_non_collection_raises(self):
        client, server = _make_client()
        movie = _mock(type="movie", title="Not a collection")
        server.fetchItem.return_value = movie
        with pytest.raises(PlexError, match="not a collection"):
            client.delete_collection("50")


# ---------------------------------------------------------------------------
# Watch State
# ---------------------------------------------------------------------------


class TestMarkWatched:
    def test_marks_and_confirms(self):
        client, server = _make_client()
        item = MagicMock()
        item.title = "Inception"
        item.type = "movie"
        server.fetchItem.return_value = item
        result = client.mark_watched("123")
        item.markWatched.assert_called_once()
        assert "Inception" in result
        assert "watched" in result

    def test_unsupported_type_raises(self):
        client, server = _make_client()
        item = _mock(type="collection", title="Col")
        server.fetchItem.return_value = item
        with pytest.raises(PlexError, match="does not support watch state"):
            client.mark_watched("100")


class TestMarkUnwatched:
    def test_marks_and_confirms(self):
        client, server = _make_client()
        item = MagicMock()
        item.title = "Inception"
        item.type = "movie"
        server.fetchItem.return_value = item
        result = client.mark_unwatched("123")
        item.markUnwatched.assert_called_once()
        assert "unwatched" in result


class TestRemoveFromContinueWatching:
    def test_removes_and_confirms(self):
        client, server = _make_client()
        item = MagicMock()
        item.title = "Half Watched Movie"
        item.type = "movie"
        server.fetchItem.return_value = item
        result = client.remove_from_continue_watching("55")
        item.removeFromContinueWatching.assert_called_once()
        assert "Half Watched Movie" in result

    def test_unsupported_type_raises(self):
        client, server = _make_client()
        item = _mock(type="artist", title="Band")
        server.fetchItem.return_value = item
        with pytest.raises(PlexError, match="does not support"):
            client.remove_from_continue_watching("60")


class TestSetPlaybackProgress:
    def test_sets_progress(self):
        client, server = _make_client()
        item = MagicMock()
        item.title = "Movie"
        item.type = "movie"
        server.fetchItem.return_value = item
        result = client.set_playback_progress("123", 60000)
        item.updateProgress.assert_called_once_with(60000, state="stopped")
        assert "60000ms" in result

    def test_zero_progress_raises(self):
        client, _ = _make_client()
        with pytest.raises(ValueError, match="must be > 0"):
            client.set_playback_progress("123", 0)

    def test_negative_progress_raises(self):
        client, _ = _make_client()
        with pytest.raises(ValueError, match="must be > 0"):
            client.set_playback_progress("123", -100)


# ---------------------------------------------------------------------------
# Playlists
# ---------------------------------------------------------------------------


class TestGetPlaylists:
    def test_returns_formatted(self):
        client, server = _make_client()
        pl = _mock(
            title="My Playlist",
            playlistType="video",
            leafCount=10,
            duration=7200000,
            ratingKey=50,
        )
        server.playlists.return_value = [pl]
        results = client.get_playlists()
        assert results[0]["title"] == "My Playlist"


class TestGetPlaylistItems:
    def test_returns_items(self):
        client, server = _make_client()
        item = _mock(
            type="movie",
            title="Inception",
            year=2010,
            rating=8.8,
            audienceRating=9.0,
            duration=8880000,
            ratingKey=123,
            addedAt=None,
        )
        playlist = MagicMock()
        playlist.items.return_value = [item]
        server.fetchItem.return_value = playlist
        results = client.get_playlist_items("50")
        assert results[0]["title"] == "Inception"

    def test_non_playlist_raises(self):
        client, server = _make_client()
        movie = _mock(type="movie", title="Not a playlist")
        server.fetchItem.return_value = movie
        with pytest.raises(PlexError, match="not a playlist"):
            client.get_playlist_items("50")


# ---------------------------------------------------------------------------
# Management
# ---------------------------------------------------------------------------


class TestScanLibrary:
    def test_triggers_scan(self):
        client, server = _make_client()
        section = MagicMock()
        server.library.section.return_value = section
        result = client.scan_library("Movies")
        section.update.assert_called_once()
        assert "Movies" in result
