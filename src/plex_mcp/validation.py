"""Input validation helpers for Plex rating keys and pagination parameters."""


def validate_rating_key(value: str) -> str:
    """Validate a Plex rating key (numeric string)."""
    value = value.strip()
    if not value.isdigit():
        raise ValueError(f"Invalid rating key: '{value}'. Expected a numeric string.")
    return value


def validate_limit(value: int, max_val: int = 50) -> int:
    """Clamp a limit parameter to the range [1, max_val]."""
    return max(1, min(value, max_val))
