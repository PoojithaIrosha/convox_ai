from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pgvector import Vector

from convox_ai.shared.db import Connection


@dataclass(frozen=True)
class IndexedDocument:
    version: int
    content_hash: bytes
    section_count: int
    chunk_count: int


@dataclass(frozen=True)
class SectionRow:
    id: UUID
    section_index: int
    heading_path: list[str]
    kind: str
    body: str
    page_from: int | None
    page_to: int | None
    token_count: int


@dataclass(frozen=True)
class ChunkRow:
    id: UUID
    section_id: UUID
    chunk_index: int
    text: str
    search_text: str
    embedding: list[float]


async def find_indexed(conn: Connection, document_id: UUID) -> IndexedDocument | None:
    cur = await conn.execute(
        "SELECT version, content_hash, section_count, chunk_count"
        " FROM kb.indexed_documents WHERE document_id = %s",
        (document_id,),
    )
    row = await cur.fetchone()
    return IndexedDocument(*row) if row else None


async def replace_document(
    conn: Connection,
    *,
    document_id: UUID,
    organization_id: UUID,
    version: int,
    content_hash: bytes,
    title: str,
    embedding_model: str,
    indexed_at: datetime,
    sections: list[SectionRow],
    chunks: list[ChunkRow],
) -> None:
    """Delete the document's old rows and insert the new ones. Run it in one transaction."""
    await delete_document(conn, document_id)  # cascades to sections and chunks
    await conn.execute(
        "INSERT INTO kb.indexed_documents (document_id, organization_id, version, content_hash,"
        " title, embedding_model, section_count, chunk_count, indexed_at)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            document_id,
            organization_id,
            version,
            content_hash,
            title,
            embedding_model,
            len(sections),
            len(chunks),
            indexed_at,
        ),
    )
    async with conn.cursor() as cur:
        await cur.executemany(
            "INSERT INTO kb.sections (id, organization_id, document_id, section_index,"
            " heading_path, kind, body, page_from, page_to, token_count)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    s.id,
                    organization_id,
                    document_id,
                    s.section_index,
                    s.heading_path,
                    s.kind,
                    s.body,
                    s.page_from,
                    s.page_to,
                    s.token_count,
                )
                for s in sections
            ],
        )
        await cur.executemany(
            "INSERT INTO kb.chunks (id, organization_id, document_id, section_id, chunk_index,"
            " text, search_text, embedding, embedding_model)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    c.id,
                    organization_id,
                    document_id,
                    c.section_id,
                    c.chunk_index,
                    c.text,
                    c.search_text,
                    Vector(c.embedding),
                    embedding_model,
                )
                for c in chunks
            ],
        )


async def delete_document(conn: Connection, document_id: UUID) -> bool:
    cur = await conn.execute(
        "DELETE FROM kb.indexed_documents WHERE document_id = %s", (document_id,)
    )
    return cur.rowcount > 0