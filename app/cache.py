"""
Caching utilities for the CampManager API
"""
import hashlib
import json
from functools import wraps
from typing import Any, Dict, Optional, Union
from flask import current_app
from datetime import datetime, timedelta


class SimpleCache:
    """Simple in-memory cache implementation"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            return None
        
        # Check if expired
        if key in self._expiry and datetime.utcnow() > self._expiry[key]:
            self.delete(key)
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, timeout: int = 300) -> None:
        """Set value in cache with timeout in seconds"""
        self._cache[key] = value
        if timeout > 0:
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=timeout)
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        self._expiry.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_keys = len(self._cache)
        expired_keys = sum(1 for key, expiry in self._expiry.items() 
                          if datetime.utcnow() > expiry)
        
        return {
            'total_keys': total_keys,
            'expired_keys': expired_keys,
            'active_keys': total_keys - expired_keys
        }


# Global cache instance
cache = SimpleCache()


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments"""
    # Create a string representation of all arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items()) if kwargs else {}
    }
    
    # Convert to JSON string and hash it
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(timeout: int = 300, key_prefix: str = ''):
    """
    Decorator to cache function results
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                current_app.logger.debug(f"Cache HIT for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            current_app.logger.debug(f"Cache MISS for key: {cache_key}")
            result = func(*args, **kwargs)
            
            # Only cache non-None results
            if result is not None:
                cache.set(cache_key, result, timeout)
                current_app.logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache keys matching a pattern
    
    Args:
        pattern: Pattern to match (simple string matching)
    
    Returns:
        Number of keys invalidated
    """
    keys_to_delete = [key for key in cache._cache.keys() if pattern in key]
    
    for key in keys_to_delete:
        cache.delete(key)
    
    current_app.logger.info(f"Invalidated {len(keys_to_delete)} cache keys matching pattern: {pattern}")
    return len(keys_to_delete)


def invalidate_registration_form_cache(camp_id: str) -> int:
    """
    Invalidate registration form cache for a specific camp
    
    Args:
        camp_id: Camp ID to invalidate cache for
    
    Returns:
        Number of keys invalidated
    """
    pattern = f"registration_form:{camp_id}"
    return invalidate_cache_pattern(pattern)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return cache.get_stats()


def clear_all_cache() -> None:
    """Clear all cache"""
    cache.clear()
    current_app.logger.info("All cache cleared")
