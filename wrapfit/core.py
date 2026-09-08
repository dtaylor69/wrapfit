"""Core logic: does any word in a text exceed a given wrap width."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Violation:
    line: int
    paragraph: int
    word: str
    length: int
    excess: int


@dataclass
class Report:
    width: int
    lenient: bool
    tabsize: int = 8
    violations: List[Violation] = field(default_factory=list)
    wrapped_line_count: Optional[int] = None

    @property
    def ok(self) -> bool:
        # In lenient mode a long word is a known, accepted outcome, not a failure.
        return self.lenient or not self.violations

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "width": self.width,
            "lenient": self.lenient,
            "tabsize": self.tabsize,
            "violations": [
                {
                    "line": v.line,
                    "paragraph": v.paragraph,
                    "word": v.word,
                    "length": v.length,
                    "excess": v.excess,
                }
                for v in self.violations
            ],
            "wrapped_line_count": self.wrapped_line_count,
        }


def _indent_width(line: str, tabsize: int) -> int:
    """Column width of a line's leading whitespace, with tabs expanded to tabsize."""
    stripped = line.lstrip(" \t")
    indent = line[: len(line) - len(stripped)]
    return len(indent.expandtabs(tabsize))


def _paragraph_numbers(lines: List[str]) -> List[int]:
    """1-based paragraph number for each line, where a paragraph is a run of
    non-blank lines and a paragraph break is one or more blank lines between them."""
    numbers = []
    paragraph = 1
    seen_content = False
    pending_break = False
    for line in lines:
        if line.strip() == "":
            pending_break = True
            numbers.append(paragraph)
            continue
        if pending_break and seen_content:
            paragraph += 1
            pending_break = False
        seen_content = True
        numbers.append(paragraph)
    return numbers


def find_violations(text: str, width: int, *, tabsize: int = 8) -> List[Violation]:
    lines = text.splitlines()
    paragraphs = _paragraph_numbers(lines)
    violations = []
    for line_no, line in enumerate(lines, start=1):
        # A tab-indented line has less room left for its content than the raw
        # width suggests, since the indent itself eats columns once expanded.
        budget = max(width - _indent_width(line, tabsize), 0)
        for word in line.split():
            if len(word) > budget:
                violations.append(
                    Violation(
                        line=line_no,
                        paragraph=paragraphs[line_no - 1],
                        word=word,
                        length=len(word),
                        excess=len(word) - budget,
                    )
                )
    return violations


def check(text: str, width: int, *, lenient: bool = False, tabsize: int = 8) -> Report:
    if width < 1:
        raise ValueError("width must be at least 1")
    if tabsize < 1:
        raise ValueError("tabsize must be at least 1")

    report = Report(
        width=width,
        lenient=lenient,
        tabsize=tabsize,
        violations=find_violations(text, width, tabsize=tabsize),
    )

    if lenient:
        # Mirror textwrap's own defaults so the reported line count matches what
        # a caller would get from calling textwrap.wrap themselves.
        wrapped = []
        for paragraph in text.split("\n\n"):
            wrapped.extend(
                textwrap.wrap(
                    paragraph,
                    width=width,
                    break_long_words=True,
                    break_on_hyphens=True,
                    tabsize=tabsize,
                )
            )
        report.wrapped_line_count = len(wrapped)

    return report
