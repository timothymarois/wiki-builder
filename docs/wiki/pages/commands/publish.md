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
  { label = "Command", value = "wiki publish" },
  { label = "Argument", value = "OUT" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Link ending", value = "none", note = "an address ends in a folder" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0" },
  { label = "Problems", value = "1" },
  { label = "Misuse", value = "2" },
]
+++

`wiki publish` builds the same site as `wiki build` into the folder it is given, with addresses that end
in a folder rather than a file.[^publish] Those addresses need a server; how they differ is described on
[Site](../site.md).

## Usage

The folder is required.[^usage]
```sh
wiki publish [--root ROOT] [--wiki WIKI] OUT
```

## Arguments

| Argument | Meaning |
|---|---|
| `OUT` | the folder to build into, relative to the working directory; empty, or an earlier build[^usage] |

## Output

It prints what `wiki build` prints, then a reminder that the result needs a server.[^output]

## Exit codes

It exits with 0 once built, 1 when a page stops the build, and 2 when the folder is not empty and was not
made by the tool, or there is no wiki.[^exit]

[^publish]: `src/builder/cli.py` — `run()` builds into `OUT` with `links="clean"`.
[^usage]: `src/builder/cli.py` — `main()` gives `publish` the positional `out`; `run()` resolves it from
    the working directory and passes it to `guard_output()`.
[^output]: `src/builder/cli.py` — `run()` prints that clean addresses need a server.
[^exit]: `src/builder/cli.py` — `run()` returns 2 when `guard_output()` refuses; `main()` returns 2 with no
    wiki and 1 for a `WikiError`.
