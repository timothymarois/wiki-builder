+++
title = "Index tables"
subtitle = "a generated table over a named set of pages, with their subtitles and the pages beneath each"
status = "draft"
intent = """
An index table exists so that no writer maintains a list of pages by hand. Where a wiki's index does not
follow its tree, a writer should still be able to say which pages to list and what to show for each, and
adding a page should change the table with no edit to the page holding it.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Syntax", value = "[index] in front matter, {index-table} in the body", cite = "declare" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Columns", value = "field, label or count", note = "one of them each", cite = "columns" },
  { label = "Fields", value = "subtitle, status", cite = "columns" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Refusals", value = "a pattern matching no page, a column naming none or two sources, a total with nothing counted", cite = "refused" },
  { label = "Written", value = "into the page and its markdown copy", cite = "written" },
]
+++

A page can carry a table of other pages that the build writes from those pages
themselves.[^declare] It differs from the member table described on [Families](../checks/families.md) in
what it lists: **a family is a page and its children, and an index is any set of pages a pattern
names**.[^declare] A wiki whose index follows its tree wants the family table; one whose index does not
wants this.[^declare]

## Declaring

`pages` names the pages to list and `columns` what each row shows, and `{index-table}` marks where the
table goes.[^declare] Both go after the last ordinary key, or the keys below them are read as part of
the index.[^declare]

```toml
[index]
pages = "area/*"
total = true
columns = [
  { heading = "Subject", field = "subtitle" },
  { heading = "Pages", count = true },
]
```

A pattern names addresses under `pages`: `*` stops at a `/` and `**` does not, so `area/*` lists the
pages directly under `area` and `area/**` lists everything beneath it.[^glob] Several patterns may be
given as a list.[^declare] A pattern matching no page is refused, because a table that empties itself
after a page moves looks exactly like a table over a set that is empty.[^refused]

## Columns

Each column states a `heading` and **exactly one** of three sources.[^columns]

| Source | Shows |
|---|---|
| `field` | the listed page's own front matter: `subtitle` or `status`[^columns] |
| `label` | the value of that infobox label on the listed page, empty where it states none[^columns] |
| `count` | how many pages sit beneath the listed page, however deep[^columns] |

The first cell of every row is the listed page's title, linked, so no column needs to
name it.[^written] `total = true` adds a totals row summing each counted column, and leaves the other
cells empty, because summing what a page happened to write in a cell would invent a number no page
states.[^total]

**A count is a property of the tree**, which no page states and no infobox could carry, and it is the
value a writer keeping an index by hand gets wrong first: a page added beneath a listed page changes
it.[^columns]

## Writing

The table is written where the marker stands, in the page and in its markdown copy, after the page is
rendered.[^written] A marker the build cannot replace, such as one inside a list or an indented block,
is refused, and so is a marker written more than once, a marker with no `[index]`, and an `[index]` with
no marker.[^refused]

[^declare]: `src/builder/build.py` — `index_table_rows()` reads `pages` and `columns` from a page's
    `index` table, and `INDEX_TABLE` is the marker; `read_front_matter()` parses the front matter as
    TOML, where a table takes every key written under it.
[^glob]: `src/builder/build.py` — `glob_pattern()` writes `*` as an expression that stops at a `/` and
    `**` as one that does not, and `index_pages()` matches every page against each pattern.
[^columns]: `src/builder/build.py` — `index_table_rows()` takes a column's `count` from
    `pages_beneath()`, its `field` from the listed page's front matter, and its `label` from the listed
    page's infobox; `COLUMN_FIELDS` names the front matter a column may show.
[^total]: `src/builder/build.py` — `index_table_rows()` sums each counted column when `index.total` is
    set, leaving every other cell of that row empty.
[^written]: `src/builder/build.py` — `index_table_html()` and `index_table_markdown()` write the table
    with each listed page's title as its first cell, and `write_site()` puts them where the marker's
    paragraph stands.
[^refused]: `src/builder/build.py` — `index_problems()`, called from `check()`.
