"""Time-ordered UUIDv7 ids, the same kind the backend uses.

Python 3.14 adds uuid.uuid7(); on 3.12 the uuid6 package provides it. The result is
converted to a plain uuid.UUID so psycopg, Pydantic and JSON treat it like any other id.
"""

from uuid import UUID

from uuid6 import uuid7


def new_id() -> UUID:
    return UUID(int=uuid7().int)