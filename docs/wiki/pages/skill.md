+++
title = "Skill"
subtitle = "how an agent learns to write a page"
status = "approved"
categories = ["Commands"]
intent = """
The skill exists so that an agent writing a page, in any project, writes it the way the owner approved
without each project inventing its own rules. A change to those rules should reach a project only when
that project asks for it, and arrive where somebody reviews it.
"""

[[infobox]]
group = "Skill"
rows = [
  { label = "Command", value = "wiki sync" },
  { label = "Holds", value = "the rules, and a worked example" },
]
+++

The **skill** is the half of the tool that is not code: instructions for writing a page, and a worked
example of one page written well and badly.[^files] `wiki sync` copies it into the project, where agents
read it.[^sync] The rules it teaches are enforced by the [Checks](checks.md).

## Home

The skill goes into the project's `.agents/skills` folder if there is one. Otherwise it goes into
`.claude/skills`, which is created if it does not exist.[^home] The first is preferred because the second
is often a link to it, and writing through the link would write the same place twice.[^home]

The skill lands in a folder named after itself, and a file is rewritten only when its text has
changed.[^written]

## Release

`wiki sync` also records, in the project's settings file, which release of the tool the project is
on.[^record] It changes that one line and leaves the rest of the hand-written file alone.[^record]

**`wiki check` fails while that record is missing or names a different release**, and it says to run
`wiki sync`.[^version] A newer release can add a check, and a new check finds old pages; the record makes
that failure expected rather than surprising.[^version]

[^files]: `src/builder/cli.py` — `sync()` copies `SKILL.md` and
    `references/the-standard.md` from `SKILL`, which
    `src/builder/build.py` finds with `skill_dir()`.
[^sync]: `src/builder/cli.py` — `sync()`.
[^home]: `src/builder/cli.py` — `skill_home()` tries `.agents/skills`, then
    `.claude/skills`, and falls back to `.claude/skills`.
[^written]: `src/builder/cli.py` — `SKILL_NAME` names the folder; `sync()`
    compares each file's text before writing it.
[^record]: `src/builder/config.py` — `record_version()` replaces the
    `version` line under `[tool]`, or appends that table if it is absent.
[^version]: `src/builder/build.py` — `version_problems()`, called from
    `check()`.
