+++
title = "Skill"
subtitle = "how an agent learns to write a page"
status = "approved"
intent = """
The skill exists so that an agent writing a page, in any project, writes it the way the owner approved
without each project inventing its own rules. A change to those rules should reach a project only when
that project asks for it, and arrive where somebody reviews it.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Name", value = "writing-wiki-pages", cite = "files" },
  { label = "Command", value = "wiki sync", cite = "sync" },
  { label = "Options", value = "--skill-dir, --no-skill", cite = ["skilldir", "noskill"] },
]

[[infobox]]
group = "Contents"
rows = [
  { label = "Instructions", value = "SKILL.md", cite = "files" },
  { label = "Worked examples", value = "page-standard.md, reference-standard.md", cite = "files" },
  { label = "Rule files", value = "naming-and-grammar.md, reference-pages.md", cite = "files" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Location", value = ".agents/skills, else .claude/skills", note = "unless --skill-dir names one", cite = ["home", "skilldir"] },
  { label = "Release record", value = "wiki.toml", note = "checked by wiki check", cite = ["record", "version"] },
]
+++

The **skill**, `writing-wiki-pages`, is the half of the tool that is not code: instructions for writing
a page in `SKILL.md`, and a `references` folder beside it.[^files] That folder holds the rules for naming,
grammar and reference pages, and two worked examples, one for an ordinary page and one for a reference
page, each written well and badly.[^files] `wiki sync` copies it into the project, where agents read
it.[^sync] The rules it teaches are enforced by the [Checks](checks.md).

## Home

The skill goes into the project's `.agents/skills` folder if there is one.[^home] Otherwise it goes into
`.claude/skills`, which is created if it does not exist.[^home] The first is preferred because the second
is often a link to it, and writing through the link would write the same place twice.[^home]

The skill lands in a folder named after itself, and a file is rewritten only when its text has
changed.[^written]

`wiki sync --skill-dir` names the folder instead, relative to the project, and the skill goes there
whatever else exists; the folder is created if it is missing.[^skilldir] `wiki sync --no-skill` records
the release without writing the skill, and asking for both at once is refused.[^noskill]

## Release

`wiki sync` also records, in `wiki.toml`, which release of the tool the project is on.[^record] It changes
that one line and leaves the rest of the hand-written file alone.[^record]

**`wiki check` fails while that record is missing or names a different release**, and it says to run
`wiki sync`.[^version] A newer release can add a check, and a new check finds old pages; the record makes
that failure expected rather than surprising.[^version]

[^files]: `src/builder/cli.py` — `SKILL_NAME` names the skill; `sync()` copies every markdown file under
    `SKILL`, which `src/builder/build.py` finds with `skill_dir()`.
[^sync]: `src/builder/cli.py` — `sync()`.
[^home]: `src/builder/cli.py` — `skill_home()` tries `.agents/skills`, then `.claude/skills`, and falls
    back to `.claude/skills`.
[^written]: `src/builder/cli.py` — `SKILL_NAME` names the folder; `sync()` compares each file's text before
    writing it.
[^skilldir]: `src/builder/cli.py` — `skill_home()` joins a given folder to the project root before trying
    either convention.
[^noskill]: `src/builder/cli.py` — `sync()` skips the copy when `skill` is false; `main()` puts
    `--no-skill` and `--skill-dir` in one mutually exclusive group.
[^record]: `src/builder/config.py` — `record_version()` replaces the `version` line under `[tool]`, or
    appends that table if it is absent.
[^version]: `src/builder/build.py` — `version_problems()`, called from `check()`.
