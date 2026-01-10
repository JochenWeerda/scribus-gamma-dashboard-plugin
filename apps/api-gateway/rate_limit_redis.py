"""Redis-basierter Rate-Limiter für Multi-Instance-Support."""

import time
import logging
from typing import Optional
import redis

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Redis-basierter Rate-Limiter für Multi-Instance-Support.
    
    Verwendet Redis für Shared State zwischen mehreren API-Gateway-Instanzen.
    """
    
    def __init__(
        self,
        redis_url: str,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit:",
    ):
        """
        Initialisiert Redis Rate-Limiter.
        
        Args:
            redis_url: Redis Connection URL
            requests_per_window: Max. Requests pro Zeitfenster
            window_seconds: Zeitfenster in Sekunden
            key_prefix: Prefix für Redis-Keys
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test Connection
            self.redis_client.ping()
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis nicht verfügbar für Rate-Limiting: {e}. Fallback zu In-Memory.")
            self.redis_client = None
            self.enabled = False
        
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
    
    def is_allowed(self, identifier: str) -> tuple[bool, Optional[int]]:
        """
        Prüft ob Request erlaubt ist.
        
        Args:
            identifier: Identifier (z.B. IP-Adresse)
        
        Returns:
            Tuple (is_allowed, retry_after_seconds)
        """
        if not self.enabled or not self.redis_client:
            # Fallback: Immer erlauben wenn Redis nicht verfügbar
            return True, None
        
        key = f"{self.key_prefix}{identifier}"
        now = int(time.time())
        window_start = now - self.window_seconds
        
        try:
            # Pipeline für atomare Operationen
            pipe = self.redis_client.pipeline()
            
            # Entferne alte Einträge (außerhalb des Zeitfensters)
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Zähle aktuelle Requests
            pipe.zcard(key)
            
            # Füge aktuellen Request hinzu
            pipe.zadd(key, {str(now): now})
            
            # Setze TTL (expire nach window_seconds)
            pipe.expire(key, self.window_seconds)
            
            results = pipe.execute()
            current_count = results[1]
            
            if current_count >= self.requests_per_window:
                # Rate Limit überschritten
                # Berechne Retry-After (Zeit bis ältester Request aus Fenster fällt)
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = int(oldest[0][1])
                    retry_after = (oldest_time + self.window_seconds) - now + 1
                    return False, max(1, retry_after)
                
                return False, self.window_seconds
            
            return True, None
        
        except Exception as e:
            logger.error(f"Redis Rate-Limiter Fehler: {e}")
            # Bei Fehler: Erlauben (fail-open)
            return True, None
    
    def get_remaining(self, identifier: str) -> int:
        """
        Gibt verbleibende Requests zurück.
        
        Args:
            identifier: Identifier (z.B. IP-Adresse)
        
        Returns:
            Anzahl verbleibender Requests
        """
        if not self.enabled or not self.redis_client:
            return self.requests_per_window
        
        key = f"{self.key_prefix}{identifier}"
        now = int(time.time())
        window_start = now - self.window_seconds
        
        try:
            # Entferne alte Einträge
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Zähle aktuelle Requests
            count = self.redis_client.zcard(key)
            return max(0, self.requests_per_window - count)
        
        except Exception as e:
            logger.error(f"Redis Rate-Limiter Fehler (get_remaining): {e}")
            return self.requests_per_window

