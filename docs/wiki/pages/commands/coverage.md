+++
title = "wiki coverage"
subtitle = "list the source files no page cites"
status = "approved"
intent = """
wiki coverage exists so that a writer or an agent can see which of the project's source files no page
cites, and which citations name a file that no longer exists, without reading every page. It should report
and never block: each gap is a line to act on, not a failed command.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki coverage", cite = "usage" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Files written", value = "none", cite = "coverage" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", note = "whatever the report finds", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", note = "such as no [coverage] table", cite = "exit" },
]
+++

`wiki coverage` lists every source file that no page's references cite, and every citation of a file that
does not exist, then the totals, and writes nothing.[^coverage] It counts only the files `coverage.include`
names in `wiki.toml`, less those `coverage.exclude` names, as [wiki.toml](../wiki-toml.md) describes.

## Usage

It takes only the options every command shares.[^usage]
```sh
wiki coverage [-h] [--root ROOT] [--wiki WIKI]
wiki coverage
```

## Output

A source file counts as cited when a page's reference names it in backticks; a reference inside a code
block, or one naming a folder, covers nothing, and a line number after a file, as in `src/app.py:12`, is
ignored.[^cited] A citation is reported as naming a file that does not
exist only when it names a file with an extension under a folder the project has, so an action, a media
type or a generated folder is never reported.[^cited] On a project with one uncited file and one citation
of a file that does not exist:[^coverage]
```text
wiki: src/builder/__init__.py is cited by no page
wiki: commands/sync.md cites src/builder/sync.py, which does not exist
wiki: 20 of 21 source files cited; 1 citation names a file that does not exist
```

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | the report is printed, whatever it finds[^exit] | `wiki: 20 of 21 source files cited; 1 citation names a file that does not exist` |
| `1` | `coverage.include` matches no file, a pattern list is not a list of patterns, or a pattern leads outside the project[^exit] | `wiki: wiki.toml: coverage.include matches no files in /path/to/notes; name the project's source files relative to the project, such as include = ["src/**/*.py"]` |
| `2` | `wiki.toml` has no `[coverage]` table[^exit] | `wiki: wiki.toml has no [coverage] table; add one naming the source files to count, such as [coverage] include = ["src/**/*.py"]` |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |

[^coverage]: `src/builder/cli.py` — `run()` prints a line for each file in the `uncited` list `coverage()`
    returns and each page and name in its `missing` list, then the totals; `src/builder/build.py` —
    `coverage()` reads the pages and the project and writes nothing.
[^usage]: `src/builder/cli.py` — `main()` gives `coverage` only the shared options.
[^cited]: `src/builder/build.py` — `cited_paths()` reads the backticked names in footnotes outside fenced
    code, dropping a trailing line number with `LINE_NUMBER`; `coverage()` counts a name that is a file, and reports one as missing only when it has an
    extension, sits under a folder the project has, and does not exist.
[^exit]: `src/builder/cli.py` — `run()` returns 0 after the report and 2 when `coverage()` returns `None`;
    `main()` returns 1 for a `WikiError`, which `read_coverage()` in `src/builder/config.py`, refusing an
    absolute pattern or one with a `..` part, and `coverage()` in `src/builder/build.py` raise, and 2 with
    no wiki; argparse exits 2 on an option it does not know.
