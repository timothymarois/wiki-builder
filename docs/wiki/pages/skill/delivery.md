+++
title = "Delivery"
subtitle = "the skill's folder in a project, and the release that wiki.toml records"
status = "approved"
intent = """
Delivery exists so that a change to the skill's rules reaches a project only when that project asks for
it, and arrives where the project reviews it.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki sync", cite = "sync" },
  { label = "Options", value = "--skill-dir, --no-skill", cite = ["skilldir", "noskill"] },
  { label = "Package manifest", value = "manifest.json", cite = "manifest" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Skill folder", value = ".agents/skills, else .claude/skills", note = "unless --skill-dir names one", cite = ["home", "skilldir"] },
  { label = "Release record", value = "wiki.toml", note = "checked by wiki check", cite = ["record", "version"] },
]
+++

`wiki sync` copies the [skill](../skill.md) into a project, and records which release of the tool the
project is on.[^sync]

## Home

The skill goes into the project's `.agents/skills` folder if there is one.[^home] Otherwise it goes into
`.claude/skills`, which is created if it does not exist.[^home] The first is preferred because the second
is often a link to it, and writing through the link would write the same place twice.[^home]

The skill lands in a folder named after itself, and a file is rewritten only when its text has
changed.[^written] A file that a newer release no longer ships stays in the project until it is deleted by
hand.[^written]

`wiki sync --skill-dir` names the folder instead, relative to the project, and the skill goes there
whatever else exists; the folder is created if it is missing.[^skilldir] `wiki sync --no-skill` records
the release without writing the skill, and asking for both at once is refused.[^noskill]

## Release

`wiki sync` also records, in `wiki.toml`, which release of the tool the project is on.[^record] It writes
the `version` setting of the `[tool]` table, adding the setting or the whole table when it is missing, and
changes no other setting, no line ending and no comment beside the version.[^record]

**`wiki check` fails while that record is missing or names a different release**, and it says to run
`wiki sync`.[^version] A newer release can add a check, and a new check finds old pages; the record makes
that failure expected rather than surprising.[^version]

## Skill package

The repository also publishes the skill as a **skill package**: `manifest.json`, at the repository's
root, names the package `wiki-builder` and lists `writing-wiki-pages` at the folder `wiki sync` copies
from.[^manifest] A Rundesk agent gets the skill by adding the repository as a skill package, and receives
each change to it with the next release tag, without running `wiki sync`.{missing} The manifest
carries the same version as the release, and the tool's tests fail while the two differ.[^manifest]

[^sync]: `src/builder/cli.py` — `sync()` copies every markdown file under `SKILL` into `skill_home()`, then
    calls `record_version()` in `src/builder/config.py`.
[^home]: `src/builder/cli.py` — `skill_home()` tries `.agents/skills`, then `.claude/skills`, and falls
    back to `.claude/skills`.
[^written]: `src/builder/cli.py` — `SKILL_NAME` names the folder; `sync()` compares each file's text before
    writing it, and deletes nothing.
[^skilldir]: `src/builder/cli.py` — `skill_home()` joins a given folder to the project root before trying
    either convention.
[^noskill]: `src/builder/cli.py` — `sync()` skips the copy when `skill` is false; `main()` puts
    `--no-skill` and `--skill-dir` in one mutually exclusive group.
[^record]: `src/builder/config.py` — `record_version()` replaces the `version` line inside the `[tool]`
    table, keeping a comment after the value, adds one under its header or appends the table, writes the
    file's own line endings back, and refuses to write a file that would read differently anywhere outside
    `[tool]`; `src/builder/cli.py` — `sync()` prints the recorded release.
[^version]: `src/builder/build.py` — `version_problems()`, called from `check()`.
[^manifest]: `manifest.json` — `schema` 1, `name`, `version` and `skills`, whose one entry names
    `writing-wiki-pages` at `src/skill`; `tests/test_build.py` —
    `test_the_skill_package_manifest_lists_the_skill_this_release_ships()` holds its version to
    `src/builder/__init__.py`.
