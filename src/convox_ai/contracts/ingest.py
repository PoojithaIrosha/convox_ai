from typing import Literal
from uuid import UUID

from convox_ai.contracts.base import Contract

from datetime import datetime

class IngestRequested(Contract):
    action: Literal["INDEX", "DELETE"]
    document_id: UUID
    organization_id: UUID
    version: int
    storage_key: str | None = None
    content_type: str | None = None
    file_name: str | None = None
    title: str | None = None
    sha256: str | None = None
    requested_at: datetime | None = None

class IngestStatus(Contract):
    document_id: UUID
    organization_id: UUID
    version: int
    status: Literal["PROCESSING", "READY", "FAILED", "DELETED"]
    section_count: int | None = None
    chunk_count: int | None = None
    page_count: int | None = None
    error_code: str | None = None
    at: datetime