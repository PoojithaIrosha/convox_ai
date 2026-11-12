from dataclasses import dataclass, field
from typing import Literal

BlockKind = Literal["heading", "text", "table", "image"]
SectionKind = Literal["TEXT", "TABLE", "IMAGE"]

@dataclass(frozen=True)
class Block:
    kind: BlockKind
    text: str
    level: int = 0
    page: int | None = None

@dataclass(frozen=True)
class ParsedDocument:
    blocks: list[Block]
    page_count: int | None = None

class DraftSection:
    heading_path: list[str]
    blocks: list[Block] = field(default_factory=list)

    @property
    def body(self) -> str:
        return "\n\n".join(b.text for b in self.blocks)

    @property
    def kind(self) -> SectionKind:
        kinds = {b.kind for b in self.blocks}
        if kinds == {"table"}:
            return "TABLE"
        if kinds == {"image"}:
            return "IMAGE"
        return "TEXT"

    @property
    def page(self) -> tuple[int | None, int | None]:
        numbers = [b.page for b in self.blocks if b.page is not None]
        return (min(numbers), max(numbers)) if numbers else (None, None)


@dataclass(frozen=True)
class DraftChunk:
    index: int
    text: str
    search_text: str
