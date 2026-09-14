+++
title = "Checks"
subtitle = "every reason the wiki is not fit to read"
status = "approved"
intent = """
The checks exist so that a wiki read instead of the code cannot quietly stop being true. Each one refuses
a way documentation has been seen to rot, and together they should name every problem at once, in
sentences a person can act on.
"""

[[infobox]]
group = "Exit"
rows = [
  { label = "Nothing wrong", value = "0" },
  { label = "A problem found", value = "1" },
  { label = "No wiki there", value = "2" },
]
+++

`wiki check` builds the site in a temporary folder and lists **every problem at once**, not only the
first.[^check] Each check was added after the failure it prevents had actually happened.{missing}

## Refusals

| Refused | Described on |
|---|---|
| A paragraph that cites nothing, or a reference to a document[^cited] | [Citations](checks/citations.md) |
| A heading that asks a question or rates its contents[^headings] | [Headings](checks/headings.md) |
| A page longer than its budget[^budget] | [Reading budgets](checks/budgets.md) |
| A picture whose subject has changed[^pictures] | [Pictures](checks/pictures.md) |
| A page edited since its date was recorded[^dates] | [Site](site.md) |
| A wiki written against a different release of the tool[^version] | [Skill](skill.md) |

## Stoppages

Some problems **stop the build** instead of joining the list: a page with no intent, a page that nobody
can reach, a sidebar naming a page that does not exist, or a picture with no record.[^stop] When that
happens, only that one problem is reported, as a single sentence, and the command exits with 1.[^caught]

[^check]: `src/builder/build.py` — `check()` builds into a temporary folder
    and gathers every problem; `src/builder/cli.py` — `main()` prints them
    and returns 1 if there are any, and 2 when there is no wiki.
[^cited]: `src/builder/build.py` — `uncited_problems()` and
    `citation_problems()`.
[^headings]: `src/builder/build.py` — `heading_problems()`.
[^budget]: `src/builder/build.py` — `budget_problems()`.
[^pictures]: `src/builder/build.py` — `picture_problems()`.
[^dates]: `src/builder/build.py` — `date_problems()`.
[^version]: `src/builder/build.py` — `version_problems()`.
[^stop]: `src/builder/build.py` — `read_pages()`, `write_site()`,
    `render_nav()` and `rewrite_references()` raise `WikiError`.
[^caught]: `src/builder/cli.py` — `main()` catches `WikiError`, prints it, and returns 1.
