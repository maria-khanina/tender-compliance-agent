import pathlib
from collections.abc import Iterator

import docx
import openpyxl
from docx.document import Document as DocxDocument
from docx.oxml.ns import qn
from docx.table import Table, _Row
from docx.text.paragraph import Paragraph
from openpyxl.cell.cell import Cell, MergedCell
from pypdf import PdfReader

from schemas import DocumentInput


NON_BREAKING_SPACE = " "


def _normalize_text(text: str) -> str:
    return text.replace(NON_BREAKING_SPACE, " ")


def _iter_docx_block_items(
    document: DocxDocument,
) -> Iterator[Paragraph | Table]:
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def _docx_table_row_text(row: _Row) -> str:
    cells = [cell.text.strip() for cell in row.cells]
    return " | ".join(cells)


def _extract_docx_text(path: pathlib.Path) -> str:
    document = docx.Document(str(path))
    lines = []
    for block in _iter_docx_block_items(document):
        if isinstance(block, Paragraph):
            lines.append(block.text)
        elif isinstance(block, Table):
            for row in block.rows:
                lines.append(_docx_table_row_text(row))
    return "\n".join(lines)


def _extract_pdf_text(path: pathlib.Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        pages.append(f"--- PAGE {page_number} ---")
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _xlsx_row_text(row: tuple[Cell | MergedCell, ...]) -> str | None:
    cells = ["" if cell.value is None else str(cell.value) for cell in row]
    if not any(cell.strip() for cell in cells):
        return None
    return " | ".join(cells)


def _extract_xlsx_text(path: pathlib.Path) -> str:
    workbook = openpyxl.load_workbook(str(path), data_only=True)
    lines = []
    for sheet_name in workbook.sheetnames:
        worksheet = workbook[sheet_name]
        lines.append(f"=== SHEET: {sheet_name} ===")
        for row in worksheet.iter_rows():
            row_text = _xlsx_row_text(row)
            if row_text is not None:
                lines.append(row_text)
    return "\n".join(lines)


def _extract_txt_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


_EXTRACTORS = {
    ".txt": _extract_txt_text,
    ".docx": _extract_docx_text,
    ".pdf": _extract_pdf_text,
    ".xlsx": _extract_xlsx_text,
}


def _extract_document_text(path: pathlib.Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".doc":
        raise ValueError(
            f"{path}: legacy .doc format is not supported. "
            "Convert the file to .docx and try again."
        )
    extractor = _EXTRACTORS.get(suffix)
    if extractor is None:
        raise ValueError(
            f"{path}: unsupported file format {suffix!r}. "
            f"Supported formats: {sorted(_EXTRACTORS)}."
        )
    return extractor(path)


def load_document_text(path: str) -> DocumentInput:
    file_path = pathlib.Path(path)
    raw_text = _extract_document_text(file_path)
    normalized_text = _normalize_text(raw_text)
    if not normalized_text.strip():
        raise ValueError(f"Document at {path} is empty.")
    return DocumentInput(path=path, text=normalized_text)


def load_document_texts(paths: list[str]) -> list[DocumentInput]:
    return [load_document_text(path) for path in paths]
