from collections.abc import Sequence
from uuid import UUID

from pgvector import Vector

from convox_ai.shared.db import Connection

VECTOR_SEARCH = """
WITH nearest AS MATERIALIZED (
    SELECT id, embedding <=> %(query)s AS distance
    FROM kb.chunks
    ORDER BY distance
    LIMIT %(limit)s
)
SELECT id FROM nearest ORDER BY distance
"""

async def vector_search(
        conn: Connection,
        query_vector: Sequence[float],
        limit: int = 50
) -> list[UUID]:
    """Call inside db.tenant_tx(...): the SET LOCAL lines last until that transaction ends."""
    await conn.execute("SET LOCAL hnsw.iterative_scan = relaxed_order")
    await conn.execute("SET LOCAL hnsw.ef_search = 100")
    cur = await conn.execute(VECTOR_SEARCH, { "query": Vector(list(query_vector)), "limit": limit })
    return [row[0] for row in await cur.fetchall()]