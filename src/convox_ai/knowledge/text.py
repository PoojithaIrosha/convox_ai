
import re
from collections.abc import Callable

CountTokens = Callable[[str], int]

_SENTENCE_END = re.compile(r"(?<=[.!?।])\s+")

def split_sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE_END.split(text.strip()) if s]


def pack(pieces: list[str], count: CountTokens, limit: int, joiner: str) -> list[str]:
    """Join pieces in order into groups of at most `limit` tokens.

    A piece that is bigger than `limit` on its own becomes its own group; callers
    split such pieces first (split_to_fit) when that matters.
    """
    groups: list[str] = []
    current: list[str] = []
    size = 0
    for piece in pieces:
        n = count(piece)
        if current and size + n > limit:
            groups.append(joiner.join(current))
            current, size = [], 0
        current.append(piece)
        size += n
    if current:
        groups.append(joiner.join(current))
    return groups

def split_to_fit(text: str, count: CountTokens, limit: int) -> list[str]:
    """Split one long paragraph into pieces of at most `limit` tokens, at sentence ends.

    A single sentence longer than the limit is split between words.
    """
    pieces: list[str] = []
    for sentence in split_sentences(text):
        if count(sentence) <= limit:
            pieces.append(sentence)
        else:
            pieces.extend(pack(sentence.split(), count, limit, joiner=" "))
    return pack(pieces, count, limit, joiner=" ")
