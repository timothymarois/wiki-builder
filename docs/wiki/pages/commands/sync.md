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
  { label = "Skill folder", value = ".agents/skills, else .claude/skills", cite = "home" },
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
wiki sync [-h] [--root ROOT] [--wiki WIKI] [--skill-dir DIR | --no-skill]
wiki sync
```

## Options

| Option | Meaning | Default |
|---|---|---|
| `--skill-dir DIR` | the folder to put the skill in, relative to the project[^group] | `.agents/skills` if it exists, otherwise `.claude/skills`[^home] |
| `--no-skill` | record the release without writing the skill[^noskill] | the skill is written |

## Output

It names each file it wrote, leaving out any already up to date, then the release it recorded.[^output] It
deletes nothing, so a file a newer release no longer ships stays where it is.[^output] In a project with
an `.agents/skills` folder:[^output]
```text
wiki: wrote .agents/skills/writing-wiki-pages/SKILL.md
wiki: wrote .agents/skills/writing-wiki-pages/references/flowcharts.md
wiki: wrote .agents/skills/writing-wiki-pages/references/naming-and-grammar.md
wiki: wrote .agents/skills/writing-wiki-pages/references/page-standard.md
wiki: wrote .agents/skills/writing-wiki-pages/references/reference-pages.md
wiki: wrote .agents/skills/writing-wiki-pages/references/reference-standard.md
wiki: wiki.toml records wiki-builder 0.1.0
```

With `--no-skill`, it says so in place of the files:[^output]
```text
wiki: the skill was left out, as asked
wiki: wiki.toml records wiki-builder 0.1.0
```

When `wiki.toml` has no `[tool]` table, or one with no `version`, the release is added to it, and no other
setting, line ending or comment beside the version changes.[^record]

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | the release is recorded[^exit] | `wiki: wiki.toml records wiki-builder 0.1.0` |
| `1` | there is no `wiki.toml` to record it in; the skill has already been written, and is not listed[^exit] | ``wiki: there is no wiki.toml in /path/to/notes/docs/wiki; write one with a [site] name and at least one [[section]], then run `wiki sync` again`` |
| `1` | `wiki.toml` is not valid TOML, and is left as it was[^record] | `wiki: wiki.toml is unreadable:` and the parser's error |
| `1` | recording the release would change another setting, such as under a `[[tool]]` list, and the file is left as it was[^record] | ``wiki: wiki.toml could not take the release without changing another setting; set version = "0.1.0" in its [tool] table by hand, then run `wiki sync` again`` |
| `2` | both skill options are given; the message names the option given second first[^exit] | `wiki sync: error: argument --skill-dir: not allowed with argument --no-skill` |
| `2` | there is no wiki where it was pointed[^exit] | `wiki: no wiki at nowhere` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |

[^sync]: `src/builder/cli.py` — `sync()`, and `record_version()` in `src/builder/config.py`.
[^group]: `src/builder/cli.py` — `main()` puts `--skill-dir` and `--no-skill` in one mutually exclusive
    group; `skill_home()` joins a given folder to the project.
[^home]: `src/builder/cli.py` — `skill_home()` tries `.agents/skills`, then `.claude/skills`, and falls
    back to `.claude/skills`.
[^output]: `src/builder/cli.py` — `sync()` prints each file it wrote, the line for a skill left out and
    the recorded release, and deletes nothing.
[^record]: `src/builder/config.py` — `record_version()` replaces the `version` line inside the `[tool]`
    table, keeping a comment after the value, adds one under its header or appends the table, writes the
    file's own line endings back, and refuses to write a file that would read differently anywhere outside
    `[tool]`.
[^exit]: `src/builder/cli.py` — `main()` returns 2 with no wiki and 1 for a `WikiError`, and argparse exits
    2 when both options are given or an option it does not know is; `sync()` copies the skill before `record_version()` in
    `src/builder/config.py` raises `WikiError` for a missing `wiki.toml`.
[^noskill]: `src/builder/cli.py` — `main()` declares `--no-skill` off by default, and `run()` passes
    `skill=not args.no_skill` to `sync()`, which writes the skill only when asked and records the release
    either way.
