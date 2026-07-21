import fitz

from src.pdf_loader import PDFLoader


def _make_pdf(path, pages_text):
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_discover_pdfs_returns_empty_list_for_missing_directory(tmp_path):
    loader = PDFLoader(tmp_path / "does_not_exist")

    assert loader.discover_pdfs() == []


def test_discover_pdfs_returns_empty_list_for_empty_directory(tmp_path):
    loader = PDFLoader(tmp_path)

    assert loader.discover_pdfs() == []


def test_discover_pdfs_finds_pdf_files(tmp_path):
    _make_pdf(tmp_path / "a.pdf", ["Hello world"])
    (tmp_path / "not_a_pdf.txt").write_text("ignore me")

    loader = PDFLoader(tmp_path)
    pdfs = loader.discover_pdfs()

    assert len(pdfs) == 1
    assert pdfs[0].name == "a.pdf"


def test_load_all_extracts_text_per_page(tmp_path):
    _make_pdf(tmp_path / "doc.pdf", ["First page content", "Second page content"])

    loader = PDFLoader(tmp_path)
    pages = list(loader.load_all())

    assert len(pages) == 2
    assert pages[0].filename == "doc.pdf"
    assert pages[0].page_number == 1
    assert "First page content" in pages[0].text
    assert pages[1].page_number == 2
    assert "Second page content" in pages[1].text


def test_load_all_skips_invalid_pdf(tmp_path):
    bad_file = tmp_path / "broken.pdf"
    bad_file.write_text("this is not a real pdf")

    loader = PDFLoader(tmp_path)
    pages = list(loader.load_all())

    assert pages == []
