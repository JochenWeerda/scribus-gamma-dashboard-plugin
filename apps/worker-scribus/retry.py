"""Retry-Logic für Worker-Jobs."""

import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_on_failure(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator für Retry-Logik.
    
    Args:
        max_retries: Maximale Anzahl von Retries
        backoff_factor: Exponential backoff Faktor
        exceptions: Tuple von Exceptions, die retried werden sollen
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
                        raise
            
            # Sollte nie erreicht werden, aber für Type-Checking
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry state")
        
        return wrapper
    return decorator

