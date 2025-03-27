import time
from typing import Any, Dict, Optional, Callable
from .logger import get_logger

logger = get_logger()

class SimpleCache:
    """A simple in-memory cache with TTL (Time To Live)"""

    def __init__(self, ttl: int = 3600):
        """Initialize the cache
        
        Args:
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry["expires_at"]:
            # Entry has expired
            del self.cache[key]
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL in seconds
        """
        expires_at = time.time() + (ttl if ttl is not None else self.ttl)
        self.cache[key] = {"value": value, "expires_at": expires_at}
        logger.debug(f"Cache set for key: {key}")

    def delete(self, key: str) -> None:
        """Delete a value from the cache
        
        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted for key: {key}")

    def clear(self) -> None:
        """Clear the entire cache"""
        self.cache.clear()
        logger.debug("Cache cleared")

# Create a global cache instance
cache = SimpleCache()

def cached(ttl: int = 3600):
    """Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            result = cache.get(key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator
