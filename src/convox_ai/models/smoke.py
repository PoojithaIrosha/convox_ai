from typing import cast

from pydantic import BaseModel

from convox_ai.models.chat import build_chat_models
from convox_ai.models.embeddings import SentenceTransformerEmbedder
from convox_ai.models.rerank import CrossEncoderReranker
from convox_ai.settings import Settings

QUESTION_EN = "How long does delivery to Jaffna take?"
QUESTION_SI = "යාපනයට බෙදා හැරීමට කොපමණ කාලයක් ගතවේද?"  # the same question in Sinhala
UNRELATED = "Our office is closed on public holidays."
ANSWER = "Orders to Jaffna arrive within 3 working days. Cash on delivery is available."


class Pong(BaseModel):
    word: str


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _report(name: str, ok: bool, detail: str) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)
    return ok


async def run_smoke(settings: Settings) -> bool:
    results: list[bool] = []
    chat = build_chat_models(settings)

    reply = await chat.reply.ainvoke("Reply with exactly one word: pong")
    results.append(_report("reply model", "pong" in reply.text.lower(), repr(reply.text[:80])))

    structured = cast(
        Pong,
        await chat.fast.with_structured_output(Pong).ainvoke(
            "Fill the field 'word' with the word pong."
        ),
    )
    results.append(_report("structured output", structured.word.lower() == "pong", repr(structured)))

    embedder = SentenceTransformerEmbedder(settings.models.embedding)
    en, si, other = await embedder.embed_documents([QUESTION_EN, QUESTION_SI, UNRELATED])
    same, different = _dot(en, si), _dot(en, other)
    results.append(
        _report(
            "embeddings",
            embedder.dimensions == 1024 and same > different,
            f"{embedder.dimensions} dims; en~si {same:.3f} > en~unrelated {different:.3f}",
        )
    )

    reranker = CrossEncoderReranker(settings.models.reranker)
    relevant, irrelevant = await reranker.score(QUESTION_SI, [ANSWER, UNRELATED])
    results.append(
        _report(
            "reranker",
            0 <= irrelevant < relevant <= 1,
            f"answer {relevant:.3f} > unrelated {irrelevant:.3f}",
        )
    )
    return all(results)