"""Describe an uploaded image as text, so search and the reply model can use it."""

import base64
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from convox_ai.shared.errors import PermanentError

PROMPT = (
    "You are indexing a business's knowledge base for search. First transcribe all "
    "visible text exactly: prices, product names, opening hours, phone numbers. Then "
    "describe in two or three sentences what the image shows. Write in the language of "
    "the text in the image; if there is none, write in English. Output plain text only."
)


def image_message(path: Path, mime_type: str) -> HumanMessage:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return HumanMessage(
        content=[
            {"type": "text", "text": PROMPT},
            {"type": "image", "base64": data, "mime_type": mime_type},
        ]
    )


class ImageDescriber:
    def __init__(self, model: BaseChatModel) -> None:
        self._model = model  # a chat model that accepts images (settings.models.vision)

    async def describe(self, path: Path, mime_type: str) -> str:
        response = await self._model.ainvoke([image_message(path, mime_type)])
        text = response.text.strip()
        if not text:
            raise PermanentError("empty_document", "the vision model returned no description")
        return text