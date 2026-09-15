+++
title = "wiki families"
subtitle = "list the child pages that share no declared layout"
status = "approved"
intent = """
wiki families exists so that a writer or an agent can see child pages that are shaped on their own, side by
side, before deciding whether they are one family. It should report and decide nothing, because whether
pages are things of one kind is a person's judgement.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki families", cite = "usage" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Files written", value = "none", cite = "report" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", note = "whatever the report finds", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki families` lists every parent page with two or more children that declares no `[family]` layout, with
each child's second-level headings, then every child whose title repeats a word of its parent's title, then
the totals, and writes nothing.[^report] How a family is declared and checked is described on
[Families](../checks/families.md).

## Usage

It takes only the options every command shares.[^usage]
```sh
wiki families [-h] [--root ROOT] [--wiki WIKI]
wiki families
```

## Output

A child's headings are listed in order, leaving out any shown in a code sample.[^report] A title repeats its
parent's when a word of more than three letters, singular or plural, is in both.[^report] On wiki-builder's
own wiki, where the Checks and Commands pages declare families:[^report]
```text
wiki: pages.md declares no family for its 4 children
wiki:   pages/diagrams.md: Writing, Drawing, Citations, Copies
wiki:   pages/markdown.md: Links, Code, Tables, Citations
wiki:   pages/pdfs.md: Links, Publishing, Viewer
wiki:   pages/pictures.md: Text pictures, Infobox picture, Lightbox
wiki: site.md declares no family for its 2 children
wiki:   site/agent-markdown.md: Copies, Index, Audiences
wiki:   site/layout.md: Sidebar, Article, Footer, Narrow screens
wiki: 2 families declared; 2 parents with two or more children declaring none
```

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | the report is printed, whatever it finds[^exit] | `wiki: 2 families declared; 2 parents with two or more children declaring none` |
| `1` | a page's front matter cannot be read[^exit] | `wiki: refunds.md has unreadable front matter:` and the parser's error |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |

[^report]: `src/builder/cli.py` — `run()` prints each line `families_report()` returns; `src/builder/build.py`
    — `families_report()` lists each parent of two or more `children_of()` it with no `family`, their
    `section_headings()`, each child title sharing a word longer than three letters with its parent's, and
    the totals, and writes nothing.
[^usage]: `src/builder/cli.py` — `main()` gives `families` only the shared options.
[^exit]: `src/builder/cli.py` — `run()` returns 0 after the report; `main()` returns 1 for a `WikiError`, which
    `read_front_matter()` in `src/builder/build.py` raises, and 2 with no wiki; argparse exits 2 on an option
    it does not know.
