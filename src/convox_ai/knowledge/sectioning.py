from convox_ai.knowledge.text import CountTokens, pack, split_to_fit
from convox_ai.knowledge.types import Block, DraftSection

MAX_SECTION_TOKENS = 1200

def build_sections(
    blocks: list[Block],
    title: str,
    count_tokens: CountTokens,
    max_tokens: int = MAX_SECTION_TOKENS,
) -> list[DraftSection]:
    sections: list[DraftSection] = []
    stack: list[tuple[int, str]] = []  # the headings we're under: (level, text)
    current: list[Block] = []

    def close() -> None:
        if current:  # a heading with no body makes no section
            sections.append(DraftSection([title, *(h for _, h in stack)], current.copy()))
            current.clear()

    for block in blocks:
        if block.kind != "heading":
            current.append(block)
            continue
        if not stack and block.level <= 1 and block.text.casefold() == title.casefold():
            continue  # the document's own title is already the first path element
        close()
        while stack and stack[-1][0] >= block.level:
            stack.pop()
        stack.append((block.level, block.text))
    close()

    result: list[DraftSection] = []
    for section in sections:
        result.extend(split_oversized(section, count_tokens, max_tokens))
    return result

def split_oversized(
    section: DraftSection, count_tokens: CountTokens, max_tokens: int
) -> list[DraftSection]:
    """Split a section over max_tokens into consecutive sections with the same path."""
    pieces: list[Block] = []
    for block in section.blocks:
        if count_tokens(block.text) <= max_tokens:
            pieces.append(block)
        elif block.kind == "table":
            pieces.extend(_split_table(block, count_tokens, max_tokens))
        else:
            parts = split_to_fit(block.text, count_tokens, max_tokens)
            pieces.extend(Block(block.kind, p, page=block.page) for p in parts)

    result: list[DraftSection] = []
    current: list[Block] = []
    size = 0
    for block in pieces:
        n = count_tokens(block.text)
        if current and size + n > max_tokens:
            result.append(DraftSection(section.heading_path, current))
            current, size = [], 0
        current.append(block)
        size += n
    if current:
        result.append(DraftSection(section.heading_path, current))
    return result


def _split_table(block: Block, count_tokens: CountTokens, max_tokens: int) -> list[Block]:
    """Split a Markdown table by rows, repeating its header row in every part."""
    lines = block.text.splitlines()
    header, rows = "\n".join(lines[:2]), lines[2:]
    budget = max(max_tokens - count_tokens(header), 1)
    groups = pack(rows, count_tokens, budget, joiner="\n")
    return [Block("table", f"{header}\n{group}", page=block.page) for group in groups]