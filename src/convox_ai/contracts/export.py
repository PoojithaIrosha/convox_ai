import json
from pathlib import Path

from pydantic import BaseModel

from convox_ai.contracts.ingest import IngestRequested, IngestStatus
from convox_ai.contracts.reply import ReplyRequested, ReplyResult

CONTRACTS: dict[str, type[BaseModel]] = {
    "reply-requested": ReplyRequested,
    "reply-result": ReplyResult,
    "ingest-requested": IngestRequested,
    "ingest-status": IngestStatus,
}

def render(model: type[BaseModel]) -> str:
    schema = model.model_json_schema(by_alias=True)
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

def export(folder: Path, *, check: bool) -> list[str]:
    """Returns the names of schemas that differ from the files (when check=True)."""
    folder.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for name, model in CONTRACTS.items():
        path = folder / f"{name}.schema.json"
        text = render(model)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(path.name)
        else:
            path.write_text(text, encoding="utf-8")
    return stale