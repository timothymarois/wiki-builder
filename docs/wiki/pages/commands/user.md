+++
title = "wiki user"
subtitle = "build only the pages marked for users into a folder"
status = "approved"
intent = """
wiki user exists so that the pages meant for people outside the project can be handed to them with
nothing internal left in. It should never carry a reference, a missing-source mark or a page's source.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki user", cite = "usage" },
  { label = "Arguments", value = "OUT", cite = "usage" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Output folder", value = "OUT", note = "relative to the working directory", cite = "usage" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Files written", value = "OUT, UPDATED.toml", cite = ["user", "dates"] },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki user` builds only the pages marked for users into the folder it is given, with every
reference, red mark and Source tab removed.[^user] A draft marked for users is built too, under its draft
banner.[^draft] How a page is marked for users is described on
[Front matter](../front-matter.md).

## Usage

The folder is required.[^usage]
```sh
wiki user [-h] [--root ROOT] [--wiki WIKI] OUT
wiki user readers
```

## Arguments

| Argument | Meaning |
|---|---|
| `OUT` | the folder to build into, relative to the working directory; empty, or an earlier build[^usage] |

## Output

It prints a line for each page it built, then the same closing lines as `wiki build`.[^output] **The
totals of sources and marks, and the list of drafts, count every page in the wiki**, not only those it
built.[^output] Like `wiki build`, it records each changed page's date in `UPDATED.toml`.[^dates] With
`site.url` set in `wiki.toml`, it also writes `sitemap.xml` into `OUT`, listing every approved page it
built and every category page at its full address; without it, a closing line names the
setting.[^sitemap] On a
wiki of three pages, one of them marked for users, with the folder being wherever the command
ran:[^output]
```text
wiki: refunds                            22 words    1 cited    1 missing
wiki: 1 source cited, 1 claim marked as having no source
wiki: the collected goals read in 17 words
wiki: these budgets are PROVISIONAL -- 500 words a page, 3500 for the collected goals. What this project's readers actually read has not been measured; until it is, the numbers are a guess that happens to be enforced. Set budget.calibrated in wiki.toml once it is.
wiki: 1 page written to /path/to/notes/readers
wiki: set site.url in wiki.toml to write sitemap.xml
```

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | the user build is written[^exit] | `wiki: 1 page written to /path/to/notes/readers` |
| `1` | a problem stops the build[^exit] | the problem |
| `2` | `OUT` is not empty and was not made by the tool[^exit] | `wiki: /path/to/notes/taken is not empty and was not written by this tool; remove it yourself if you meant to replace it` |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |
| `2` | `OUT` is missing[^exit] | `wiki user: error: the following arguments are required: OUT` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |

[^user]: `src/builder/cli.py` — `run()` builds with audience `"user"`; `src/builder/build.py` —
    `visible_to()`, `for_user()` and `with_source` in `write_site()`.
[^draft]: `src/builder/build.py` — `write_site()` writes every page `visible_to()` the audience, whatever
    its `status`, and `render_page()` adds the draft banner.
[^usage]: `src/builder/cli.py` — `main()` gives `user` the positional `out`; `run()` resolves it from
    the working directory and passes it to `guard_output()`.
[^output]: `src/builder/cli.py` — `run()` passes `report()` the word counts of the pages the build
    emitted, but `citation_counts()` and the drafts of every page, and prints the page count and folder.
[^dates]: `src/builder/cli.py` — `run()` calls `build()`, and `write_site()` in `src/builder/build.py`
    records dates in `UPDATED.toml`.
[^sitemap]: `src/builder/build.py` — `write_site()` writes `sitemap_xml()` as `SITEMAP` when `build()` is
    given `sitemap=True` and the site has a `url`; `src/builder/cli.py` — `run()` asks for it on `publish`
    and `user`, and prints how many addresses it lists, or the setting to add.
[^exit]: `src/builder/cli.py` — `run()` returns 2 when `guard_output()` refuses; `main()` returns 2 with no
    wiki and 1 for a `WikiError`; argparse exits 2 on a missing argument or an option it does not know.
