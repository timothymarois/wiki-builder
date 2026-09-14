+++
title = "wiki check"
subtitle = "every reason the wiki is not fit to read"
status = "approved"
intent = """
wiki check exists so that a person, or the gate a project runs before merging, learns every reason the
wiki is not fit to read in one run. It should change nothing, and its exit code alone should be enough to
fail a build.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki check" },
  { label = "Options", value = "--root, --wiki" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0" },
  { label = "Problems", value = "1" },
  { label = "Misuse", value = "2" },
]
+++

`wiki check` builds the site in a temporary folder and reports every problem it finds, without writing to
the wiki.[^check] What each problem means is described on [Checks](../checks.md).

## Usage

It takes only the options every command shares.[^usage]
```sh
wiki check [--root ROOT] [--wiki WIKI]
```

## Output

Each problem is printed as one sentence naming the page and what to do. Then come every page's word count
and a last line counting pages and problems.[^output]

## Exit codes

It exits with 0 when there are no problems, 1 when there is at least one, and 2 when there is no
wiki.[^exit] A problem that stops the build is reported on its own, and also exits with 1.[^stop]

[^check]: `src/builder/build.py` — `check()` builds into a temporary directory with `record=False`.
[^usage]: `src/builder/cli.py` — `main()` gives `check` only the shared options.
[^output]: `src/builder/cli.py` — `run()` prints each problem to standard error, then calls `report()` and
    prints the count.
[^exit]: `src/builder/cli.py` — `run()` returns 1 when there are problems; `main()` returns 2 with no wiki.
[^stop]: `src/builder/cli.py` — `main()` catches `WikiError` and returns 1.
