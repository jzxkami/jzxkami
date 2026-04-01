from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    def __init__(self, ttl_seconds: int, maxsize: int = 512) -> None:
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.maxsize = max(1, int(maxsize))

        self._store: OrderedDict[K, tuple[float, V]] = OrderedDict()
        self._lock = threading.RLock()

        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: K) -> tuple[bool, V | None]:
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if item is None:
                self._misses += 1
                return False, None

            expires_at, value = item
            if expires_at <= now:
                del self._store[key]
                self._misses += 1
                return False, None

            self._store.move_to_end(key)
            self._hits += 1
            return True, value

    def set(self, key: K, value: V) -> None:
        expires_at = time.time() + self.ttl_seconds
        with self._lock:
            self._store[key] = (expires_at, value)
            self._store.move_to_end(key)

            while len(self._store) > self.maxsize:
                self._store.popitem(last=False)
                self._evictions += 1

    def stats(self) -> dict[str, int]:
        with self._lock:
            now = time.time()
            expired_keys = [k for k, (exp, _) in self._store.items() if exp <= now]
            for k in expired_keys:
                del self._store[k]

            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "size": len(self._store),
                "ttl_seconds": self.ttl_seconds,
                "maxsize": self.maxsize,
            }
