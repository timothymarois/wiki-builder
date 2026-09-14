+++
title = "wiki sync"
subtitle = "bring the skill and the recorded release up to date"
status = "approved"
intent = """
wiki sync exists so that a project takes up a release of the tool in one step: the skill its agents read,
and the release its pages are checked against. It should write only those, and only where the project
asks.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki sync", cite = "sync" },
  { label = "Options", value = "--skill-dir, --no-skill, --root, --wiki", cite = "group" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Skill folder", value = ".agents/skills, else .claude/skills", cite = "group" },
  { label = "Release record", value = "wiki.toml", cite = "sync" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", note = "such as no wiki.toml", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki sync` copies the skill into the project, and records in `wiki.toml` the release it came
from.[^sync] Why the skill lives in the project is described on [Skill](../skill.md).

## Usage

Either skill option may be given, but not both.[^group]
```sh
wiki sync [--root ROOT] [--wiki WIKI] [--skill-dir DIR | --no-skill]
```

## Options

| Option | Meaning | Default |
|---|---|---|
| `--skill-dir DIR` | the folder to put the skill in, relative to the project[^group] | `.agents/skills` if it exists, otherwise `.claude/skills` |
| `--no-skill` | record the release without writing the skill | the skill is written |

## Output

It names each file it wrote, leaving out any already up to date, then the release it recorded.[^output]

## Exit codes

It exits with 0 once done, 1 when there is no `wiki.toml` to record the release in, and 2 when both skill
options are given or there is no wiki.[^exit]

[^sync]: `src/builder/cli.py` — `sync()`, and `record_version()` in `src/builder/config.py`.
[^group]: `src/builder/cli.py` — `main()` puts `--skill-dir` and `--no-skill` in one mutually exclusive
    group; `skill_home()` joins a given folder to the project.
[^output]: `src/builder/cli.py` — `sync()` prints each file it wrote and the recorded release.
[^exit]: `src/builder/cli.py` — `main()` returns 2 with no wiki and 1 for a `WikiError`;
    `src/builder/config.py` — `record_version()` raises one when `wiki.toml` is missing.
