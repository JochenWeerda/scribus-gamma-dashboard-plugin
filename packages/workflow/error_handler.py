from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar


T = TypeVar("T")


@dataclass
class RetryPolicy:
    max_retries: int = 2
    backoff_seconds: float = 0.5


def run_with_retries(fn: Callable[[], T], *, policy: RetryPolicy = RetryPolicy()) -> T:
    last_exc: Exception | None = None
    for attempt in range(policy.max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt >= policy.max_retries:
                raise
            time.sleep(policy.backoff_seconds * (attempt + 1))
    assert last_exc is not None
    raise last_exc

