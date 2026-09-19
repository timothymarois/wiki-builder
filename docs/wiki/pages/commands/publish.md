+++
title = "wiki publish"
subtitle = "build the site with clean addresses, for a host"
status = "approved"
intent = """
wiki publish exists so that a wiki can be put on a web host with addresses that read cleanly. It should
never write over a folder the tool did not make.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki publish", cite = "usage" },
  { label = "Arguments", value = "OUT", cite = "usage" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Output folder", value = "OUT", note = "relative to the working directory", cite = "usage" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Files written", value = "OUT, UPDATED.toml", cite = ["publish", "dates"] },
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
[Site](../site.md). **The folder is written whole or not at all**: the build goes to a folder beside it
and replaces it once it has finished, so a build that stops partway leaves no half-written site and the
last one published is still there.[^whole]

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
`wiki build`, it records each changed page's date in `UPDATED.toml`.[^dates] With `site.url` set in
`wiki.toml`, it also writes `sitemap.xml` into `OUT`, listing every approved page and category page at its
full address, each page with the day it last changed; without it, a closing line names the
setting.[^sitemap] On a wiki of three pages,
with the folder being wherever the command ran:[^output]
```text
wiki: goals                              25 words    0 cited    0 missing
wiki: index                               8 words    0 cited    0 missing
wiki: refunds                            22 words    1 cited    1 missing
wiki: 1 source cited, 1 claim marked as having no source
wiki: the collected goals read in 17 words
wiki: these budgets are PROVISIONAL -- 500 words a page, 3500 for the collected goals. What this project's readers actually read has not been measured; until it is, the numbers are a guess that happens to be enforced. Set budget.calibrated in wiki.toml once it is.
wiki: 3 pages written to /path/to/notes/site-out
wiki: set site.url in wiki.toml to write sitemap.xml
wiki: /path/to/notes/site-out uses clean addresses and needs a server; the site itself opens without one
```

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | the site is built[^exit] | `wiki: /path/to/notes/site-out uses clean addresses and needs a server; the site itself opens without one` |
| `1` | a problem stops the build[^exit] | the problem, with `OUT` left as it was[^whole] |
| `2` | `OUT` is not empty and was not made by the tool[^exit] | `wiki: /path/to/notes/taken is not empty and was not written by this tool; remove it yourself if you meant to replace it` |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |
| `2` | `OUT` is missing[^exit] | `wiki publish: error: the following arguments are required: OUT` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |

[^publish]: `src/builder/cli.py` — `run()` builds into `OUT` with `links="clean"`.
[^usage]: `src/builder/cli.py` — `main()` gives `publish` the positional `out`; `run()` resolves it from
    the working directory and passes it to `guard_output()`.
[^output]: `src/builder/cli.py` — `run()` calls `report()`, then prints the page count, the folder, and
    that clean addresses need a server.
[^dates]: `src/builder/cli.py` — `run()` calls `build()`, and `write_site()` in `src/builder/build.py`
    records dates in `UPDATED.toml`.
[^sitemap]: `src/builder/build.py` — `write_site()` writes `sitemap_xml()` as `SITEMAP` when `build()` is
    given `sitemap=True` and the site has a `url`; `src/builder/cli.py` — `run()` asks for it on `publish`
    and `user`, and prints how many addresses it lists, or the setting to add.
[^whole]: `src/builder/cli.py` — `run()` builds `publish` and `user` into a `tempfile.mkdtemp()` beside
    `OUT`, removes it if the build raises, and renames it over `OUT` once the build has returned.
[^exit]: `src/builder/cli.py` — `run()` returns 2 when `guard_output()` refuses; `main()` returns 2 with no
    wiki and 1 for a `WikiError`; argparse exits 2 on a missing argument or an option it does not know.
