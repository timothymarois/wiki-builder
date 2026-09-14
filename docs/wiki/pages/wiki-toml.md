+++
title = "wiki.toml"
subtitle = "the settings file for a wiki"
status = "approved"
intent = """
wiki.toml exists so that a project decides, in one file it owns, what its wiki is called, which pages start
its sidebar and how long a page may be, without the tool guessing any of it. A mistake in it should stop
the build with a sentence saying what to fix.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Name", value = "wiki.toml", cite = "location" },
  { label = "Location", value = "docs/wiki/wiki.toml", note = "inside the wiki folder", cite = "location" },
  { label = "Format", value = "TOML", cite = "location" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Required", value = "site.name, one [[section]]", cite = "read" },
  { label = "Unknown keys", value = "ignored", cite = "read" },
]
+++

`wiki.toml` holds a wiki's name, its sidebar sections, its reading budgets and the release it was last
synced with.[^read] How budgets are enforced is described on [Reading budgets](checks/budgets.md), and how
pages nest beneath a section on [Pages](pages.md).

## Location

The file sits in the wiki folder, `docs/wiki/wiki.toml` unless `--wiki` names another folder, and is read
as TOML.[^location]

## Keys

| Key | Type | Default | Meaning |
|---|---|---|---|
| `site.name` | string | required | the name at the top of the sidebar and in every tab title[^read] |
| `site.tagline` | string | none | a line under the name in the sidebar[^read] |
| `[[section]]` | table, repeated | required, at least one | a group in the sidebar, in the order written[^nav] |
| `section.title` | string | empty | the group's heading[^nav] |
| `section.pages` | list of page names | none | the pages that start a branch, by path without `.md`, such as `checks/budgets`[^nav] |
| `section.categories` | list of category names | none | categories linked from the sidebar[^nav] |
| `budget.page` | whole number | 500 | words a page may use[^budget] |
| `budget.intent` | whole number | 120 | words an intent may use[^intent] |
| `budget.goals` | whole number | 3500 | words the collected goals may use[^goals] |
| `budget.calibrated` | true or false | false | whether the budgets have been measured against a reader[^calibrated] |
| `tool.version` | string | none | the release `wiki sync` recorded[^version] |

Any other key is ignored.[^read] A section that lists nothing gets no heading in the sidebar.[^nav]

## Validation

Every problem below stops the build, except a missing or different `tool.version`, which `wiki check`
lists with the rest.[^version]

| Condition | Message |
|---|---|
| the file is missing | `wiki: there is no wiki.toml in /path/to/notes/docs/wiki`[^read] |
| the file is not valid TOML | `wiki: wiki.toml is unreadable:` and the parser's error[^read] |
| `site.name` is missing or empty | `wiki: wiki.toml has no site.name`[^read] |
| there is no `[[section]]` | `wiki: wiki.toml lists no sections, so nothing would be reachable`[^read] |
| a budget is not a positive whole number | `wiki: wiki.toml: budget.page must be a positive number of words`[^read] |
| a section lists a page that does not exist | `wiki: the navigation lists a page 'nope' that does not exist`[^nav] |
| a section lists a category no approved page carries | `wiki: the navigation lists a category 'Payments' that no page belongs to`[^nav] |
| `tool.version` is missing | ``wiki: wiki.toml does not say which release of the tool these pages were written against; run `wiki sync` ``[^version] |
| `tool.version` names another release | ``wiki: these pages were written against wiki-builder 0.0.9 and this is 0.1.0; run `wiki sync`, then expect any rule added since to be enforced here``[^version] |

## Example

wiki-builder's own wiki runs on the default budgets; two of its sections are shown here.[^example]

```toml
[site]
name = "Wiki Builder"
tagline = "the tool's own wiki"

[[section]]
title = "Start"
pages = ["index", "brief", "goals"]

[[section]]
title = "Reference"
pages = ["commands", "wiki-toml", "front-matter", "pictures-toml"]

[tool]
version = "0.1.0"
```

[^read]: `src/builder/config.py` — `read_config()` reads `site`, `section`, `budget` and `tool` and nothing
    else, and raises the first five messages; `src/builder/build.py` — `render_page()` puts `site.name`
    in the sidebar and the tab title, and `site.tagline` beneath the name.
[^location]: `src/builder/config.py` — `CONFIG`, read from the wiki folder by `read_config()` with
    `tomllib`; `src/builder/build.py` — `wiki_of()` defaults that folder to `docs/wiki`.
[^nav]: `src/builder/build.py` — `render_nav()` writes each section's title over its pages and categories
    in order, skips a section with neither, and raises for a page or category that does not exist.
[^budget]: `src/builder/config.py` — `DEFAULT_BUDGET`, under which `read_config()` merges `[budget]`.
[^version]: `src/builder/build.py` — `version_problems()`, called from `check()`; `src/builder/config.py` —
    `record_version()`, called by `wiki sync`, writes `tool.version`.
[^example]: `docs/wiki/wiki.toml` — no `[budget]` table.
[^intent]: `src/builder/config.py` — `DEFAULT_BUDGET` sets 120; `src/builder/build.py` — `read_pages()`
    refuses an intent that runs over it.
[^goals]: `src/builder/config.py` — `DEFAULT_BUDGET` sets 3500; `src/builder/build.py` —
    `budget_problems()` refuses collected goals that run over it.
[^calibrated]: `src/builder/config.py` — `DEFAULT_BUDGET` sets it false; `src/builder/build.py` — `report()`
    calls the budgets provisional on every run until it is true.
