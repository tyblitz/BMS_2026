import time
from typing import Any, Optional

_CACHE: dict[str, tuple[float, Any]] = {}


def get_analytics_cache(key: str) -> Optional[Any]:
    """Retrieves cached analytics result if not expired."""
    entry = _CACHE.get(key)
    if not entry:
        return None
    expires_at, data = entry
    if time.time() > expires_at:
        _CACHE.pop(key, None)
        return None
    return data


def set_analytics_cache(key: str, data: Any, ttl_seconds: int = 120):
    """Stores data in memory with TTL expiration."""
    _CACHE[key] = (time.time() + ttl_seconds, data)


def clear_analytics_cache():
    """Invalidates all cached analytics (e.g. after upload, edit, or delete)."""
    _CACHE.clear()
