from __future__ import annotations

import re
from collections import Counter
from typing import Callable, Iterable, List

LineClassifier = Callable[[str], str]


class DocumentCleaner:
    """Cleans raw document text with regex-based heuristics.

    The cleaner removes emails and URLs, repairs common OCR artifacts, and
    strips repeated headers/footers across paginated text. An optional machine
    learning classifier hook can be provided to label lines as "header",
    "footer", or "body" to further improve structural cleanup.

    Args:
        line_classifier: Optional callable that receives a line of text and
            returns a label. Lines labeled as "header" or "footer" will be
            removed when cleaning pages.
    """

    def __init__(self, line_classifier: LineClassifier | None = None) -> None:
        self.line_classifier = line_classifier

    def clean(self, text: str) -> str:
        """Run all cleaning passes on the provided text.

        Args:
            text: Raw document text.

        Returns:
            Cleaned document text with noise removed.
        """

        without_contacts = self._remove_emails_and_urls(text)
        fixed_ocr = self._fix_ocr_errors(without_contacts)
        return self._strip_repeated_headers_footers(fixed_ocr)

    def _remove_emails_and_urls(self, text: str) -> str:
        """Remove email addresses and URLs using regex patterns."""

        email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        url_pattern = r"https?://\S+|www\.\S+"
        combined_pattern = rf"({email_pattern})|({url_pattern})"
        return re.sub(combined_pattern, "", text)

    def _fix_ocr_errors(self, text: str) -> str:
        """Fix a handful of common OCR mistakes via regex replacements."""

        replacements = (
            (r"ﬁ", "fi"),
            (r"ﬂ", "fl"),
            (r"(?<=\w)\n(?=\w)", ""),
            (r"(\w+)-\n(\w+)", r"\1\2"),
            (r"\bI\b(?=\w)", "l"),
        )

        cleaned = text
        for pattern, repl in replacements:
            cleaned = re.sub(pattern, repl, cleaned)
        return cleaned

    def _strip_repeated_headers_footers(self, text: str, min_repeats: int = 2) -> str:
        """Remove headers and footers repeated across multiple pages.

        Pages are split on form-feed characters (``\f``). The first and last
        non-empty lines that repeat across at least ``min_repeats`` pages are
        removed. If a ``line_classifier`` is provided, any line classified as a
        header/footer at the page boundary is also removed.

        Args:
            text: Document text containing zero or more form-feed delimiters.
            min_repeats: Minimum number of repeated occurrences to consider a
                line a header or footer.

        Returns:
            Text with repeated headers and footers removed.
        """

        pages = [page.splitlines() for page in re.split(r"\f+", text)]
        header_counts: Counter[str] = Counter()
        footer_counts: Counter[str] = Counter()

        for lines in pages:
            header = self._first_non_empty(lines)
            footer = self._last_non_empty(lines)
            if header:
                header_counts[header] += 1
            if footer:
                footer_counts[footer] += 1

        repeated_headers = {line for line, count in header_counts.items() if count >= min_repeats}
        repeated_footers = {line for line, count in footer_counts.items() if count >= min_repeats}

        cleaned_pages: List[str] = []
        for lines in pages:
            trimmed = self._remove_boundary_line(lines, repeated_headers, from_start=True)
            trimmed = self._remove_boundary_line(trimmed, repeated_footers, from_start=False)
            cleaned_pages.append("\n".join(trimmed).strip())

        return "\n\n".join([page for page in cleaned_pages if page])

    def _remove_boundary_line(
        self, lines: Iterable[str], to_remove: set[str], *, from_start: bool
    ) -> List[str]:
        """Remove a boundary line if it matches repeated text or ML labels."""

        lines_list = list(lines)
        if not lines_list:
            return []

        index = 0 if from_start else len(lines_list) - 1
        candidate = lines_list[index]
        stripped = candidate.strip()

        is_repeated = stripped in to_remove and stripped
        is_ml_labeled = False
        if self.line_classifier and stripped:
            label = self.line_classifier(stripped)
            boundary_label = "header" if from_start else "footer"
            is_ml_labeled = label.lower() == boundary_label

        if is_repeated or is_ml_labeled:
            if from_start:
                return lines_list[1:]
            return lines_list[:-1]
        return lines_list

    @staticmethod
    def _first_non_empty(lines: Iterable[str]) -> str:
        """Return the first non-empty line from an iterable of lines."""

        for line in lines:
            if line.strip():
                return line.strip()
        return ""

    @staticmethod
    def _last_non_empty(lines: Iterable[str]) -> str:
        """Return the last non-empty line from an iterable of lines."""

        for line in reversed(list(lines)):
            if line.strip():
                return line.strip()
        return ""
