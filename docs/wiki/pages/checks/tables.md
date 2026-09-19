+++
title = "Tables"
subtitle = "a table the renderer will not draw, served to a reader as a paragraph of pipes"
status = "draft"
categories = ["Refusals"]
intent = """
The tables check exists so that a page cannot pass its gate while rendering as raw pipes. A reader should
never meet a table that fell apart, and the writer should be told which row broke it and what to do,
rather than discovering it on the published page.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Syntax", value = "markdown table", cite = "source" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Refusals", value = "a row carrying text after its last pipe, and a row whose cells do not match its header", cite = ["trailing", "cells"] },
  { label = "Scope", value = "every table in a page's markdown", cite = "source" },
  { label = "Exceptions", value = "code samples, and the tables the build writes", cite = ["fenced", "written"] },
  { label = "Enforcement", value = "listed with every other problem", cite = "order" },
  { label = "Clearing", value = "give the row its cells", cite = ["trailing", "cells"] },
]
+++

A markdown table falls apart on one bad row, and **what reaches the reader is a paragraph of raw
pipes**.[^trailing][^cells] Every other check reads the table from the markdown, where its rows are still
rows, so a broken table cites its sources correctly and passes them all.[^blind] This check reads the same
markdown the renderer does and refuses what the renderer will not draw.[^source] The citation rules those
rows are held to are described on [Citations](citations.md).

## Refusals

### Trailing text

A row that begins with a pipe and does not end with one is refused.[^trailing] The renderer drops that row
out of the table and serves it as a paragraph, leaving a table with a header and nothing under it — which
is how a citation or a red mark written past the closing pipe breaks a page.[^trailing]

```text
wiki: checks/tables.md:31: the table row “| a | b | {missing}” carries text after its last |, so the renderer drops it out of the table and serves the table as a paragraph of pipes; move what follows the last | into a cell
```

### Cell count

A row that does not divide into as many cells as its header is refused.[^cells] **A ragged row does not
lose only itself**: the renderer refuses the whole table, header and every other row with it.[^cells] Cells
are divided on every pipe the writer did not escape, and a pipe inside backticks still divides one, because
the renderer divides there too.[^cells]

```text
wiki: checks/tables.md:31: the table row “| e |” has 1 cell where its header has 2, so the renderer refuses the whole table and serves it as a paragraph of pipes; give the row 2 cells, one for each column
```

### Silence

A table that is drawn with fewer rows than the markdown wrote, for a reason neither rule above names, is
refused where it starts.[^backstop]

## Scope

Every table in a page's markdown is read: a line holding a pipe, followed by the dashed line, and the rows
under it up to the first blank line.[^source]

## Exceptions

A table inside a code sample is not checked, because it is the thing itself rather than a table the page
draws.[^fenced] The tables the build writes — the health page's, and a family's member table — are written
after the page is rendered, and the check renders each page's own markdown, so neither is
counted.[^written]

## Enforcement

Each problem is listed with every other problem `wiki check` finds, before the citation checks, because a
table the renderer threw away still cites correctly and their silence is what needs
explaining.[^order]

## Clearing

A refused row passes once it has one cell for each column and nothing after its last pipe.[^trailing][^cells]

[^source]: `src/builder/build.py` — `source_tables()` reads each header line followed by `TABLE_SEPARATOR`
    and the rows under it, blanking fenced code and footnote definitions so every line keeps its number.
[^trailing]: `src/builder/build.py` — `table_problems()` refuses a row that starts with a pipe and does not
    end with one.
[^cells]: `src/builder/build.py` — `table_problems()` compares `table_cells()` of each row with its
    header's, and `CELL_EDGE` divides on every pipe not preceded by a backslash.
[^backstop]: `src/builder/build.py` — `table_problems()` renders the page's markdown with `make_markdown()`
    and counts the `<tr>` inside `RENDERED_BODY` against the rows written.
[^blind]: `src/builder/build.py` — `statements()` reads a block starting with a pipe row by row, whatever
    the renderer made of it.
[^fenced]: `src/builder/build.py` — `source_tables()` blanks `FENCED` before reading.
[^written]: `src/builder/build.py` — `health_html()` and `family_table_html()` write their tables in
    `write_site()`, after `markdown()` has run.
[^order]: `src/builder/build.py` — `check()` calls `table_problems()` before `uncited_problems()`.
