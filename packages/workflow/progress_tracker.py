from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


ProgressCallback = Callable[[Dict[str, Any]], None]


@dataclass
class ProgressTracker:
    on_event: Optional[ProgressCallback] = None
    publish_to_bus: bool = True
    bus_channel: str = "workflow"
    bus_event_prefix: str = "workflow"
    _event_bus: Any = None

    def emit(self, event: str, **payload: Any) -> None:
        message = {"event": event, **payload}

        if self.on_event:
            self.on_event(message)

        if not self.publish_to_bus:
            return

        if self._event_bus is None:
            try:
                from packages.event_bus import get_event_bus  # type: ignore

                self._event_bus = get_event_bus()
            except Exception:
                self._event_bus = False

        if not self._event_bus or not getattr(self._event_bus, "enabled", False):
            return

        try:
            event_type = f"{self.bus_event_prefix}.{event}"
            self._event_bus.publish(self.bus_channel, event_type, message)
        except Exception:
            # Never fail the workflow due to observability.
            pass
