# Collection Management & Watch State Tools

## Goal

Extend mcp-plex with full CRUD for collections (regular + smart) and watch state management tools. Also add `get_collection_items` for reading collection contents.

## New Tools (11 total)

### Phase 1: Collection Read Enhancement + Formatting
- [x] Enrich `format_collection` with `smart` and `summary` fields
- [x] `get_collection_items(rating_key)` -- list items in a collection

### Phase 2: Collection CRUD
- [x] `create_collection(library_name, title, rating_keys)` -- create a regular collection
- [x] `create_smart_collection(library_name, title, libtype, sort, filters, limit)` -- create a smart collection
- [x] `edit_collection(rating_key, title, summary, sort_order, mode)` -- edit collection metadata
- [x] `add_to_collection(rating_key, item_rating_keys)` -- add items to a regular collection
- [x] `remove_from_collection(rating_key, item_rating_keys)` -- remove items from a regular collection
- [x] `delete_collection(rating_key)` -- delete a collection

### Phase 3: Watch State Management
- [x] `mark_watched(rating_key)` -- mark a media item as fully watched
- [x] `mark_unwatched(rating_key)` -- mark a media item as unwatched
- [x] `remove_from_continue_watching(rating_key)` -- remove from continue watching / on-deck
- [x] `set_playback_progress(rating_key, progress_ms)` -- set a specific playback position

### Phase 4: Documentation
- [x] Update README.md with new tool list

## Implementation Details

### Layering (follows existing pattern)

Each new tool touches three layers:

1. **`formatting.py`** -- enrich `format_collection`, add `format_collection_detailed`
2. **`client.py`** -- new `PlexClient` methods wrapping `plexapi` calls
3. **`server.py`** -- new `@mcp.tool()` definitions

### Phase 1: Collection Read Enhancement

**formatting.py** -- enrich `format_collection` with:
- `smart` (bool) via `collection.smart`
- `summary` (str, if present)

Add `format_collection_detailed` for single-collection views:
- `smart`, `summary`, `sort`, `mode`, `labels`

**client.py** -- `get_collection_items`:
- Validates via `getattr(collection, 'type', None) == 'collection'` (not `hasattr(item, 'items')` which would also match playlists)
- Wrapped in try/except like all other client methods
- Returns `[format_media_item(item) for item in collection.items()]`

### Phase 2: Collection CRUD

**`create_collection`** -- uses `section.createCollection(title=title, items=items)` where items are fetched via `plex.fetchItem()` for each rating key. Returns formatted collection after creation.

**`create_smart_collection`** -- uses `section.createCollection(title=title, smart=True, libtype=libtype, sort=sort, filters=filters, limit=limit)`.
- `libtype` parameter required for show libraries (e.g., "episode", "show") to control what the filters match
- Filters dict uses plexapi operator syntax: `>>` (greater than), `<<` (less than), `!` (not)
- Docstring must document operator syntax and common filter fields (genre, year, rating, decade, contentRating, resolution, etc.)
- Returns formatted collection after creation

**`edit_collection`** -- all params optional except `rating_key`. Uses `collection.editTitle()`, `collection.editSummary()`, `collection.sortUpdate()`, `collection.modeUpdate()`. Returns formatted collection after edit.

**`add_to_collection` / `remove_from_collection`** -- fetches items from rating keys, calls `collection.addItems(items)` / `collection.removeItems(items)`. Validates the collection is not smart (smart collections don't support manual item changes). Returns confirmation with updated item count.

**`delete_collection`** -- calls `collection.delete()`. Returns confirmation string.

### Phase 3: Watch State

Capability checks use the specific method being called, not a proxy attribute:

- `mark_watched` -> validates `hasattr(item, 'markWatched')`, then calls `item.markWatched()`
- `mark_unwatched` -> validates `hasattr(item, 'markUnwatched')`, then calls `item.markUnwatched()`
- `remove_from_continue_watching` -> validates `hasattr(item, 'removeFromContinueWatching')` (only on Movie/Episode), then calls it
- `set_playback_progress` -> validates `hasattr(item, 'updateProgress')`, validates `progress_ms > 0` (plexapi: setting 0 does not work; use `mark_unwatched` instead), calls `item.updateProgress(progress_ms, state="stopped")`

All return a confirmation string with the item title and action taken.

### Validation

- New `validate_rating_keys(values: list[str])` helper for bulk operations (calls `validate_rating_key` on each)

### Explicitly Out of Scope

- Editing smart collection filters after creation (`collection.updateFilters()`) -- can add later if needed
- Reordering items within collections (`collection.moveItem()`) -- can add later
- Collection poster/art management

## File Change Summary

| File | Changes |
|------|---------|
| `validation.py` | Add `validate_rating_keys` |
| `formatting.py` | Enrich `format_collection`, add `format_collection_detailed` |
| `client.py` | Add 11 new methods |
| `server.py` | Add 11 new `@mcp.tool()` definitions |
| `README.md` | Update tool list |
