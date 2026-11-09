from collections.abc import Sequence
from typing import Protocol

import anyio
import numpy as np
from sentence_transformers import SentenceTransformer

from convox_ai.models.device import best_device


class Embedder(Protocol):
    @property
    def model_id(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...

    def count_tokens(self, text: str) -> int: ...


class SentenceTransformerEmbedder:
    def __init__(
        self,
        model_id: str,
        *,
        device: str | None = None,
        batch_size: int = 16,
        cache_folder: str | None = None,
    ) -> None:
        self._model = SentenceTransformer(
            model_id, device=device or best_device(), cache_folder=cache_folder
        )
        dimensions = self._model.get_embedding_dimension()
        if dimensions is None:
            raise ValueError(f"{model_id} does not report an embedding size")
        self._model_id = model_id
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._one_at_a_time = anyio.CapacityLimiter(1)

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=True,  # length 1, so cosine = dot product
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32).tolist()  # type: ignore[no-any-return]

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        return await anyio.to_thread.run_sync(
            self._encode, list(texts), limiter=self._one_at_a_time
        )

    async def embed_query(self, text: str) -> list[float]:
        # bge-m3 needs no query prefix. Some other models do: read the model card.
        return (await self.embed_documents([text]))[0]

    def count_tokens(self, text: str) -> int:
        """Tokens as this model counts them. The chunker (Part 5) sizes chunks with it."""
        return len(self._model.tokenizer.encode(text, add_special_tokens=False))