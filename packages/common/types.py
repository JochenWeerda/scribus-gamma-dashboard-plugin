"""SQLAlchemy custom types.

We want the same models to work with Postgres (UUID native) and SQLite (tests/dev).
"""

from __future__ import annotations

import uuid
from sqlalchemy.types import TypeDecorator, CHAR


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    - Postgres: uses native UUID
    - Other DBs (e.g. SQLite): stores as CHAR(32) hex
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID

            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value if dialect.name == "postgresql" else value.hex
        # Accept string UUIDs
        parsed = uuid.UUID(str(value))
        return parsed if dialect.name == "postgresql" else parsed.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

