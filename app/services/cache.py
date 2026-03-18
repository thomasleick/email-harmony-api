import hashlib
import time
from typing import Any, Dict, Tuple
from app.core.config import settings

class SimpleMemoryCache:
    def __init__(self):
        # key: hash, value: (timestamp, data)
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def _generate_key(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Any | None:
        key = self._generate_key(text)
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < settings.CACHE_TTL_SECONDS:
                return data
            else:
                del self._cache[key]
        return None

    def set(self, text: str, data: Any):
        key = self._generate_key(text)
        self._cache[key] = (time.time(), data)

# Global Instance
cache = SimpleMemoryCache()
