from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from pgvector.psycopg import register_vector_async
from psycopg import AsyncConnection
from psycopg.rows import TupleRow
from psycopg_pool import AsyncConnectionPool

Connection = AsyncConnection[TupleRow]

async def _register_vector(conn: Connection) -> None:
    """Runs once for each new pooled connection: teaches psycopg the `vector` type.

    After this, pass embeddings as `pgvector.Vector(list_of_floats)` query parameters;
    `vector` columns come back as `pgvector.Vector` (call `.to_list()` for floats).
    """
    await register_vector_async(conn)


class Database:
    def __init__(self, url: str, *, min_size: int = 2, max_size: int = 10) -> None:
        # open=False: the pool is created now but connects only in open(), inside the
        # running event loop. Creating connections at import time would fail.
        self._pool: AsyncConnectionPool[Connection] = AsyncConnectionPool(
            url,
            min_size=min_size,
            max_size=max_size,
            open=False,
            configure=_register_vector,
            name="convox-ai",
        )

    async def open(self) -> None:
        """Connect at startup. Waits until min_size connections work, or fails."""
        await self._pool.open(wait=True, timeout=30)

    async def close(self) -> None:
        await self._pool.close()

    async def ping(self) -> bool:
        """For the readiness check (Part 11): can we run a query right now?"""
        try:
            async with self._pool.connection(timeout=2) as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    @asynccontextmanager
    async def tenant_tx(self, organization_id: UUID) -> AsyncIterator[Connection]:
        """A transaction in which RLS shows only `organization_id`'s rows.

        Commits when the block ends normally, rolls back if it raises.
        """
        async with self._pool.connection() as conn, conn.transaction():
            # set_config(name, value, is_local=true) = SET LOCAL, but accepts a parameter.
            await conn.execute(
                "SELECT set_config('app.tenant_id', %s, true)", (str(organization_id),)
            )
            yield conn