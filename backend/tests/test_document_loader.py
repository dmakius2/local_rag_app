import docx
import fitz

from src.document_loader import DocumentLoader


def _make_pdf(path, pages_text):
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def _make_docx(path, paragraphs):
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    document.save(path)


def test_discover_documents_returns_empty_list_for_missing_directory(tmp_path):
    loader = DocumentLoader(tmp_path / "does_not_exist")

    assert loader.discover_documents() == []


def test_discover_documents_returns_empty_list_for_empty_directory(tmp_path):
    loader = DocumentLoader(tmp_path)

    assert loader.discover_documents() == []


def test_discover_documents_finds_supported_files_only(tmp_path):
    _make_pdf(tmp_path / "a.pdf", ["Hello world"])
    (tmp_path / "b.txt").write_text("some text")
    _make_docx(tmp_path / "c.docx", ["some docx text"])
    (tmp_path / "d.doc").write_bytes(b"legacy binary doc")
    (tmp_path / "ignore.jpg").write_bytes(b"not a document")

    loader = DocumentLoader(tmp_path)
    names = sorted(p.name for p in loader.discover_documents())

    assert names == ["a.pdf", "b.txt", "c.docx", "d.doc"]


def test_load_all_extracts_text_per_pdf_page(tmp_path):
    _make_pdf(tmp_path / "doc.pdf", ["First page content", "Second page content"])

    loader = DocumentLoader(tmp_path)
    pages = list(loader.load_all())

    assert len(pages) == 2
    assert pages[0].filename == "doc.pdf"
    assert pages[0].page_number == 1
    assert "First page content" in pages[0].text
    assert pages[1].page_number == 2
    assert "Second page content" in pages[1].text


def test_load_all_skips_invalid_pdf(tmp_path):
    (tmp_path / "broken.pdf").write_text("this is not a real pdf")

    loader = DocumentLoader(tmp_path)
    pages = list(loader.load_all())

    assert pages == []


def test_load_all_extracts_text_from_docx(tmp_path):
    _make_docx(tmp_path / "notes.docx", ["First paragraph.", "Second paragraph."])

    loader = DocumentLoader(tmp_path)
    pages = list(loader.load_all())

    assert len(pages) == 1
    assert pages[0].filename == "notes.docx"
    assert pages[0].page_number == 1
    assert "First paragraph." in pages[0].text
    assert "Second paragraph." in pages[0].text


def test_load_all_extracts_text_from_txt(tmp_path):
    (tmp_path / "notes.txt").write_text("Plain text content.")

    loader = DocumentLoader(tmp_path)
    pages = list(loader.load_all())

    assert len(pages) == 1
    assert pages[0].filename == "notes.txt"
    assert pages[0].page_number == 1
    assert pages[0].text == "Plain text content."


def test_load_all_skips_legacy_doc_without_raising(tmp_path):
    (tmp_path / "legacy.doc").write_bytes(b"legacy binary doc content")
    (tmp_path / "notes.txt").write_text("still gets indexed")

    loader = DocumentLoader(tmp_path)
    pages = list(loader.load_all())

    assert len(pages) == 1
    assert pages[0].filename == "notes.txt"
