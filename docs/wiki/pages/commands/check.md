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
  { label = "Command", value = "wiki check", cite = "usage" },
  { label = "Options", value = "--root, --wiki", cite = "usage" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki check` builds the site in a temporary folder and reports every problem it finds, without writing to
the wiki.[^check] What each problem means is described on [Checks](../checks.md), and how it runs on
every push on [Continuous integration](../continuous-integration.md).

## Usage

It takes only the options every command shares.[^usage]
```sh
wiki check [-h] [--root ROOT] [--wiki WIKI]
wiki check
```

## Output

Each problem is printed as one sentence naming the page, the line and what to do.[^output] Every claim
marked as having no source is listed the same way, and does not fail the check.[^marks] Then come every
page's word count and citations, the totals, and a last line counting pages and problems.[^output] On a
wiki of three pages with one uncited sentence:[^output]
```text
wiki: refunds.md:13: “A support agent can issue one.” states something and cites nothing; give it a reference, or {missing} if there is none
wiki: refunds.md:12: “Partial refunds are not offered. {missing}” is marked as having no source
wiki: goals                              20 words    0 cited    0 missing
wiki: index                               3 words    0 cited    0 missing
wiki: refunds                            29 words    1 cited    1 missing
wiki: 1 source cited, 1 claim marked as having no source
wiki: the collected goals read in 15 words
wiki: 3 pages, 1 problem
```

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | no problem is found[^exit] | a last line ending `0 problems` |
| `1` | at least one problem is found | each problem, then a last line such as `wiki: 3 pages, 1 problem` |
| `1` | a problem stops the build | that problem alone[^stop] |
| `2` | there is no wiki where it was pointed | `wiki: no wiki at nowhere` |

[^check]: `src/builder/build.py` — `check()` builds into a temporary directory with `record=False`.
[^usage]: `src/builder/cli.py` — `main()` gives `check` only the shared options.
[^output]: `src/builder/cli.py` — `run()` prints each problem to standard error, then calls `report()` with
    `citation_counts()` and prints the count.
[^marks]: `src/builder/cli.py` — `run()` prints `missing_marks()` after the problems.
[^exit]: `src/builder/cli.py` — `run()` returns 1 when there are problems and 0 when there are none;
    `main()` returns 2 with no wiki.
[^stop]: `src/builder/cli.py` — `main()` catches `WikiError`, prints it, and returns 1.
