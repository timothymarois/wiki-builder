+++
title = "PICTURES.toml"
subtitle = "the record of what each picture shows"
status = "approved"
intent = """
PICTURES.toml exists so that every picture on a page says what it depicts, and the tool can tell when that
has changed. A picture should never reach a page without a record.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Name", value = "PICTURES.toml", cite = "read" },
  { label = "Location", value = "docs/wiki/images/PICTURES.toml", note = "inside the wiki folder", cite = "read" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Unrecorded picture", value = "build stopped", cite = "missing" },
  { label = "Rewritten by", value = "wiki bless", cite = "write" },
]
+++

`PICTURES.toml` holds one table for each picture in the wiki's `images` folder, naming the files in the
project that the picture shows.[^read] How the check uses it is described on [Pictures](checks/pictures.md),
and how a changed picture is cleared on [wiki bless](commands/bless.md).

## Location

The file sits in the `images` folder inside the wiki folder, and is read as TOML; without it, no page can
show a picture.[^read]

## Keys

Each table is named for a picture's file name, such as `["refund-flow.svg"]`.[^read]

| Key | Type | Default | Meaning |
|---|---|---|---|
| `depicts` | list of paths | none | the files or folders the picture shows, relative to the project; with none, the picture is never checked[^keys] |
| `digest` | string | none | the fingerprint of those files, written by `wiki bless`; with none, the picture is never checked[^bless][^keys] |
| `blessed` | string | none | the reason last given to `wiki bless`[^bless] |
| `made` | string | none | kept when `wiki bless` rewrites the file, and read by nothing else[^write] |

`wiki bless` rewrites the whole file, keeping only these four keys and replacing every comment with its
own header.[^write]

## Validation

Every problem below stops the build or the check, except a changed subject, which `wiki check` lists with
the rest.[^missing]

| Condition | Message |
|---|---|
| a page shows a picture with no table | `wiki: refunds/ shows flow.svg, which has no entry in PICTURES.toml`[^missing] |
| a table names a file that is not in `images` | `wiki: PICTURES.toml lists refund-flow.svg, which is not in /path/to/notes/docs/wiki/images`[^missing] |
| `depicts` names a path that is not in the project | `wiki: a picture says it shows src/gone.py, which is not in this project`[^missing] |
| `depicts` names a folder holding no files | `wiki: a picture says it shows src/empty, which holds no files`[^missing] |
| the depicted files changed since `digest` was written | ``wiki: refund-flow.svg shows src/refunds.py, which has changed since the picture was made; re-render it, or `wiki bless refund-flow.svg "<why the picture is still true>"` ``[^check] |

## Example

The record of the picture on [Pages](pages.md), as `wiki bless` last wrote it.[^example]

```toml
["page-anatomy.svg"]
digest = "sha256:f9c4cbd3da17f352546b89d1b1ae49aae89570f268a71355a6ee094c56aefa6a"
depicts = ["src/builder/assets/template.html"]
blessed = "the template gained a placeholder for the diagram script at the foot of the page; nothing a reader sees moved"
```

[^read]: `src/builder/build.py` — `read_ledger()` reads `LEDGER` from the `images` folder inside the wiki
    folder, and returns an empty record when the file is missing.
[^keys]: `src/builder/build.py` — `picture_problems()` skips a table with no `depicts` or no `digest`, and
    `subject_digest()` fingerprints each path in `depicts` from the project root.
[^write]: `src/builder/build.py` — `write_ledger()`, called by `bless()`, writes its own header and, for
    each picture, only `made`, `digest`, `depicts` and `blessed`.
[^missing]: `src/builder/build.py` — `rewrite_references()` and `render_infobox()` refuse a picture with no
    table, `write_site()` a table with no file, and `subject_digest()` a path that is missing or empty.
[^check]: `src/builder/build.py` — `picture_problems()`, called from `check()`.
[^example]: `docs/wiki/images/PICTURES.toml` — the `page-anatomy.svg` table.
[^bless]: `src/builder/build.py` — `bless()` sets `digest` to what `subject_digest()` makes of `depicts`
    now and `blessed` to the reason given, then calls `write_ledger()`.
