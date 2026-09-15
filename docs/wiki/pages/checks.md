+++
title = "Checks"
subtitle = "every refusal wiki check makes, grouped by kind"
status = "approved"
intent = """
The checks exist so that a wiki read instead of the code cannot quietly stop being true. Each one refuses
a way documentation has been seen to rot, and together they should name every problem at once, in
sentences a person can act on.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki check", cite = "check" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "check" },
  { label = "Problems", value = "1", cite = "check" },
  { label = "Misuse", value = "2", note = "such as no wiki at the path", cite = "check" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Reporting", value = "every problem at once", cite = "check" },
  { label = "Build stoppage", value = "that problem alone", cite = "caught" },
]
+++

`wiki check` builds the site in a temporary folder and lists **every problem at once**, not only the
first.[^check] It exits with 0 for a sound wiki, 1 when it finds a problem, and 2 when it is misused,
such as pointed where there is no wiki.[^check] The same check runs on every push and pull request
through [Continuous integration](continuous-integration.md). A check proves that a sentence cites
something, not that the citation is true; an agent checks that from the [Review prompt](review-prompt.md).

## Order

Every check runs before the result is decided, so one problem never hides another.[^check][^caught]

```mermaid
flowchart LR
  accTitle: wiki check run
  accDescr: wiki check builds the site in a temporary folder. A page that cannot be built stops it with exit code 1; otherwise it runs every check, lists every problem and every claim with no source, and exits 1 if there is a problem or 0 if not.
  run(["wiki check run"]) --> build["Build the site in a temporary folder"] --> built{"Every page built?"}
  built -- "Yes" --> checks["Run every check"] --> list["List problems and unsourced claims"]
  built -- "No" --> stopped(["Stopped with the reason, exit 1"])
  list --> any{"Any problem?"}
  any -- "Yes" --> failed(["Exit 1"])
  any -- "No" --> passed(["Exit 0"])
```

## Refusals

| Refused | Described on |
|---|---|
| A sentence that cites nothing, or a reference to a document[^cited] | [Citations](checks/citations.md) |
| An infobox row that cites nothing[^rows] | [Citations](checks/citations.md) |
| A heading that asks a question, rates its contents or points at the page[^headings] | [Headings](checks/headings.md) |
| A name or sentence that points at the page, hides who acts, quotes the owner or carries no fact[^wording] | [Wording](checks/wording.md) |
| A link to a wiki page that does not exist[^deadlinks] | [Site](site.md) |
| A page longer than its budget[^budget] | [Reading budgets](checks/budgets.md) |
| A picture whose subject has changed[^pictures] | [Pictures](checks/pictures.md) |
| A page edited since its date was recorded[^dates] | [Site](site.md) |
| A wiki written against a different release of the tool[^version] | [Delivery](skill/delivery.md) |
## Stoppages

Some problems **stop the build** instead of joining the list, such as a missing `wiki.toml` or `goals.md`,
a page with no title or intent, a page that no reader can reach, a sidebar naming a page that does not exist
or a picture with no record.[^stop] When that happens, only that one problem is reported, as a single
sentence, and the command exits with 1.[^caught]

[^check]: `src/builder/build.py` — `check()` builds into a temporary folder and gathers every problem;
    `src/builder/cli.py` — `run()` prints them and returns 1 if there are any and 0 if not, and `main()`
    returns 2 when there is no wiki.
[^cited]: `src/builder/build.py` — `uncited_problems()` and `citation_problems()`.
[^rows]: `src/builder/build.py` — `infobox_problems()`.
[^headings]: `src/builder/build.py` — `heading_problems()`.
[^wording]: `src/builder/build.py` — `pointing_problems()`, `vague_actor_problems()`,
    `attribution_problems()` and `empty_word_problems()`.
[^deadlinks]: `src/builder/build.py` — `dead_link_problems()`.
[^budget]: `src/builder/build.py` — `budget_problems()`.
[^pictures]: `src/builder/build.py` — `picture_problems()`.
[^dates]: `src/builder/build.py` — `date_problems()`.
[^version]: `src/builder/build.py` — `version_problems()`.
[^stop]: `src/builder/config.py` — `read_config()`; `src/builder/build.py` — `read_pages()`,
    `write_site()`, `render_nav()`, `render_infobox()`, `rewrite_references()` and `subject_digest()`
    raise `WikiError`.
[^caught]: `src/builder/cli.py` — `main()` catches `WikiError`, prints it, and returns 1.
