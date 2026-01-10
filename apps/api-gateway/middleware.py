"""Middleware für API-Gateway."""

import time
import json
import logging
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import config

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware für Correlation-ID."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware für Request-Logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        
        # Log Request
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": str(request.url.path),
                "client": request.client.host if request.client else None,
            }
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log Response
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "process_time_ms": int(process_time * 1000),
                }
            )
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "error": str(e),
                    "process_time_ms": int(process_time * 1000),
                },
                exc_info=True
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate-Limiting Middleware.
    
    Verwendet Redis für Multi-Instance-Support, fällt zurück auf In-Memory wenn Redis nicht verfügbar.
    """
    
    def __init__(
        self,
        app,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        use_redis: bool = True,
        redis_url: str = None,
    ):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        
        # Versuche Redis-basierten Rate-Limiter
        if use_redis and redis_url:
            try:
                from rate_limit_redis import RedisRateLimiter
                self.rate_limiter = RedisRateLimiter(
                    redis_url=redis_url,
                    requests_per_window=requests_per_window,
                    window_seconds=window_seconds,
                )
                self.use_redis = self.rate_limiter.enabled
            except Exception as e:
                logger.warning(f"Redis Rate-Limiter konnte nicht initialisiert werden: {e}. Verwende In-Memory.")
                self.use_redis = False
        else:
            self.use_redis = False
        
        # Fallback: In-Memory Rate-Limiter
        if not self.use_redis:
            self._requests = {}  # {ip: [(timestamp, ...), ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not config.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        # Redis-basierter Rate-Limiter
        if self.use_redis:
            is_allowed, retry_after = self.rate_limiter.is_allowed(client_ip)
            if not is_allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": retry_after or self.window_seconds
                    },
                    headers={"Retry-After": str(retry_after or self.window_seconds)}
                )
            return await call_next(request)
        
        # In-Memory Fallback
        now = time.time()
        
        # Cleanup alte Einträge
        if client_ip in self._requests:
            self._requests[client_ip] = [
                ts for ts in self._requests[client_ip]
                if now - ts < self.window_seconds
            ]
        else:
            self._requests[client_ip] = []
        
        # Prüfe Limit
        if len(self._requests[client_ip]) >= self.requests_per_window:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": self.window_seconds
                },
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Track Request
        self._requests[client_ip].append(now)
        
        return await call_next(request)

