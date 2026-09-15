+++
title = "Families"
subtitle = "headings and infobox labels outside a declared family's layout, and members the parent does not link"
status = "approved"
categories = ["Refusals"]
intent = """
The families check exists so that pages about things of one kind keep their approved layout, and a
reader who has read one member knows where to look on every other. It should be easy to fix: each refusal
names the member, the heading or label, and both ways to make it pass.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Syntax", value = "[family] in a parent's front matter", cite = "declare" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Refusals", value = "an unlisted heading or label, headings out of order, an unlinked member", cite = ["headings", "labels", "links"] },
  { label = "Scope", value = "the direct children of a page declaring a family", cite = "scope" },
  { label = "Exceptions", value = "a listed heading or label left out", cite = "exceptions" },
  { label = "Enforcement", value = "listed with every other problem", cite = "enforcement" },
  { label = "Clearing", value = "rename on the member, or add to the parent's list", cite = "clearing" },
]
+++

A parent page opts in by declaring its family's layout in its front matter, and `wiki check` then refuses a
member that strays from it.[^declare] How a layout is chosen is described on [Skill](../skill.md), and the
report that finds families not yet declared on [wiki families](../commands/families.md).

```toml
[family]
headings = ["Usage", "Options", "Arguments", "Output", "Exit codes"]
labels = ["Command", "Arguments", "Options", "Output folder", "Files written"]
table = ["Arguments", "Options", "Files written"]
```

When the family names `table`, the build writes the parent's member table where `{family-table}` stands on
its own line: one row per member, linked, with the member's infobox value for each label, and an empty cell
where the member states none.[^table]

## Refusals

### Headings

A member's second-level heading that `headings` does not list is refused, and so is a heading that comes
before one the list puts first.[^headings]
```text
wiki: commands/serve.md: the heading 'Flags' is not in the family layout on commands.md; rename it to one of Usage, Options, Arguments, Output, Exit codes, or add it to family.headings there
wiki: commands/sync.md: the heading 'Output' comes before 'Options', but family.headings on commands.md lists 'Options' first; order the headings as it lists them
```

### Infobox labels

A member's infobox label that `labels` does not list is refused, whichever group holds it.[^labels]
```text
wiki: commands/check.md: the infobox label 'Name' is not in the family layout on commands.md; rename it to one of Command, Arguments, Argument, Options, Output folder, Default port, Files written, Success, Problems, Misuse, or add it to family.labels there
```

### Parent links

A member that the parent's text does not link is refused, so the parent lists every member.[^links] A parent
with both `table` and `{family-table}` links every member through the table the build writes.[^links]
```text
wiki: commands.md does not link commands/audit.md, a member of its family; link every member from the parent, such as in a table of the members
```

### Table

A `table` label that `labels` does not list is refused, and so are a `table` with no `{family-table}` on the
parent, and a `{family-table}` with no `table` or on a page with no family.[^tablecheck]
```text
wiki: commands.md: family.table lists 'Flags', which family.labels does not; add it to family.labels, or take it out of family.table
wiki: commands.md declares family.table but has no {family-table}; put {family-table} on its own line where the member table goes
wiki: commands.md has {family-table} but declares no family.table; add table = [...] under [family], naming the infobox labels the member table compares
wiki: brief.md has {family-table} but declares no [family]; declare the family's layout, with table naming the infobox labels its member table compares
```

A `{family-table}` the build cannot replace, such as one inside a list or an indented block, is refused, and so
is a marker written more than once.[^tablecheck]
```text
wiki: commands.md has {family-table} where the build cannot write the table, such as in a list, a quote or an indented block; put it on a line of its own, with a blank line before and after
wiki: commands.md has {family-table} 2 times; keep one, where the member table goes
```

### Declaration

A `family` that is not a table, and a `headings` or `labels` that is empty or is not a list of names, are
refused, and the family's members are not checked until each is fixed.[^declare]
```text
wiki: checks.md: family.headings must list the headings every member of the family may use, such as headings = ["Usage", "Output"], or leave family.headings out to check no headings
```

## Scope

The check reads the direct children of each page that declares `[family]`: their second-level headings
outside code samples, compared as the page shows them without a closing run of `#` or backticks, and every
infobox label in every group.[^scope] A grandchild belongs to its own
parent's family, when that parent declares one.[^scope]

## Exceptions

A member may leave out any heading or label its family lists, so a section that does not apply is not
written.[^exceptions] A key the family does not declare is not checked, and a parent that declares no family
is not checked at all.[^exceptions]

## Enforcement

Each problem is listed with every other problem `wiki check` finds, and never stops the build.[^enforcement]

## Clearing

A refused member passes once its heading or label is renamed to one the family lists, or once the name is
added to the list on the parent for every member.[^clearing] A missing link is cleared by linking the member
from the parent's text, such as from a table of the members.[^links]

[^declare]: `src/builder/build.py` — `family_problems()` reads `headings` and `labels` from a page's `family`
    table, reports a `family` that is not a table and a list that is empty or holds anything but names, and
    skips that family's members.
[^headings]: `src/builder/build.py` — `family_problems()` compares each member's `section_headings()` with
    `headings`, refusing a heading the list does not hold and one placed before a heading the list puts
    first.
[^labels]: `src/builder/build.py` — `family_problems()` refuses each infobox row, in any group, whose label
    `labels` does not hold.
[^links]: `src/builder/build.py` — `family_problems()` resolves each link in the parent's text with
    `linked_page()`, refuses a member none of them reaches, and counts every member linked when the parent
    has both `table` and a line `FAMILY_TABLE_LINE` matches.
[^table]: `src/builder/build.py` — `family_table_rows()` takes each written member's infobox value for every
    label in `table`, empty where the member states none; `write_site()` puts `family_table_html()` where the
    parent's `{family-table}` paragraph stands, and `family_table_markdown()` into its markdown copy.
[^tablecheck]: `src/builder/build.py` — `family_problems()` refuses a `table` label outside `labels`, a
    `table` with no marker, and a marker with no `table` or no `family`; it renders the parent with
    `make_markdown()` and refuses a marker that is not a paragraph of its own, or is one more than once.
[^scope]: `src/builder/build.py` — `family_problems()` checks `children_of()` the declaring page only, and
    `section_headings()` reads `SECTION_HEADING` outside `FENCED` code, dropping a closing run of `#` and
    every backtick.
[^exceptions]: `src/builder/build.py` — `family_problems()` checks only the headings and labels a member
    uses, checks a key only when the family declares it, and skips a page with no `family`.
[^enforcement]: `src/builder/build.py` — `check()` adds `family_problems()` to the problems it lists.
[^clearing]: `src/builder/build.py` — `family_problems()` names the family's list and the parent page in
    every refusal it makes.
