"""Event-Bus Package - Redis Pub/Sub für Event-Kommunikation."""

try:
    from .bus import EventBus, get_event_bus
    __all__ = ["EventBus", "get_event_bus"]
except ImportError:
    # Fallback wenn redis nicht verfügbar
    __all__ = []

