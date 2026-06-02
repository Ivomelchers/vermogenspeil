"""Gedeeld CSV-importcontract voor alle broker-platformen."""

from dataclasses import dataclass, field
from typing import Protocol


class CsvParseError(ValueError):
    """Bestand of platform-match ongeldig — geen gedeeltelijke import."""


@dataclass(frozen=True)
class CsvSkippedRow:
    line_number: int
    reason: str
    description: str = ""
    preview: str = ""


@dataclass
class CsvParseResult:
    """Resultaat van één parser-run; geen rijen worden stilletjes weggelaten."""

    rows: list
    rows_in_file: int
    skipped: list[CsvSkippedRow] = field(default_factory=list)

    @property
    def rows_recognized(self) -> int:
        return len(self.rows)

    @property
    def rows_skipped(self) -> int:
        return len(self.skipped)

    @property
    def unknown_descriptions(self) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in self.skipped:
            if item.reason != "unknown_description" or not item.description:
                continue
            if item.description not in seen:
                seen.add(item.description)
                ordered.append(item.description)
        return ordered


class CsvPlatformParser(Protocol):
    platform: str

    def fingerprint_score(self, normalized_headers: set[str]) -> float:
        """0.0–1.0: hoe sterk dit bestand bij dit platform past."""

    def parse(self, content: str) -> CsvParseResult:
        """Parse volledige inhoud; onbekende regels in skipped, niet weggooien."""
