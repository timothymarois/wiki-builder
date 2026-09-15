+++
title = "Markdown syntax"
subtitle = "text, links, code, tables, citations and the missing mark"
status = "approved"
intent = """
The markdown syntax page exists so that a writer finds every piece of markdown a page can use, and what
the site draws from it, in one place. A writer should learn how to link, cite and show code without
reading the source of another page.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Parser", value = "mistune 3.3.4", cite = "parser" },
  { label = "Extensions", value = "footnotes, tables, strikethrough", cite = "parser" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Citation", value = "a markdown footnote", cite = "cite" },
  { label = "No source", value = "a red mark", cite = "missing" },
  { label = "Page link", value = "the page's file, relative to this one", cite = "links" },
  { label = "Contents box", value = "second- and third-level headings", cite = "headings" },
]
+++

A page is written in markdown, with three extensions switched on: footnotes, tables and
strikethrough.[^parser] Paragraphs, bold, italics, lists and quotes are drawn as markdown draws them, and
`~~text~~` strikes text through.[^parser] Settings above the markdown are described on
[Front matter](../front-matter.md), drawings on [Diagrams](diagrams.md), and pictures on
[Pictures](pictures.md).

Second- and third-level headings are numbered in the page's contents box, and fourth- to sixth-level
headings are drawn without a number.[^headings] What a heading may say is described on
[Headings](../checks/headings.md).

## Links

A page links to another page by that page's file, written relative to its own, and the site turns the link
into the page's address.[^links] A link to a page the wiki does not have is drawn red, and `wiki check`
refuses it.[^dead] A link to any other file in the repository becomes a path from the page to that
file.[^links] A link to an address outside the wiki opens in a new tab and ends in an arrow.[^outside]

```markdown
Drawings are described on [Diagrams](diagrams.md), and the check on [wiki check](../commands/check.md).
```

## Code

Code inside a sentence is written between backticks.[^parser] A block of code is written between fences
with its language named, and the site gives it a Copy button.[^copy] A block whose language is `mermaid`
is drawn as a diagram instead, as [Diagrams](diagrams.md) describes.

## Tables

A table is written as a markdown table and drawn as a wiki table, which scrolls inside its own frame on a
screen narrower than it.[^table] Every row cites in at least one of its cells, as
[Citations](../checks/citations.md) describes.

## Citations

A citation is a markdown footnote: a mark such as `[^expiry]` after the claim, and a line at the foot of
the page that opens with the same mark and names the code.[^cite] The site numbers each mark in the order
the page first uses it, draws it as a bracketed number, and lists the entries under a References heading at
the foot.[^cite] A claim with nothing to cite carries `{missing}`, drawn as a red mark, and inside code the
mark is shown as written.[^missing] What a citation must name is described on
[Citations](../checks/citations.md).

```markdown
A session ends thirty minutes after its last request.[^expiry]

[^expiry]: `src/session/expiry.py` — `sweep()`.
```

[^parser]: `src/builder/build.py` — `make_markdown()` builds a `mistune` parser with the `footnotes`,
    `table` and `strikethrough` plugins; `pyproject.toml` pins `mistune==3.3.4`.
[^headings]: `src/builder/build.py` — `HEADING` matches `h2` and `h3` only, which `number_headings()`
    numbers and `render_contents()` lists.
[^links]: `src/builder/build.py` — `rewrite_references()` turns a link to a `.md` file inside the pages
    folder into that page's address, and any other relative link into a path from the page to the file.
[^dead]: `src/builder/build.py` — `rewrite_references()` marks a link to a page the wiki does not have
    with `NEW_PAGE`, and `dead_link_problems()` refuses it.
[^outside]: `src/builder/build.py` — `rewrite_references()` adds `OUTSIDE` to a link matching
    `OUTSIDE_LINK`; `src/builder/assets/wiki.css` draws the arrow on `a.ext`.
[^copy]: `src/builder/build.py` — `write_site()` wraps each code block from the markdown in `srcbox` with a
    Copy button.
[^table]: `src/builder/build.py` — `write_site()` wraps each table in `wt` and gives it the class `w`;
    `src/builder/assets/wiki.css` draws both.
[^cite]: `src/builder/build.py` — `footnote_reference()` draws `CITATION` with the number the footnotes
    plugin gives a footnote on its first use, and `footnote_item()` and `footnote_block()` list the entries
    under References.
[^missing]: `src/builder/build.py` — `write_site()` replaces `MISSING` with `MISSING_CITATION` outside
    `CODE_HTML` only.
