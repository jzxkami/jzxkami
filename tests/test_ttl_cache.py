import time

from app.services.ttl_cache import TTLCache


def test_ttl_cache_hit_and_expire():
    cache: TTLCache[str, str] = TTLCache(ttl_seconds=1, maxsize=2)

    hit, value = cache.get("k1")
    assert hit is False
    assert value is None

    cache.set("k1", "v1")
    hit, value = cache.get("k1")
    assert hit is True
    assert value == "v1"

    time.sleep(1.1)
    hit, value = cache.get("k1")
    assert hit is False
    assert value is None
