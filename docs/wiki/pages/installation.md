+++
title = "Installation"
subtitle = "requirements, the wrapper script, a first wiki and updates"
status = "approved"
intent = """
Installation exists so that any project, on any stack, can start a wiki with one pinned release of the
tool and a handful of files. Updating should be a one-line change a reviewer can see.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Package", value = "wiki-builder", cite = "package" },
  { label = "Command", value = "wiki", cite = "package" },
]

[[infobox]]
group = "Requirements"
rows = [
  { label = "Python", value = "3.11 or newer", cite = "package" },
  { label = "Parser", value = "mistune, pinned exactly", cite = "package" },
  { label = "Runner", value = "uv or pip", cite = "uv" },
]

[[infobox]]
group = "Defaults"
rows = [
  { label = "Wiki folder", value = "docs/wiki", cite = "where" },
]
+++

wiki-builder is one Python package, and its only command is `wiki`.[^package] What each command does is
described on [Commands](commands.md), and checking a wiki on every push on
[Continuous integration](continuous-integration.md). An agent can take a project through every step
below from the [Installation prompt](installation-prompt.md).

## Requirements

It needs Python 3.11 or newer, and one dependency pinned exactly, the markdown parser `mistune`.[^package]
The wrapper script below also needs `uv`, whose `uvx` runs a release straight from its git address; a
project without `uv` installs a release with `pip` and runs `wiki` directly.[^uv]

## Wrapper

A project commits one script that runs a pinned release, and passes `--root` so the tool finds the project
wherever the script is called from.[^root]

```sh
#!/bin/sh
# scripts/dev-wiki.sh
set -eu
WIKI_VERSION=TAG
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec uvx --from "git+https://github.com/timothymarois/wiki-builder@$WIKI_VERSION" \
     wiki "$@" --root "$ROOT"
```

The tool accepts `--root` after the command, which is what lets the script add it to whatever it is
handed.[^root] `TAG` names a published wiki-builder release.{missing}

## First wiki

The tool reads a wiki from `docs/wiki` unless told otherwise.[^where] That folder needs a `wiki.toml`
with a site name and at least one section, or the tool stops and says so.[^config]

```toml
[site]
name = "Notes"

[[section]]
title = "Start"
pages = ["index", "goals"]
```

Every wiki needs a `goals.md` page to collect the intents onto, and every page needs a title and an
intent.[^pages] Every page a section lists must exist, so the example above also needs an
`index.md`.[^nav] A page about the wiki itself says `goals = false`.[^exempt]

```markdown
+++
title = "Goals"
status = "approved"
goals = false
intent = """
This page collects what each part of the project is for.
"""
+++

What each part is for.
```

`wiki sync` writes the skill for the project's agents and records the release, then `wiki build` records
each page's date.[^sync] The tool writes no ignore file, so a project adds `docs/wiki/site/` to its own
`.gitignore` to keep the rendered site out of version control, as wiki-builder does.[^ignore]

```sh
./scripts/dev-wiki.sh sync
./scripts/dev-wiki.sh build
./scripts/dev-wiki.sh check
```

## Continuous integration

`wiki check` exits with 1 on any problem, so a CI job that runs it fails the moment a change breaks the
wiki.[^exit] Installing the tool includes adding that job to the project's CI, so the wiki is checked on
every push and pull request and cannot drift unnoticed between local runs, as described on
[Continuous integration](continuous-integration.md).

## Updates

An update is a new tag in the script, then `wiki sync` to rewrite the skill and record the release.[^sync]
`wiki check` fails until that release is recorded, and names every page a new rule breaks.[^version]

[^package]: `pyproject.toml` — `[project.scripts]` names the `wiki` command, `requires-python` asks for
    3.11 or newer, and `dependencies` pins `mistune==3.3.4`.
[^uv]: uv docs — [Tools](https://docs.astral.sh/uv/guides/tools/): `uvx` is an alias for `uv tool run`,
    and `--from` installs a tool from another source, such as a git repository; `action.yml` — installs
    wiki-builder with `pip`, without `uv`.
[^root]: `src/builder/cli.py` — `main()` accepts `--root` and `--wiki` before the command or after it.
[^where]: `src/builder/build.py` — `wiki_of()` defaults the wiki to `docs/wiki`.
[^config]: `src/builder/config.py` — `read_config()` refuses a `wiki.toml` with no `site.name` or no
    `[[section]]`.
[^pages]: `src/builder/build.py` — `write_site()` refuses a wiki with no `goals.md`, and `read_pages()`
    refuses a page with no title or intent.
[^nav]: `src/builder/build.py` — `render_nav()` refuses a section listing a page that does not exist.
[^exempt]: `src/builder/build.py` — `goals = false` is skipped by `goals_page()` and `uncited_problems()`.
[^sync]: `src/builder/cli.py` — `sync()` writes the skill and calls `record_version()` in
    `src/builder/config.py`; `src/builder/build.py` — `write_site()` records dates in `UPDATED.toml`.
[^ignore]: `.gitignore` — `docs/wiki/site/`; `src/builder/cli.py` — `run()` builds into `site` inside the
    wiki folder, and nothing in `src/builder` writes a `.gitignore`.
[^exit]: `src/builder/cli.py` — `run()` returns 1 when `check()` finds a problem, and `main()` returns that
    as the exit code.
[^version]: `src/builder/build.py` — `version_problems()`, called from `check()`, which gathers every
    problem at once.
