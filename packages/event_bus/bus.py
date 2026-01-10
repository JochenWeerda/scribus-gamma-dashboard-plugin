"""Event-Bus Implementation basierend auf Redis Pub/Sub."""

import json
import logging
import os
from typing import Callable, Dict, Any, Optional
import redis

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event-Bus basierend auf Redis Pub/Sub.
    
    Ermöglicht asynchrone Event-Kommunikation zwischen Services.
    """
    
    def __init__(self, redis_url: str):
        """
        Initialisiert Event-Bus.
        
        Args:
            redis_url: Redis Connection URL
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            self.enabled = True
            # Test Connection
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis nicht verfügbar für Event-Bus: {e}. Event-Bus deaktiviert.")
            self.redis_client = None
            self.pubsub = None
            self.enabled = False
    
    def publish(self, channel: str, event_type: str, data: Dict[str, Any]):
        """
        Veröffentlicht ein Event.
        
        Args:
            channel: Event-Kanal (z.B. "jobs", "artifacts", "status")
            event_type: Event-Typ (z.B. "job.created", "job.completed")
            data: Event-Daten (wird als JSON serialisiert)
        """
        if not self.enabled or not self.redis_client:
            logger.debug(f"Event-Bus deaktiviert, Event nicht veröffentlicht: {channel}/{event_type}")
            return
        
        try:
            event = {
                "type": event_type,
                "data": data,
            }
            message = json.dumps(event)
            self.redis_client.publish(channel, message)
            logger.debug(f"Event published: {channel}/{event_type}")
        except Exception as e:
            logger.error(f"Fehler beim Veröffentlichen von Event: {e}")
    
    def subscribe(self, channel: str, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Abonniert einen Event-Kanal.
        
        Args:
            channel: Event-Kanal
            callback: Callback-Funktion (event_type, data)
        
        Returns:
            PubSub-Objekt für weiteres Handling
        """
        if not self.enabled or not self.pubsub:
            logger.warning(f"Event-Bus deaktiviert, Subscription nicht möglich: {channel}")
            return None
        
        try:
            self.pubsub.subscribe(channel)
            
            def message_handler(message):
                if message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        event_type = event.get("type")
                        event_data = event.get("data", {})
                        callback(event_type, event_data)
                    except Exception as e:
                        logger.error(f"Fehler beim Verarbeiten von Event: {e}")
            
            return self.pubsub
            
        except Exception as e:
            logger.error(f"Fehler beim Abonnieren von Kanal: {e}")
            return None
    
    def unsubscribe(self, channel: str):
        """Beendet Abonnement eines Kanals."""
        if not self.enabled or not self.pubsub:
            return
        
        try:
            self.pubsub.unsubscribe(channel)
        except Exception as e:
            logger.error(f"Fehler beim Beenden des Abonnements: {e}")


def get_event_bus() -> EventBus:
    """
    Erstellt EventBus aus Umgebungsvariablen.
    
    Environment Variables:
        REDIS_URL: Redis Connection URL
        EVENT_BUS_ENABLED: 'true' zum Aktivieren (default: 'true')
    """
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    enabled = os.environ.get("EVENT_BUS_ENABLED", "true").lower() == "true"
    
    if not enabled:
        # Return disabled EventBus
        class DisabledEventBus:
            enabled = False
            def publish(self, *args, **kwargs): pass
            def subscribe(self, *args, **kwargs): return None
            def unsubscribe(self, *args, **kwargs): pass
        
        return DisabledEventBus()
    
    return EventBus(redis_url)

