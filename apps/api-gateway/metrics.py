"""Prometheus Metrics für API-Gateway."""

import time
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

# Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Job Metrics
jobs_total = Counter(
    "jobs_total",
    "Total jobs created",
    ["job_type", "status"],
)

jobs_processing_duration_seconds = Histogram(
    "jobs_processing_duration_seconds",
    "Job processing duration in seconds",
    ["job_type"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

# Queue Metrics
queue_size = Gauge(
    "queue_size",
    "Current queue size",
    ["queue_name"],
)

# Error Metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware für Prometheus Metrics."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint selbst
        if request.url.path == "/metrics":
            return await call_next(request)
        
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()
            
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)
            
            # Track errors
            if status_code >= 400:
                errors_total.labels(
                    error_type=f"http_{status_code}",
                    endpoint=endpoint,
                ).inc()
            
            return response
        
        except Exception as e:
            # Track exceptions
            errors_total.labels(
                error_type=type(e).__name__,
                endpoint=endpoint,
            ).inc()
            raise


def metrics_endpoint():
    """Prometheus Metrics Endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def record_job_created(job_type: str, status: str):
    """Record job creation metric."""
    jobs_total.labels(job_type=job_type, status=status).inc()


def record_job_processing_duration(job_type: str, duration_seconds: float):
    """Record job processing duration."""
    jobs_processing_duration_seconds.labels(job_type=job_type).observe(duration_seconds)


def update_queue_size(queue_name: str, size: int):
    """Update queue size metric."""
    queue_size.labels(queue_name=queue_name).set(size)

