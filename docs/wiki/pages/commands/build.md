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
  { label = "Command", value = "wiki build", cite = "usage" },
  { label = "Options", value = "--root, --wiki", cite = "usage" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Output", value = "docs/wiki/site", note = "site inside the wiki folder", cite = "build" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki build` renders every page into `site` inside the wiki folder, `docs/wiki/site` by default, and
records the day each changed page last changed.[^build] What the site holds is described on
[Site](../site.md).

## Usage

It takes only the options every command shares.[^usage]
```sh
wiki build [-h] [--root ROOT] [--wiki WIKI]
wiki build
```

## Output

It prints each page's word count and citations, then the totals, the words in the collected goals, and
how many pages it wrote and where.[^report] It also names any draft waiting on the owner, and warns while
the reading budgets are uncalibrated.[^report] On a wiki of three pages, with the folder on the last line
being wherever the wiki sits:[^report]
```text
wiki: goals                              25 words    0 cited    0 missing
wiki: index                               8 words    0 cited    0 missing
wiki: refunds                            22 words    1 cited    1 missing
wiki: 1 source cited, 1 claim marked as having no source
wiki: the collected goals read in 17 words
wiki: these budgets are PROVISIONAL -- 500 words a page, 3500 for the collected goals. What this project's readers actually read has not been measured; until it is, the numbers are a guess that happens to be enforced. Set budget.calibrated in wiki.toml once it is.
wiki: 3 pages written to /path/to/notes/docs/wiki/site
```

It refuses to write into a folder that is not empty and was not made by an earlier build.[^guard] A build
that stops partway has already copied its stylesheet, so the next build still accepts the folder.[^partway]
A file put in the folder by hand, such as a host's `CNAME`, survives every build: a build lists the files
it wrote in `.wiki-build` inside the folder, and deletes only files from that list.[^record]

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | the site is written[^exit] | `wiki: 3 pages written to /path/to/notes/docs/wiki/site` |
| `1` | a problem stops the build[^stop] | the problem, such as `wiki: there is no goals.md; the collected goals need a page to be collected onto` |
| `1` | `UPDATED.toml` or `PICTURES.toml` is not valid TOML[^unreadable] | `wiki: UPDATED.toml is unreadable:` and the parser's error |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |
| `2` | the site folder holds files the tool did not write[^exit] | `wiki: /path/to/notes/docs/wiki/site is not empty and was not written by this tool; remove it yourself if you meant to replace it` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |

[^build]: `src/builder/cli.py` — `run()` builds into `site` inside the wiki folder;
    `src/builder/build.py` — `write_site()` writes `UPDATED.toml` when a page's digest changes.
[^usage]: `src/builder/cli.py` — `main()` gives `build` only the shared options.
[^report]: `src/builder/build.py` — `report()`, with `citation_counts()`; `src/builder/cli.py` — `run()`
    prints the page count and the folder.
[^guard]: `src/builder/cli.py` — `guard_output()`.
[^partway]: `src/builder/build.py` — `write_site()` copies `wiki.css` into `assets` before it writes any
    page, and `src/builder/cli.py` — `guard_output()` accepts a folder that holds it.
[^record]: `src/builder/build.py` — `clear_stale()`, called at the end of `write_site()`, unlinks only the
    files `BUILD_RECORD` lists that the build did not write again, then records what it wrote.
[^exit]: `src/builder/cli.py` — `main()` returns 2 with no wiki and prints a `WikiError` before returning 1;
    `run()` returns 2 when `guard_output()` refuses; argparse exits 2 on an option it does not know.
[^unreadable]: `src/builder/build.py` — `read_dates()` and `read_ledger()` raise a `WikiError` naming the
    file when it is not valid TOML.
[^stop]: `src/builder/cli.py` — `main()` prints a `WikiError` and returns 1; `src/builder/build.py` —
    `write_site()` raises a `WikiError` for a wiki with no `goals.md`.
