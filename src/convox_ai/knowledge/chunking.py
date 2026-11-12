from itertools import pairwise

from convox_ai.knowledge.text import CountTokens, pack, split_sentences, split_to_fit
from convox_ai.knowledge.types import DraftChunk, DraftSection

TARGET_TOKENS = 300  # aim for this
MAX_TOKENS = 450  # never more than this (plus the repeated sentence)

def chunk_section(
    section: DraftSection,
    count_tokens: CountTokens,
    target: int = TARGET_TOKENS,
    hard_max: int = MAX_TOKENS,
) -> list[DraftChunk]:
    body = section.body
    if count_tokens(body) <= hard_max:
        texts = [body]  # a small section is one chunk
    else:
        units: list[str] = []
        for block in section.blocks:
            if count_tokens(block.text) <= target:
                units.append(block.text)
            else:
                units.extend(split_to_fit(block.text, count_tokens, target))
        texts = _with_overlap(pack(units, count_tokens, target, joiner="\n\n"), count_tokens)

    prefix = " > ".join(section.heading_path)
    return [DraftChunk(i, t, f"{prefix}\n\n{t}") for i, t in enumerate(texts)]


def _with_overlap(texts: list[str], count_tokens: CountTokens, max_overlap: int = 60) -> list[str]:
    """Start each chunk with the last sentence of the one before, if that sentence is short.

    A fact split across a chunk boundary then appears whole in at least one chunk.
    """
    result = texts[:1]
    for previous, text in pairwise(texts):
        sentences = split_sentences(previous)
        carry = sentences[-1] if sentences else ""
        if carry and count_tokens(carry) <= max_overlap:
            result.append(f"{carry} {text}")
        else:
            result.append(text)
    return result