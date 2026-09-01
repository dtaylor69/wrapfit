"""Core logic: does any word in a text exceed a given wrap width."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Violation:
    line: int
    word: str
    length: int
    excess: int


@dataclass
class Report:
    width: int
    lenient: bool
    violations: List[Violation] = field(default_factory=list)
    wrapped_line_count: Optional[int] = None

    @property
    def ok(self) -> bool:
        # In lenient mode a long word is a known, accepted outcome, not a failure.
        return self.lenient or not self.violations


def find_violations(text: str, width: int) -> List[Violation]:
    violations = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for word in line.split():
            if len(word) > width:
                violations.append(
                    Violation(line=line_no, word=word, length=len(word), excess=len(word) - width)
                )
    return violations


def check(text: str, width: int, *, lenient: bool = False) -> Report:
    if width < 1:
        raise ValueError("width must be at least 1")

    report = Report(width=width, lenient=lenient, violations=find_violations(text, width))

    if lenient:
        # Mirror textwrap's own defaults so the reported line count matches what
        # a caller would get from calling textwrap.wrap themselves.
        wrapped = []
        for paragraph in text.split("\n\n"):
            wrapped.extend(
                textwrap.wrap(paragraph, width=width, break_long_words=True, break_on_hyphens=True)
            )
        report.wrapped_line_count = len(wrapped)

    return report
