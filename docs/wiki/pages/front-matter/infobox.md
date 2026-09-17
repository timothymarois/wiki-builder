+++
title = "Infobox fields"
subtitle = "the settings for a page's infobox"
status = "approved"
intent = """
Infobox fields exist so that a page's reference card is written beside the page it summarizes, with every
row naming the footnote that proves it. A row that cites nothing should never reach a reader unmarked.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Table", value = "[[infobox]]", note = "one for each group", cite = "fields" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Row citation", value = "cite, or missing = true", cite = "check" },
  { label = "Link", value = "outside the wiki only", cite = "link" },
]
+++

An infobox is written in a page's front matter as `[[infobox]]` tables, one for each group, shown in the
order written.[^fields] What an infobox holds is described on [Pages](../pages.md), and the rule that
every row cites on [Citations](../checks/citations.md).

## Fields

| Field | Type | Default | Meaning |
|---|---|---|---|
| `group` | string | empty | the group's heading[^fields] |
| `audience` | string | the page's audience | `"user"` keeps the group in a user build[^group-audience] |
| `rows` | list of tables | none | the group's rows, in the order written[^rows] |
| `label` | string | empty | the row's name[^rows] |
| `value` | string | empty | the row's value, shown as plain text[^rows] |
| `note` | string | none | a short clause shown after the value[^rows] |
| `cite` | string, or list of strings | none | the footnotes the page's text cites for the same fact[^cite] |
| `missing` | true or false | false | marks the row as having no source[^missing] |
| `link` | string | none | an address outside the wiki that the value links to[^link-value] |
| `guaranteed` | string | none | the requirement the row satisfies, never shown[^fields] |

Any other field is ignored.[^fields]

## Validation

A `link` that is not an address outside the wiki stops the build.[^link] `wiki check` lists a row that
cites nothing, and a row citing a footnote no sentence on the page cites.[^check]

| Condition | Message |
|---|---|
| `link` is not an outside address[^link] | `wiki: refunds.md links the infobox row 'Home' to home.md, which is not an address outside the wiki; link a page from the text instead` |
| a row has neither `cite` nor `missing` | `wiki: refunds.md: the infobox row 'Amount' states something and cites nothing; give it cite = "<footnote>" naming a reference the page's text cites, or missing = true if there is none`[^check] |
| a row cites a footnote no sentence cites | `wiki: refunds.md: the infobox row 'Speed' cites [^fast], which no sentence on the page cites; cite it where the page states the same fact`[^check] |

## Example

One group of two rows, the first citing a footnote the page's text cites:[^fields]

```toml
[[infobox]]
group = "Rules"
rows = [
  { label = "Amount", value = "the whole charge", cite = "refund" },
  { label = "Partial refunds", value = "not offered", missing = true },
]
```

[^fields]: `src/builder/build.py` — `render_infobox()` reads `infobox`, and each group's `group`, `audience`
    and `rows`, and each row's `label`, `value`, `note`, `cite`, `missing` and `link`, and never reads
    `guaranteed`; `row_cites()` accepts one footnote or a list.
[^link]: `src/builder/build.py` — `render_infobox()` raises `WikiError` for a `link` that `OUTSIDE_LINK`
    does not match.
[^check]: `src/builder/build.py` — `infobox_problems()`, called from `check()`.
[^group-audience]: `src/builder/build.py` — `render_infobox()` takes a group's `audience` from the page
    when absent, and `visible_to()` keeps the group in a user build only when that is `"user"`.
[^rows]: `src/builder/build.py` — `render_infobox()` shows a group's `rows` in the order written, none when
    absent, each as its `label`, then its `value` escaped as plain text, both empty when absent, then its
    `note` when it has one.
[^cite]: `src/builder/build.py` — `row_cites()` reads `cite` as one footnote or a list, none when absent,
    and `infobox_problems()` refuses one that no sentence on the page cites.
[^missing]: `src/builder/build.py` — `render_infobox()` puts the mark for no source beside a row whose
    `missing` is true, in place of its citations.
[^link-value]: `src/builder/build.py` — `render_infobox()` makes a row's value a link to its `link` when it
    has one.
