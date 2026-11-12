import tempfile
from dataclasses import dataclass
from pathlib import Path

import anyio

from convox_ai.contracts.ingest import IngestRequested
from convox_ai.knowledge.chunking import chunk_section
from convox_ai.knowledge.filetypes import IMAGE_TYPES, MIME_TYPES, FileType, detect_file_type
from convox_ai.knowledge.images import ImageDescriber
from convox_ai.knowledge.parsing import DocumentParser
from convox_ai.knowledge.repository import (
    ChunkRow,
    SectionRow,
    delete_document,
    find_indexed,
    replace_document,
)
from convox_ai.knowledge.sectioning import build_sections
from convox_ai.knowledge.storage import ObjectStorage
from convox_ai.knowledge.types import Block, DraftSection
from convox_ai.models.embeddings import Embedder
from convox_ai.shared.clock import Clock
from convox_ai.shared.db import Database
from convox_ai.shared.errors import PermanentError
from convox_ai.shared.ids import new_id


@dataclass(frozen=True)
class IndexOutcome:
    section_count: int
    chunk_count: int
    page_count: int
    skipped: bool


class IngestService:
    def __init__(
            self,
            *,
            db: Database,
            storage: ObjectStorage,
            parser: DocumentParser,
            embedder: Embedder,
            describer: ImageDescriber | None,
            clock: Clock,
            max_file_bytes: int,
            parse_timeout_s: float,
    ) -> None:
        self._db = db
        self._storage = storage
        self._parser = parser
        self._embedder = embedder
        self._describer = describer
        self._clock = clock
        self._max_file_bytes = max_file_bytes
        self._parse_timeout_s = parse_timeout_s

    async def index(self, req: IngestRequested) -> IndexOutcome:
        if not (req.storage_key and req.sha256 and req.title and req.file_name):
            raise PermanentError(
                "invalid_request", "INDEX needs storageKey, sha256, title, fileName"
            )
        content_hash = bytes.fromhex(req.sha256)

        async with self._db.tenant_tx(req.organization_id) as conn:
            existing = await find_indexed(conn, req.document_id)
        if existing and existing.version == req.version and existing.content_hash == content_hash:
            return IndexOutcome(existing.section_count, existing.chunk_count, None, skipped=True)

        with tempfile.TemporaryDirectory(prefix="convox-ingest-") as folder:
            path = await self._storage.download(req.storage_key, Path(folder), self._max_file_bytes)
            file_type = detect_file_type(path, req.file_name)
            sections, page_count = await self._sections(path, file_type, req.title)
        if not sections:
            raise PermanentError("empty_document", "no text found in the file")

        section_rows: list[SectionRow] = []
        chunk_drafts: list[tuple[SectionRow, int, str, str]] = []
        count = self._embedder.count_tokens
        for index, section in enumerate(sections):
            page_from, page_to = section.pages
            row = SectionRow(
                id=new_id(),
                section_index=index,
                heading_path=section.heading_path,
                kind=section.kind,
                body=section.body,
                page_from=page_from,
                page_to=page_to,
                token_count=count(section.body),
            )
            section_rows.append(row)
            for chunk in chunk_section(section, count):
                chunk_drafts.append((row, chunk.index, chunk.text, chunk.search_text))

        vectors = await self._embedder.embed_documents([d[3] for d in chunk_drafts])
        chunk_rows = [
            ChunkRow(new_id(), section.id, index, text, search_text, vector)
            for (section, index, text, search_text), vector in zip(
                chunk_drafts, vectors, strict=True
            )
        ]

        async with self._db.tenant_tx(req.organization_id) as conn:
            await replace_document(
                conn,
                document_id=req.document_id,
                organization_id=req.organization_id,
                version=req.version,
                content_hash=content_hash,
                title=req.title,
                embedding_model=self._embedder.model_id,
                indexed_at=self._clock.now(),
                sections=section_rows,
                chunks=chunk_rows,
            )
        return IndexOutcome(len(section_rows), len(chunk_rows), page_count, skipped=False)

    async def delete(self, req: IngestRequested) -> None:
        async with self._db.tenant_tx(req.organization_id) as conn:
            await delete_document(conn, req.document_id)

    async def _sections(
            self, path: Path, file_type: FileType, title: str
    ) -> tuple[list[DraftSection], int | None]:
        if file_type in IMAGE_TYPES:
            if self._describer is None:
                raise PermanentError("unsupported_type", "image description is not configured")
            text = await self._describer.describe(path, MIME_TYPES[file_type])
            return [DraftSection([title], [Block("image", text)])], None

        try:
            with anyio.fail_after(self._parse_timeout_s):
                parsed = await anyio.to_thread.run_sync(
                    self._parser.parse, path, file_type, abandon_on_cancel=True
                )
        except TimeoutError as e:
            raise PermanentError("parse_failed", "parsing took too long") from e
        sections = build_sections(parsed.blocks, title, self._embedder.count_tokens)
        return sections, parsed.page_count
