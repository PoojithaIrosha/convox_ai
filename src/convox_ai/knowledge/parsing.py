from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from docling.exceptions import ConversionError
from docling_core.types import DoclingDocument
from docling_core.types.doc import DocItemLabel, TextItem, TableItem, TitleItem, SectionHeaderItem
from docling_core.types.io import DocumentStream
from marko.block import ListItem
from six import BytesIO

from convox_ai.knowledge.filetypes import FileType
from convox_ai.knowledge.types import ParsedDocument, Block
from convox_ai.shared.errors import PermanentError

_DOCLING_FORMATS = {
    FileType.PDF: InputFormat.PDF,
    FileType.DOCX: InputFormat.DOCX,
    FileType.PPTX: InputFormat.PPTX,
    FileType.HTML: InputFormat.HTML,
    FileType.MARKDOWN: InputFormat.MD
}

_SKIP_LABELS = { DocItemLabel.PAGE_HEADER, DocItemLabel.PAGE_FOOTER }

class DocumentParser:
    """Create once per process: Docling loads its layout and models on first PDF."""

    def __init__(self, max_pages: int) -> None:
        self.max_pages = max_pages
        self._converter = DocumentConverter(allowed_formats=list(_DOCLING_FORMATS.values()))

    def parse(self, path: Path, file_type: FileType):
        """Blocking: call it from a worker thread"""
        if file_type == FileType.TEXT:
            return _parse_plain_text(path)
        if file_type not in _DOCLING_FORMATS:
            raise PermanentError("unsupported_type", f"{file_type} can't be parsed as a document")

        stream = DocumentStream(
            name=f"document.{file_type.value}",
            stream=BytesIO(path.read_bytes())
        )

        try:
            result = self._converter.convert(stream, max_num_pages=self.max_pages)
        except ConversionError as e:
            raise PermanentError("parse_failed", str(e)[:300]) from e
        doc =  result.document
        return ParsedDocument(blocks=list(_blocks(doc)), page_count=len(doc.pages) or None)

def _blocks(doc: DoclingDocument) -> list[Block]:
    blocks: list[Block] = []
    for item, _depth in doc.iterate_items():
        if not isinstance(item, (TextItem, TableItem)) or item.label in _SKIP_LABELS:
            continue
        page = item.prov[0].page_no if item.prov else None
        if isinstance(item, TitleItem):
            blocks.append(Block("heading", item.text.strip(), level=1, page=page))
        elif isinstance(item, SectionHeaderItem):
            blocks.append(Block("heading", item.text.strip(), level=item.level +1, page=page))
        elif isinstance(item, TableItem):
            table = item.export_to_markdown(doc=doc).strip()
            if table:
                blocks.append(Block("table", table, page=page))
        elif isinstance(item, ListItem):
            blocks.append(Block("text", f"- {item.text.strip()}", page=page))
        elif item.text.strip():
            blocks.append(Block("text", item.text.strip(), page=page))
    return blocks

def _parse_plain_text(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8", errors="replace")
    paragraphs = [p.strip() for p in text.replace("\r\n", "\n").split("\n\n")]
    return ParsedDocument(blocks=[Block("text", p) for p in paragraphs if p])
