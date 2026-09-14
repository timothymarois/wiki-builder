+++
title = "wiki publish"
subtitle = "build the site for a host"
status = "approved"
intent = """
wiki publish exists so that a wiki can be put on a web host with addresses that read cleanly. It should
never write over a folder the tool did not make.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki publish", cite = "usage" },
  { label = "Argument", value = "OUT", cite = "usage" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Link ending", value = "none", note = "an address ends in a folder", cite = "publish" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki publish` builds the same site as `wiki build` into the folder it is given, with addresses that end
in a folder rather than a file.[^publish] Those addresses need a server; how they differ is described on
[Site](../site.md).

## Usage

The folder is required.[^usage]
```sh
wiki publish [-h] [--root ROOT] [--wiki WIKI] OUT
wiki publish site-out
```

## Arguments

| Argument | Meaning |
|---|---|
| `OUT` | the folder to build into, relative to the working directory; empty, or an earlier build[^usage] |

## Output

It prints what `wiki build` prints, then a reminder that the result needs a server.[^output] Like
`wiki build`, it records each changed page's date in `UPDATED.toml`.[^dates] On a wiki of three pages,
with the folder being wherever the command ran:[^output]
```text
wiki: goals                              25 words    0 cited    0 missing
wiki: index                               8 words    0 cited    0 missing
wiki: refunds                            22 words    1 cited    1 missing
wiki: 1 source cited, 1 claim marked as having no source
wiki: the collected goals read in 17 words
wiki: these budgets are PROVISIONAL -- 500 words a page, 3500 for the collected goals. What this project's readers actually read has not been measured; until it is, the numbers are a guess that happens to be enforced. Set budget.calibrated in wiki.toml once it is.
wiki: 3 pages written to /path/to/notes/site-out
wiki: /path/to/notes/site-out uses clean addresses and needs a server; the site itself opens without one
```

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | the site is built[^exit] | `wiki: /path/to/notes/site-out uses clean addresses and needs a server; the site itself opens without one` |
| `1` | a problem stops the build[^exit] | the problem |
| `2` | `OUT` is not empty and was not made by the tool[^exit] | `wiki: /path/to/notes/taken is not empty and was not written by this tool; remove it yourself if you meant to replace it` |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |

[^publish]: `src/builder/cli.py` — `run()` builds into `OUT` with `links="clean"`.
[^usage]: `src/builder/cli.py` — `main()` gives `publish` the positional `out`; `run()` resolves it from
    the working directory and passes it to `guard_output()`.
[^output]: `src/builder/cli.py` — `run()` calls `report()`, then prints the page count, the folder, and
    that clean addresses need a server.
[^dates]: `src/builder/cli.py` — `run()` calls `build()`, and `write_site()` in `src/builder/build.py`
    records dates in `UPDATED.toml`.
[^exit]: `src/builder/cli.py` — `run()` returns 2 when `guard_output()` refuses; `main()` returns 2 with no
    wiki and 1 for a `WikiError`.
