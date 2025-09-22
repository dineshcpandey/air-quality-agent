# src/utils/cache.py
import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
import pickle

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    ttl_seconds: int
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)

class InMemoryCache:
    """In-memory cache with TTL support"""
    
    def __init__(self, default_ttl_seconds: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl_seconds
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired())
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                entry.hit_count += 1
                self.stats['hits'] += 1
                return entry.value
            else:
                # Remove expired entry
                del self.cache[key]
                self.stats['evictions'] += 1
        
        self.stats['misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            ttl_seconds=ttl
        )
    
    async def get_or_compute(self, 
                            key: str, 
                            compute_fn: Callable,
                            ttl: Optional[int] = None) -> Any:
        """Get from cache or compute if not present"""
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Compute value
        if asyncio.iscoroutinefunction(compute_fn):
            value = await compute_fn()
        else:
            value = compute_fn()
        
        # Cache it
        await self.set(key, value, ttl)
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        import re
        regex = re.compile(pattern)
        keys_to_delete = [k for k in self.cache.keys() if regex.match(k)]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        return len(keys_to_delete)
    
    async def _cleanup_expired(self):
        """Background task to clean up expired entries"""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            expired_keys = [
                key for key, entry in self.cache.items() 
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
                self.stats['evictions'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            'size': len(self.cache),
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

class DatabaseCache:
    """Database-backed cache for persistence"""
    
    def __init__(self, db_connection, table_name: str = 'cache.query_results'):
        self.db = db_connection
        self.table_name = table_name
        
    async def initialize(self):
        """Create cache table if not exists"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            cache_key VARCHAR(64) PRIMARY KEY,
            value JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            ttl_seconds INTEGER,
            hit_count INTEGER DEFAULT 0
        );
        
        CREATE INDEX IF NOT EXISTS idx_cache_expiry 
        ON {self.table_name} (created_at, ttl_seconds);
        """
        await self.db.execute_query(sql)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from database cache"""
        sql = f"""
        SELECT value, created_at, ttl_seconds
        FROM {self.table_name}
        WHERE cache_key = $1
            AND (created_at + INTERVAL '1 second' * ttl_seconds) > NOW()
        """
        
        result = await self.db.execute_query(sql, [key])
        if result:
            # Update hit count
            await self.db.execute_query(
                f"UPDATE {self.table_name} SET hit_count = hit_count + 1 WHERE cache_key = $1",
                [key]
            )
            return result[0]['value']
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in database cache"""
        sql = f"""
        INSERT INTO {self.table_name} (cache_key, value, ttl_seconds)
        VALUES ($1, $2, $3)
        ON CONFLICT (cache_key) 
        DO UPDATE SET value = $2, created_at = NOW(), ttl_seconds = $3
        """
        
        await self.db.execute_query(sql, [key, json.dumps(value), ttl])