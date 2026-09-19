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
  { label = "Options", value = "--json, --summary", note = "one or the other", cite = "shape" },
  { label = "Arguments", value = "PAGE", note = "a page or folder; the whole wiki when none is named", cite = "scope" },
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

Beside the options every command shares, it takes one shape for its report, and the pages to report
on.[^usage]
```sh
wiki check [-h] [--root ROOT] [--wiki WIKI] [--json | --summary] [PAGE ...]
wiki check
wiki check checks/budgets
```

## Options

| Option | Meaning |
|---|---|
| `--json` | write the problems as one JSON document on standard output, for another tool to read[^shape] |
| `--summary` | count the problems by the check that found them, instead of listing them[^shape] |

**Neither may be given with the other**, and giving both exits with 2.[^shape]

Both are written for another tool rather than for a person, and what each holds is described on
[Report shapes](check/reports.md).

## Arguments

| Argument | Meaning |
|---|---|
| `PAGE` | a page or a folder under `pages`, with or without `.md`; the whole wiki when none is named[^scope] |

**Naming a page is for writing, not for merging.**[^scope] Every check still runs over the whole wiki,
because each reads one page against the others; only the report narrows, and it says what it is not
showing and what did not run.[^scope][^scoped] It skips the build, which most of a check's time goes on
and which only the page budget and the PDF links need.[^built] A name matching no page is
refused.[^scope]

```text
wiki: 1 problem on checks/budgets; 4 elsewhere, and budget and pdf did not run, so this is not the whole check -- run `wiki check` with no page before merging
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

## Exit codes

**A wiki that cannot be read at all exits with 1, not 2**, because a missing `wiki.toml` is a wrong wiki
rather than a mistyped command.[^broken] A gate that lets 1 past and stops on 2 lets a broken wiki
through.[^broken]

| Code | Condition | Message |
|---|---|---|
| `0` | no problem is found[^exit] | a last line ending `0 problems` |
| `1` | at least one problem is found[^exit] | each problem, then a last line such as `wiki: 3 pages, 1 problem` |
| `1` | a problem stops the build | that problem alone[^stop] |
| `1` | the wiki cannot be read at all[^broken] | `wiki: there is no wiki.toml in docs/wiki` |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |

[^check]: `src/builder/build.py` — `check()` builds into a temporary directory with `record=False`.
[^usage]: `src/builder/cli.py` — `main()` gives `check` the shared options and one mutually exclusive
    group.
[^shape]: `src/builder/cli.py` — `main()` puts `--json` and `--summary` in a mutually exclusive group,
    which argparse refuses both of, exiting 2.
[^scope]: `src/builder/cli.py` — `main()` gives `check` the positional `pages`; `src/builder/build.py` —
    `check_pages()` runs every check in `page_checks()` over the whole wiki and keeps the problems whose
    file `scoped_page()` matches, raising `WikiError` for a name that matches none.
[^scoped]: `src/builder/cli.py` — `run()` prints what `check()` put in `skipped`, the problems counted
    elsewhere, and the line saying this is not the whole check.
[^built]: `src/builder/build.py` — `check()` returns from `check_pages()` before the
    `tempfile.TemporaryDirectory()` build, and `BUILT_CHECKS` names the two the build is for.
[^output]: `src/builder/cli.py` — `run()` prints each problem to standard error, then calls `report()` with
    `citation_counts()`, which prints the budget warning, and prints the count; `src/builder/build.py` —
    `uncited_problems()` and `pointing_problems()` name a sentence's page and line.
[^marks]: `src/builder/cli.py` — `run()` prints `missing_marks()` after the problems.
[^exit]: `src/builder/cli.py` — `run()` returns 1 when there are problems and 0 when there are none;
    `main()` returns 2 with no wiki; argparse exits 2 on an option it does not know.
[^stop]: `src/builder/cli.py` — `main()` catches `WikiError`, prints it, and returns 1.
[^broken]: `src/builder/cli.py` — `main()` returns 2 only when the wiki folder is not there, and 1 for
    every `WikiError`, which is what `read_config()` in `src/builder/config.py` raises for a missing
    `wiki.toml`.
