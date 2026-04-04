# mcp-plex

MCP server for Plex Media Server, focused on media discovery, search, library management, and playback control. 24 granular tools designed for use with Claude and other LLM agents.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- A running [Plex Media Server](https://www.plex.tv/)
- A Plex authentication token

## Setup

### 1. Get Your Plex Token

The easiest way to find your Plex token:

1. Sign in to [Plex Web App](https://app.plex.tv)
2. Browse to any media item and click **Get Info** (or **...** > **Get Info**)
3. Click **View XML** in the bottom-left
4. In the URL bar, find the `X-Plex-Token=` parameter -- that's your token

Alternatively, check the [Plex support article](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) for other methods.

### 2. Install

```bash
cd mcp-plex
uv sync
```

### 3. Configure Environment Variables

Set these before running the server:

```bash
export PLEX_SERVER_URL="http://your-plex-server:32400"
export PLEX_TOKEN="your_plex_token"
```

### 4. Test the Connection

```bash
uv run mcp-plex-server
```

The server connects to your Plex server on startup and verifies the token. If the connection fails, check that your server URL and token are correct.

## Claude Desktop / Claude Code Configuration

Add to your MCP server config. If installed from PyPI:

```json
{
  "mcpServers": {
    "plex": {
      "command": "uvx",
      "args": ["mcp-plex-server"],
      "env": {
        "PLEX_SERVER_URL": "http://your-plex-server:32400",
        "PLEX_TOKEN": "your_plex_token"
      }
    }
  }
}
```

Or if running from a local clone:

```json
{
  "mcpServers": {
    "plex": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-plex", "run", "mcp-plex-server"],
      "env": {
        "PLEX_SERVER_URL": "http://your-plex-server:32400",
        "PLEX_TOKEN": "your_plex_token"
      }
    }
  }
}
```

## Tools

### Discovery

| Tool | Parameters | Description |
|------|-----------|-------------|
| `search_media` | `query`, `media_type=""`, `limit=20` | Search across all libraries. Optional type filter: "movie", "show", "episode", "artist", "album", "track". |
| `get_recently_added` | `limit=20`, `library_name=""` | Recently added media, optionally filtered to a library. |
| `get_on_deck` | `limit=10` | Continue watching / next episode list. |

### Library Browsing

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_libraries` | (none) | List all library sections with types and item counts. |
| `get_library_contents` | `library_name`, `sort="titleSort"`, `limit=50` | Browse a library. Sort by title, date added, year, or rating. |
| `get_media_details` | `rating_key` | Full details for one item: summary, genres, cast, directors, ratings. |
| `get_library_stats` | `library_name=""` | Item counts and stats for one or all libraries. |

### Shows

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_seasons` | `rating_key` | List seasons for a TV show. |
| `get_episodes` | `rating_key`, `season_number=0` | List episodes (all or by season). |

### Collections

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_collections` | `library_name` | List collections in a library (includes smart/regular type). |
| `get_collection_items` | `rating_key` | Get collection details and all items it contains. |
| `create_collection` | `library_name`, `title`, `rating_keys` | Create a regular collection from specific items. |
| `create_smart_collection` | `library_name`, `title`, `filters`, `libtype=""`, `sort=""`, `limit=0` | Create a smart (filter-based) auto-updating collection. |
| `edit_collection` | `rating_key`, `title=""`, `summary=None`, `sort_order=""`, `mode=""` | Edit collection metadata (title, summary, sort, display mode). |
| `add_to_collection` | `rating_key`, `item_rating_keys` | Add items to a regular collection. |
| `remove_from_collection` | `rating_key`, `item_rating_keys` | Remove items from a regular collection. |
| `delete_collection` | `rating_key` | Delete a collection (does not affect the media items). |

### Playlists

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_playlists` | (none) | List all playlists on the server. |
| `get_playlist_items` | `rating_key` | Get items in a playlist. |

### Watch State

| Tool | Parameters | Description |
|------|-----------|-------------|
| `mark_watched` | `rating_key` | Mark a movie, episode, or track as fully watched. |
| `mark_unwatched` | `rating_key` | Mark an item as unwatched, resetting progress. |
| `remove_from_continue_watching` | `rating_key` | Remove a movie or episode from Continue Watching / On Deck. |
| `set_playback_progress` | `rating_key`, `progress_ms` | Set playback position in milliseconds (must be > 0). |

### Management

| Tool | Parameters | Description |
|------|-----------|-------------|
| `scan_library` | `library_name` | Trigger a background library scan. |

## Development

```bash
uv run mcp-plex-server              # Run the server
uv run ruff check src/       # Lint
uv run ruff format src/      # Format
uv run pyright src/          # Type check
```

### Pre-commit Hooks

This project uses [lefthook](https://github.com/evilmartians/lefthook) for pre-commit checks. Install with `brew install lefthook` (or see [other install methods](https://github.com/evilmartians/lefthook/blob/master/docs/install.md)), then:

```bash
lefthook install
```
