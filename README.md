# wrapfit

Checks whether a block of text can be wrapped to a given column width
without breaking any word in half.

## The problem

`textwrap.wrap` and most editors' "wrap at column N" features will
silently break a word that's longer than the target width, splitting
it wherever the width runs out. For ordinary prose that's usually
fine. For a URL, a commit hash, a file path, or an identifier sitting
in a code comment, it corrupts the thing you were writing — and it's
easy not to notice until someone tries to click the broken link.

wrapfit answers one question: at width N, does anything in this text
have to be broken? By default that's treated as an error. If you
actually want the text broken to fit (matching plain `textwrap`
behavior), say so explicitly with `--lenient`.

## Usage

Check a file:

    $ wrapfit README.md --width 72
    fits: every word fits within 72 columns

Catch a word that won't fit:

    $ cat notes.txt
    see the report at
    https://example.com/reports/very-long-quarterly-summary-2026
    for details.

    $ wrapfit notes.txt --width 50
    line 2: too long — 'https://example.com/reports/very-long-quarterly-summary-2026' is 60 columns, 10 over width

    1 word(s) exceed 50 columns. Widen the column, shorten the word,
    or pass --lenient to allow breaking it.

    $ echo $?
    1

Allow it to break instead of failing:

    $ wrapfit notes.txt --width 50 --lenient
    line 2: would be broken — 'https://example.com/reports/very-long-quarterly-summary-2026' is 60 columns, 10 over width
    lenient wrap would produce 4 line(s)

    $ echo $?
    0

Read from stdin, useful for checking things like commit message
bodies before they're written:

    $ git log -1 --format=%B | wrapfit --width 72

Account for tab-indented input, such as a code comment:

    $ printf '\t\t\tsee-the-attached-configuration-file.yaml\n' | wrapfit --width 40 --tabsize 4
    line 1: too long — 'see-the-attached-configuration-file.yaml' is 40 columns, 12 over width

    1 word(s) exceed 40 columns. Widen the column, shorten the word,
    or pass --lenient to allow breaking it.

The word itself is exactly 40 columns, but three tabs at a tab size
of 4 already use 12 of those, leaving only 28 — so the reported
excess is relative to what's actually left on the line, not the raw
width. `--tabsize` defaults to 8, matching `textwrap` and most
terminals.

## Exit codes

- `0` — text fits, or `--lenient` was given so any long words were
  accepted as broken.
- `1` — a word exceeds the width and `--lenient` was not given.
- `2` — usage error (bad file path, invalid width).

## Design notes

- Strict by default is the point of the tool: silently accepting
  broken tokens defeats the purpose of checking in the first place.
- "Word" means a whitespace-delimited token in the input, matching
  how `textwrap` decides what counts as breakable.
- A line's leading tabs count against its width budget once expanded,
  so an indented word is checked against the columns actually left on
  the line, not the full target width.
- No third-party dependencies — standard library only.

## Status

Early. The CLI, the two checks above (strict, lenient), and tab-aware
indentation are the whole tool right now.
