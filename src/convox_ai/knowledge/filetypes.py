import zipfile
from enum import StrEnum
from pathlib import Path

from convox_ai.shared.errors import PermanentError


class FileType(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    HTML = "html"
    MARKDOWN = "md"
    TEXT = "txt"
    PNG = "png"
    JPEG = "jpg"
    WEBP = "webp"

IMAGE_TYPES = {FileType.PNG, FileType.JPEG, FileType.WEBP}
MIME_TYPES = {FileType.PNG: "image/png", FileType.JPEG: "image/jpeg", FileType.WEBP: "image/webp"}

def detect_file_type(path: Path, file_name: str) -> FileType:
    head = path.read_bytes()[:512]
    if head.startswith(b"%PDF-"):
        return FileType.PDF
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return FileType.PNG
    if head.startswith(b"\xff\xd8\xff"):
        return FileType.JPEG
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return FileType.WEBP
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())
        except zipfile.BadZipfile as e:
            raise PermanentError("unsupported_type", "damaged zip file") from e
        if "word/document.xml" in names:
            return FileType.DOCX
        if "ppt/presentation.xml" in names:
            return FileType.PPTX
        raise PermanentError("unsupported_type", "zip file that isn't DOCX or PPTX")

    try:
        text = head.decode("utf-8")
    except UnicodeDecodeError as e:
        if e.start < len(head) - 3:
            raise PermanentError("unsupported_type", "binary file of unknown type") from e
        text = head[: e.start].decode("utf-8")
    start = text.lstrip().lower()
    if start.startswith(("<!doctype html", "<html")):
        return FileType.HTML
    if file_name.lower().endswith((".md", ".markdown")):
        return FileType.MARKDOWN
    return FileType.TEXT