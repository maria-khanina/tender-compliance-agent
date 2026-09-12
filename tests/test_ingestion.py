import pathlib

import docx
import openpyxl
import pytest

from steps.ingestion import load_document_text, load_document_texts


def test_txt_is_read_and_nbsp_is_normalized(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "requirements.txt"
    path.write_text("Offeror must register in SAM.", encoding="utf-8")
    document = load_document_text(str(path))
    assert document.path == str(path)
    assert document.text == "Offeror must register in SAM."


def test_docx_preserves_paragraph_and_table_order(
    tmp_path: pathlib.Path,
) -> None:
    document = docx.Document()
    document.add_paragraph("First paragraph.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Item"
    table.cell(0, 1).text = "Qty"
    table.cell(1, 0).text = "Widget"
    table.cell(1, 1).text = "3"
    document.add_paragraph("Last paragraph.")
    path = tmp_path / "rfq.docx"
    document.save(str(path))

    result = load_document_text(str(path))

    lines = result.text.splitlines()
    assert lines == [
        "First paragraph.",
        "Item | Qty",
        "Widget | 3",
        "Last paragraph.",
    ]


def test_xlsx_joins_cells_and_skips_blank_rows(
    tmp_path: pathlib.Path,
) -> None:
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = "1. Base"
    worksheet.append(["CLIN", "Item Description", "Quantity"])
    worksheet.append([1, "Widget", 25])
    worksheet.append([None, None, None])
    path = tmp_path / "attachment_a.xlsx"
    workbook.save(str(path))

    result = load_document_text(str(path))

    lines = result.text.splitlines()
    assert lines == [
        "=== SHEET: 1. Base ===",
        "CLIN | Item Description | Quantity",
        "1 | Widget | 25",
    ]


class _FakePdfPage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakePdfReader:
    def __init__(self, _path: str) -> None:
        self.pages = [_FakePdfPage("Page one text."), _FakePdfPage("Page two text.")]


def test_pdf_joins_pages_with_page_markers(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("steps.ingestion.PdfReader", _FakePdfReader)
    path = tmp_path / "sow.pdf"
    path.write_bytes(b"%PDF-1.4 fake content")

    result = load_document_text(str(path))

    assert result.text == (
        "--- PAGE 1 ---\nPage one text.\n"
        "--- PAGE 2 ---\nPage two text."
    )


def test_doc_format_is_rejected_with_a_clear_message(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "legacy.doc"
    path.write_bytes(b"not a real doc file")
    with pytest.raises(ValueError, match=r"\.docx"):
        load_document_text(str(path))


def test_unsupported_format_is_rejected(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "notes.md"
    path.write_text("some text", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported"):
        load_document_text(str(path))


def test_empty_document_is_rejected(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("   \n\t", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        load_document_text(str(path))


def test_load_document_texts_preserves_input_order(
    tmp_path: pathlib.Path,
) -> None:
    first_path = tmp_path / "first.txt"
    second_path = tmp_path / "second.txt"
    first_path.write_text("First document.", encoding="utf-8")
    second_path.write_text("Second document.", encoding="utf-8")

    documents = load_document_texts([str(first_path), str(second_path)])

    assert [document.path for document in documents] == [
        str(first_path),
        str(second_path),
    ]
    assert documents[0].text == "First document."
    assert documents[1].text == "Second document."
