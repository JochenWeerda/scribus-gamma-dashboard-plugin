"""Shared monorepo packages namespace.

This repo uses a `packages.*` import style. The `packages/` directory is mounted
into containers at `/packages`, so Python must see it as a real package.
"""

__all__: list[str] = []

