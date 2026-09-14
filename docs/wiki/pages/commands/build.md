+++
title = "wiki build"
subtitle = "render the pages into the site"
status = "approved"
intent = """
wiki build exists so that a person can turn the pages into a site they can open, and see what each page
costs to read while they do. It should change nothing but the site and the record of when pages changed.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki build" },
  { label = "Options", value = "--root, --wiki" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Output", value = "docs/wiki/site" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0" },
  { label = "Problems", value = "1" },
  { label = "Misuse", value = "2" },
]
+++

`wiki build` renders every page into `docs/wiki/site`, and records the day each changed page last
changed.[^build] What the site holds is described on [Site](../site.md).

## Usage

It takes only the options every command shares.[^usage]
```sh
wiki build [--root ROOT] [--wiki WIKI]
```

## Output

It prints each page's word count, the words in the collected goals, any drafts waiting on the owner, and a
warning while the reading budgets are uncalibrated, then how many pages it wrote and where.[^report]

It refuses to write into a folder that is not empty and was not made by an earlier build.[^guard]

## Exit codes

It exits with 0 once the site is written, 1 when a page stops the build, and 2 when there is no wiki or
the output folder was not made by the tool.[^exit]

[^build]: `src/builder/cli.py` — `run()` builds into `site` inside the wiki folder;
    `src/builder/build.py` — `write_site()` writes `UPDATED.toml` when a page's digest changes.
[^usage]: `src/builder/cli.py` — `main()` gives `build` only the shared options.
[^report]: `src/builder/build.py` — `report()`; `src/builder/cli.py` — `run()` prints the page count and
    the folder.
[^guard]: `src/builder/cli.py` — `guard_output()`.
[^exit]: `src/builder/cli.py` — `main()` returns 2 with no wiki and 1 for a `WikiError`; `run()` returns 2
    when `guard_output()` refuses.
