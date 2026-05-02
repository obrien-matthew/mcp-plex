"""Tests for MCP server tool definitions.

These mock PlexClient entirely and verify:
- Tools delegate to the correct client method with correct args
- Return values are JSON-serialized
- PlexError / ValueError are caught and returned as error strings
"""

import json
from importlib.metadata import version
from unittest.mock import MagicMock, patch

import pytest

# Import the module so we can patch _get_client
import plex_mcp.server as server_mod
from plex_mcp.client import PlexError


@pytest.fixture(autouse=True)
def mock_client():
    """Patch _get_client for all tests in this module."""
    client = MagicMock()
    with patch.object(server_mod, "_get_client", return_value=client):
        yield client


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


class TestSearchMediaTool:
    def test_returns_json(self, mock_client):
        mock_client.search_media.return_value = [{"title": "Inception"}]
        result = server_mod.search_media("inception")
        parsed = json.loads(result)
        assert parsed[0]["title"] == "Inception"

    def test_passes_params(self, mock_client):
        mock_client.search_media.return_value = []
        server_mod.search_media("test", media_type="movie", limit=5)
        mock_client.search_media.assert_called_once_with("test", "movie", 5)

    def test_error_returns_string(self, mock_client):
        mock_client.search_media.side_effect = PlexError("fail")
        result = server_mod.search_media("test")
        assert result.startswith("Error:")


class TestGetRecentlyAddedTool:
    def test_returns_json(self, mock_client):
        mock_client.get_recently_added.return_value = [{"title": "New"}]
        result = server_mod.get_recently_added()
        assert json.loads(result)[0]["title"] == "New"


class TestGetOnDeckTool:
    def test_returns_json(self, mock_client):
        mock_client.get_on_deck.return_value = [{"title": "Continue"}]
        result = server_mod.get_on_deck()
        assert json.loads(result)[0]["title"] == "Continue"


# ---------------------------------------------------------------------------
# Library Browsing
# ---------------------------------------------------------------------------


class TestGetLibrariesTool:
    def test_returns_json(self, mock_client):
        mock_client.get_libraries.return_value = [{"title": "Movies"}]
        result = server_mod.get_libraries()
        assert json.loads(result)[0]["title"] == "Movies"


class TestGetLibraryContentsTool:
    def test_passes_params(self, mock_client):
        mock_client.get_library_contents.return_value = []
        server_mod.get_library_contents("Movies", sort="year:desc", limit=10)
        mock_client.get_library_contents.assert_called_once_with(
            "Movies", "year:desc", 10
        )


class TestGetMediaDetailsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_media_details.return_value = {"title": "Inception"}
        result = server_mod.get_media_details("123")
        assert json.loads(result)["title"] == "Inception"


class TestGetLibraryStatsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_library_stats.return_value = {"total_items": 500}
        result = server_mod.get_library_stats("Movies")
        assert json.loads(result)["total_items"] == 500


# ---------------------------------------------------------------------------
# Shows
# ---------------------------------------------------------------------------


class TestGetSeasonsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_seasons.return_value = [{"season_number": 1}]
        result = server_mod.get_seasons("100")
        assert json.loads(result)[0]["season_number"] == 1


class TestGetEpisodesTool:
    def test_passes_season_number(self, mock_client):
        mock_client.get_episodes.return_value = []
        server_mod.get_episodes("100", season_number=2)
        mock_client.get_episodes.assert_called_once_with("100", 2)


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


class TestGetCollectionsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_collections.return_value = [{"title": "Marvel"}]
        result = server_mod.get_collections("Movies")
        assert json.loads(result)[0]["title"] == "Marvel"


class TestGetCollectionItemsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_collection_items.return_value = {
            "title": "Marvel",
            "items": [{"title": "Iron Man"}],
        }
        result = server_mod.get_collection_items("100")
        parsed = json.loads(result)
        assert parsed["items"][0]["title"] == "Iron Man"


class TestCreateCollectionTool:
    def test_passes_params(self, mock_client):
        mock_client.create_collection.return_value = {"title": "New"}
        server_mod.create_collection("Movies", "New", ["1", "2"])
        mock_client.create_collection.assert_called_once_with(
            "Movies", "New", ["1", "2"]
        )


class TestCreateSmartCollectionTool:
    def test_passes_all_params(self, mock_client):
        mock_client.create_smart_collection.return_value = {"title": "Smart"}
        server_mod.create_smart_collection(
            "Movies",
            "Smart",
            {"genre": "Action"},
            libtype="movie",
            sort="year:desc",
            limit=25,
        )
        mock_client.create_smart_collection.assert_called_once_with(
            "Movies", "Smart", {"genre": "Action"}, "movie", "year:desc", 25
        )


class TestEditCollectionTool:
    def test_passes_params(self, mock_client):
        mock_client.edit_collection.return_value = {"title": "Updated"}
        server_mod.edit_collection("100", title="Updated", summary="Desc")
        mock_client.edit_collection.assert_called_once_with(
            "100", "Updated", "Desc", "", ""
        )


class TestAddToCollectionTool:
    def test_passes_params(self, mock_client):
        mock_client.add_to_collection.return_value = {"title": "Col"}
        server_mod.add_to_collection("100", ["50", "51"])
        mock_client.add_to_collection.assert_called_once_with("100", ["50", "51"])


class TestRemoveFromCollectionTool:
    def test_passes_params(self, mock_client):
        mock_client.remove_from_collection.return_value = {"title": "Col"}
        server_mod.remove_from_collection("100", ["50"])
        mock_client.remove_from_collection.assert_called_once_with("100", ["50"])


class TestDeleteCollectionTool:
    def test_returns_string(self, mock_client):
        mock_client.delete_collection.return_value = "Collection 'X' deleted."
        result = server_mod.delete_collection("100")
        assert "deleted" in result

    def test_error_returns_string(self, mock_client):
        mock_client.delete_collection.side_effect = PlexError("not found")
        result = server_mod.delete_collection("999")
        assert result.startswith("Error:")


# ---------------------------------------------------------------------------
# Watch State
# ---------------------------------------------------------------------------


class TestMarkWatchedTool:
    def test_returns_confirmation(self, mock_client):
        mock_client.mark_watched.return_value = "Marked 'X' as watched."
        result = server_mod.mark_watched("123")
        assert "watched" in result


class TestMarkUnwatchedTool:
    def test_returns_confirmation(self, mock_client):
        mock_client.mark_unwatched.return_value = "Marked 'X' as unwatched."
        result = server_mod.mark_unwatched("123")
        assert "unwatched" in result


class TestRemoveFromContinueWatchingTool:
    def test_returns_confirmation(self, mock_client):
        mock_client.remove_from_continue_watching.return_value = "Removed."
        result = server_mod.remove_from_continue_watching("55")
        assert "Removed" in result


class TestSetPlaybackProgressTool:
    def test_returns_confirmation(self, mock_client):
        mock_client.set_playback_progress.return_value = "Set to 60000ms."
        result = server_mod.set_playback_progress("123", 60000)
        assert "60000ms" in result

    def test_value_error_returns_string(self, mock_client):
        mock_client.set_playback_progress.side_effect = ValueError("bad")
        result = server_mod.set_playback_progress("123", 0)
        assert result.startswith("Error:")


# ---------------------------------------------------------------------------
# Playlists
# ---------------------------------------------------------------------------


class TestGetPlaylistsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_playlists.return_value = [{"title": "My List"}]
        result = server_mod.get_playlists()
        assert json.loads(result)[0]["title"] == "My List"


class TestGetPlaylistItemsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_playlist_items.return_value = [{"title": "Item"}]
        result = server_mod.get_playlist_items("50")
        assert json.loads(result)[0]["title"] == "Item"


# ---------------------------------------------------------------------------
# Management
# ---------------------------------------------------------------------------


class TestScanLibraryTool:
    def test_returns_string(self, mock_client):
        mock_client.scan_library.return_value = "Library scan started."
        result = server_mod.scan_library("Movies")
        assert "scan started" in result


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


class TestGetServerVersionTool:
    def test_returns_installed_version(self):
        assert server_mod.get_server_version() == version("mcp-plex-server")
