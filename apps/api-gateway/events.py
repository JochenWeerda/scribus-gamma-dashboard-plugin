"""Event-Handler für API-Gateway."""

import logging
from packages.event_bus import get_event_bus
from packages.cache import get_cache

logger = logging.getLogger(__name__)

event_bus = get_event_bus()
cache = get_cache()


def handle_job_status_update(event_type: str, data: dict):
    """Event-Handler für Job-Status-Updates."""
    job_id = data.get("job_id")
    if not job_id:
        return
    
    # Cache invalidieren
    cache_key = f"job:{job_id}"
    cache.delete(cache_key)
    logger.debug(f"Cache invalidated for job: {job_id}")


def setup_event_listeners():
    """Richtet Event-Listener ein."""
    if not event_bus.enabled:
        logger.info("Event-Bus deaktiviert, keine Event-Listener eingerichtet")
        return
    
    # Job-Status-Updates abonnieren
    event_bus.subscribe("jobs", handle_job_status_update)
    logger.info("Event-Listener eingerichtet: jobs -> handle_job_status_update")

