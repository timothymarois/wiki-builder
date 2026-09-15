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
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Files written", value = "none", cite = "check" },
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

Each problem is printed to standard error as one sentence saying what is wrong and what to do; a problem
with a sentence on a page also names that page and line.[^output] Every claim marked as having no source
is listed on standard output, and does not fail the check.[^marks] Then come every page's word count and
citations, the totals, the budget warning while budgets are uncalibrated, and a last line counting pages
and problems.[^output] On a wiki of three pages with one uncited sentence:[^output]
```text
wiki: refunds.md:14: “A support agent can issue one.” states something and cites nothing; give it a reference, or {missing} if there is none
wiki: refunds.md:12: “Partial refunds are not offered. {missing}” is marked as having no source
wiki: goals                              25 words    0 cited    0 missing
wiki: index                               8 words    0 cited    0 missing
wiki: refunds                            22 words    1 cited    1 missing
wiki: 1 source cited, 1 claim marked as having no source
wiki: the collected goals read in 17 words
wiki: these budgets are PROVISIONAL -- 500 words a page, 3500 for the collected goals. What this project's readers actually read has not been measured; until it is, the numbers are a guess that happens to be enforced. Set budget.calibrated in wiki.toml once it is.
wiki: 3 pages, 1 problem
```

When a newer wiki-builder release is published than the release running, the line before the last names it and
says how to take it up, and the check's result stays what the pages earn.[^newer] The question goes to
GitHub while the pages are checked, and the answer is awaited for at most two and a half seconds; offline,
refused or slow, the check prints no notice and no error.[^newer] Setting `WIKI_NO_RELEASE_CHECK` to any
value but empty leaves the question unasked.[^optout] Run by release 0.4.0 after 0.5.0 was
published:[^newer]
```text
wiki: wiki-builder 0.5.0 is released and this is 0.4.0; to take it up, change the pinned release to v0.5.0, run `wiki sync`, then run `wiki check`
wiki: 40 pages, 0 problems
```

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | no problem is found[^exit] | a last line ending `0 problems` |
| `1` | at least one problem is found[^exit] | each problem, then a last line such as `wiki: 3 pages, 1 problem` |
| `1` | a problem stops the build | that problem alone[^stop] |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |

[^check]: `src/builder/build.py` — `check()` builds into a temporary directory with `record=False`.
[^usage]: `src/builder/cli.py` — `main()` gives `check` only the shared options.
[^output]: `src/builder/cli.py` — `run()` prints each problem to standard error, then calls `report()` with
    `citation_counts()`, which prints the budget warning, and prints the count; `src/builder/build.py` —
    `uncited_problems()` and `pointing_problems()` name a sentence's page and line.
[^marks]: `src/builder/cli.py` — `run()` prints `missing_marks()` after the problems.
[^exit]: `src/builder/cli.py` — `run()` returns 1 when there are problems and 0 when there are none;
    `main()` returns 2 with no wiki; argparse exits 2 on an option it does not know.
[^stop]: `src/builder/cli.py` — `main()` catches `WikiError`, prints it, and returns 1.
[^newer]: `src/builder/build.py` — `newer_release()` asks `latest_release()` on a thread of its own before
    the pages are checked, waits no longer than `RELEASE_TIMEOUT`, 2.5 seconds, and gives no notice when the
    lookup fails or the release is not newer; `latest_release()` reads the tags from the git server at the
    package's `Homepage` address; `src/builder/cli.py` — `run()` prints the notice before the count and
    returns the same status either way.
[^optout]: `src/builder/build.py` — `newer_release()` gives no notice, and asks nothing, when the variable
    `NO_RELEASE_CHECK` names is set to a value that is not empty.
