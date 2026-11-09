from collections.abc import Sequence
from typing import Protocol

import anyio
import numpy as np
from sentence_transformers import CrossEncoder

from convox_ai.models.device import best_device


class Reranker(Protocol):
    async def score(self, query: str, passages: Sequence[str]) -> list[float]: ...


class CrossEncoderReranker:
    def __init__(
        self,
        model_id: str,
        *,
        device: str | None = None,
        max_length: int = 1024,
        batch_size: int = 16,
        cache_folder: str | None = None,
    ) -> None:
        self._model = CrossEncoder(
            model_id,
            device=device or best_device(),
            max_length=max_length,
            cache_folder=cache_folder,
        )
        if self._model.num_labels != 1:
            raise ValueError(f"{model_id} must output one relevance score per pair")
        self._batch_size = batch_size
        self._one_at_a_time = anyio.CapacityLimiter(1)

    def _predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        scores = self._model.predict(
            pairs, batch_size=self._batch_size, convert_to_numpy=True, show_progress_bar=False
        )
        return [float(s) for s in np.asarray(scores).reshape(-1)]

    async def score(self, query: str, passages: Sequence[str]) -> list[float]:
        if not passages:
            return []
        pairs = [(query, p) for p in passages]
        return await anyio.to_thread.run_sync(self._predict, pairs, limiter=self._one_at_a_time)