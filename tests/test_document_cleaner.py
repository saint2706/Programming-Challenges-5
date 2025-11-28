from __future__ import annotations

from ArtificialIntelligence.document_cleaner import DocumentCleaner


def test_email_and_url_removal() -> None:
    cleaner = DocumentCleaner()
    raw = "Contact us at help@example.com or visit https://example.com/about for details."
    cleaned = cleaner._remove_emails_and_urls(raw)
    assert "example.com" not in cleaned
    assert "https://" not in cleaned


def test_fix_ocr_errors() -> None:
    cleaner = DocumentCleaner()
    raw = "The offi\ncial ﬂyer shows the infor-\nmation clearly."
    cleaned = cleaner._fix_ocr_errors(raw)
    assert "official flyer" in cleaned
    assert "information" in cleaned


def test_strip_repeated_headers_and_footers() -> None:
    cleaner = DocumentCleaner()
    raw = (
        "Report Header\n\nPage 1 content line\nFooter Text\f"
        "Report Header\n\nPage 2 content line\nFooter Text"
    )
    cleaned = cleaner._strip_repeated_headers_footers(raw)
    assert "Report Header" not in cleaned
    assert "Footer Text" not in cleaned
    assert "Page 1 content line" in cleaned
    assert "Page 2 content line" in cleaned


def test_classifier_removes_singleton_header() -> None:
    def mock_classifier(line: str) -> str:
        return "header" if "Confidential" in line else "body"

    cleaner = DocumentCleaner(line_classifier=mock_classifier)
    raw = "Confidential\nUnique content on first page\fSecond page body"
    cleaned = cleaner._strip_repeated_headers_footers(raw, min_repeats=2)
    assert "Confidential" not in cleaned
    assert "Unique content on first page" in cleaned
    assert "Second page body" in cleaned
