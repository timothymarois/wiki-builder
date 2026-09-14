+++
title = "wiki player"
subtitle = "build the view for people outside the project"
status = "approved"
intent = """
wiki player exists so that the pages meant for people outside the project can be handed to them with
nothing internal left in. It should never carry a reference, a missing-source mark or a page's source.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki player", cite = "usage" },
  { label = "Argument", value = "OUT", cite = "usage" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Pages", value = "those marked for players", cite = "player" },
  { label = "Removed", value = "references, red marks, Source tab", cite = "player" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki player` builds only the pages marked for players into the folder it is given, with every
reference, red mark and Source tab removed.[^player] Which pages those are is described on
[Site](../site.md).

## Usage

The folder is required.[^usage]
```sh
wiki player [--root ROOT] [--wiki WIKI] OUT
```

## Arguments

| Argument | Meaning |
|---|---|
| `OUT` | the folder to build into, relative to the working directory; empty, or an earlier build[^usage] |

## Output

It prints what `wiki build` prints.[^output]

## Exit codes

It exits with 0 once built, 1 when a page stops the build, and 2 when the folder is not empty and was not
made by the tool, or there is no wiki.[^exit]

[^player]: `src/builder/cli.py` — `run()` builds with audience `"player"`; `src/builder/build.py` —
    `visible_to()`, `for_player()` and `with_source` in `write_site()`.
[^usage]: `src/builder/cli.py` — `main()` gives `player` the positional `out`; `run()` resolves it from
    the working directory and passes it to `guard_output()`.
[^output]: `src/builder/cli.py` — `run()` calls `report()` and prints the page count and folder.
[^exit]: `src/builder/cli.py` — `run()` returns 2 when `guard_output()` refuses; `main()` returns 2 with no
    wiki and 1 for a `WikiError`.
