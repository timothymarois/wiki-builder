+++
title = "Commands"
subtitle = "everything wiki does, and how to ask for it"
status = "approved"
intent = """
The command reference exists so that a person using the tool can find the command for a job, and exactly
how to type it, without reading the code. Every command, option, argument and exit code the tool accepts
should be here, and nothing it does not.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Program", value = "wiki", cite = "program" },
  { label = "Commands", value = "build, check, serve, sync, bless, publish, user, audit", cite = "commands" },
  { label = "Shared options", value = "--root, --wiki, --help", cite = "place" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki` is the one program the tool installs, and each job it does is a command typed after it.[^program]
The settings files it reads are described on [wiki.toml](wiki-toml.md), [Front matter](front-matter.md)
and [PICTURES.toml](pictures-toml.md).

## Usage

Every command is typed the same way, as the program's help prints it.[^program]
```sh
wiki [-h] [--version] [--root ROOT] [--wiki WIKI]
            {build,check,sync,serve,publish,user,bless,audit} ...
```

## Commands

| Command | Job |
|---|---|
| [`wiki build`](commands/build.md) | renders the pages into the site[^commands] |
| [`wiki check`](commands/check.md) | lists every reason the wiki is not fit to read |
| [`wiki serve`](commands/serve.md) | builds the site and serves it on this machine |
| [`wiki sync`](commands/sync.md) | writes the skill into the project and records the release |
| [`wiki bless`](commands/bless.md) | records that a picture is still true, and why |
| [`wiki publish`](commands/publish.md) | builds the site with clean addresses, for a host |
| [`wiki user`](commands/user.md) | builds only the pages marked for users, with everything internal removed |
| [`wiki audit`](commands/audit.md) | records that pages were checked against the code today |

Typing `wiki` with no command is the same as `wiki serve`.[^alone]

## Shared options

| Option | Meaning | Default |
|---|---|---|
| `--root ROOT` | the project[^place] | the working directory |
| `--wiki WIKI` | the folder the wiki lives in, relative to the working directory rather than to `ROOT`[^wikipath] | `docs/wiki` inside `ROOT` |
| `-h`, `--help` | the command's own help, then exit[^help] | off |

Both `--root` and `--wiki` may come before the command or after it, so a wrapper script can add them to
whatever it is handed.[^place] `wiki --version` prints the release, and is given before any command.[^version]

## Exit codes

Every command exits with 0 when it did what it was asked, 1 when something is wrong with the wiki, and 2
when it was misused: an option it does not know, no wiki where it was pointed, an output folder the tool
did not make, or a port already in use.[^exit] A problem is printed as one sentence.[^exit]

Every message names what to do.{missing} Some name only what is wrong, such as `wiki: no wiki at nowhere`,
`wiki: missing.png has no entry in PICTURES.toml` and the parser's own
`wiki: error: unrecognized arguments: --unknown`.[^messages]

[^program]: `src/builder/cli.py` — `main()` builds the `wiki` parser and its eight commands, and makes the
    command optional; `pyproject.toml` names the program under `[project.scripts]`.
[^commands]: `src/builder/cli.py` — each command's `help` in `main()`, and what `run()` does for it.
[^alone]: `src/builder/cli.py` — `run()` treats no command as `"serve"`.
[^place]: `src/builder/cli.py` — `main()` declares `--root` and `--wiki` on the program and, suppressed,
    on every command.
[^wikipath]: `src/builder/build.py` — `wiki_of()` uses a given `--wiki` as it stands, and joins
    `docs/wiki` to the root only when none is given.
[^version]: `src/builder/cli.py` — `main()` declares `--version` on the program only.
[^exit]: `src/builder/cli.py` — `main()` returns 2 when there is no wiki and prints any `WikiError`
    before returning 1; `run()` returns 2 when `guard_output()` refuses; argparse exits 2 on a command
    line it cannot read; `src/builder/serve.py` — `serve()` returns 2 for a port in use.
[^messages]: `src/builder/cli.py` — `main()` prints `no wiki at` and the path, and nothing more;
    `src/builder/build.py` — `bless()` raises `has no entry in`; argparse writes its own errors.
[^help]: `src/builder/cli.py` — `main()` leaves argparse's `-h` and `--help` on the program and on every
    command, which print that parser's help and exit; only the shared `place` parser is made with
    `add_help=False`.
