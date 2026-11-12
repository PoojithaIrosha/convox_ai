from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import Field

from convox_ai.contracts.base import Contract

Channel = Literal["WHATSAPP", "MESSENGER", "INSTAGRAM"]

class Author(StrEnum):
    CONTACT = "CONTACT"
    AGENT = "AGENT"
    ASSISTANT = "ASSISTANT"
    EXTERNAL = "EXTERNAL"

class TranscriptMessage(Contract):
    id: UUID
    at: datetime
    author: Author
    type: str
    text: str | None = None

class Summary(Contract):
    text: str
    up_to_message_id: UUID

class AssistantConfig(Contract):
    business_name: str
    instructions: str = Field(default="", max_length=4000)
    default_language: str = "en"
    min_retrieval_score: float = Field(default=0.5, ge=0, le=1)
    max_reply_chars: int = Field(default=1000, gt=0)

class ReplyRequested(Contract):
    run_id: UUID
    organization_id: UUID
    conversation_id: UUID | None
    purpose: Literal["CONVERSATION", "PREVIEW"]
    channel: Channel
    based_on_message_id: UUID | None
    requested_at: datetime
    config: AssistantConfig
    contact_name: str | None = None
    summary: Summary | None  = None
    messages: list[TranscriptMessage] = Field(max_length=60)

class Citation(Contract):
    section_id: UUID
    document_id: UUID
    title: str
    heading_path: list[str]
    score: float

class Diagnostics(Contract):
    top_score: float | None
    reply_model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    latency_ms: int

class ReplyResult(Contract):
    run_id: UUID
    organization_id: UUID
    conversation_id: UUID | None
    based_on_message_id: UUID | None
    status: Literal["COMPLETED", "FAILED"]
    decision: Literal["ANSWER", "HANDOFF", "NO_REPLY"]
    reply: str | None = None
    handoff_reason: str | None = None
    language: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    summary: Summary | None = None
    diagnostics: Diagnostics | None = None
    error_code: str | None = None


