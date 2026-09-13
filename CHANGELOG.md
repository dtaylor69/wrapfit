# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

Everything below has landed on `main` but hasn't been tagged or uploaded
to PyPI yet.

### Added

- Core check: does any whitespace-delimited word exceed a given column
  width, at a given text.
- `--lenient` to allow long words to be broken, reporting the resulting
  wrapped line count instead of failing.
- `--tabsize` so leading tabs count against a line's width budget.
- Directory mode: pass a directory instead of a file to check every
  UTF-8 text file under it, skipping anything unreadable or binary.
- `--json` for a single-line, machine-readable report (a list of
  per-file reports in directory mode).
- Per-paragraph reporting alongside line numbers, so a violation stays
  easy to locate even after the text is rewrapped and line numbers shift.
- Packaging metadata and a `py.typed` marker, in preparation for a
  PyPI release.
