+++
title = "Skill"
subtitle = "the writing-wiki-pages instructions that wiki sync puts in a project"
status = "approved"
intent = """
The skill exists so that an agent writing a page, in any project, writes it the way the owner approved
without each project inventing its own rules. A change to those rules should reach a project only when
that project asks for it, and arrive where the project reviews it.
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
  { label = "Instructions", value = "SKILL.md", cite = "contents" },
  { label = "Worked examples", value = "page-standard.md, reference-standard.md", cite = "contents" },
  { label = "Rule files", value = "naming-and-grammar.md, infobox.md, reference-pages.md, flowcharts.md", cite = "contents" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Location", value = ".agents/skills, else .claude/skills", note = "unless --skill-dir names one", cite = ["home", "skilldir"] },
  { label = "Release record", value = "wiki.toml", note = "checked by wiki check", cite = ["record", "version"] },
]
+++

The **skill**, `writing-wiki-pages`, is the instructions an agent follows to write a page: `SKILL.md`,
and a `references` folder beside it.[^files] That folder holds the rules for naming, grammar, infoboxes,
reference pages and flowcharts, and worked examples of an ordinary page and of two reference pages, a
command and an endpoint, each written well and badly.[^contents] `SKILL.md` gives the steps for each
task an agent is handed: a new page, a change in the code, a requirement not built yet, a failing check
and a review.[^tasks] `wiki sync` copies it into the project, where agents read
it.[^sync] Some of the rules it teaches are enforced by the [Checks](checks.md). **It forbids an agent to
invent**: everything on a page comes from the code, the owner's own words, or an outside service's own
documentation, and a fact none of these gives is marked `{missing}` or left out.[^invent]

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
changes no other setting.[^record]

**`wiki check` fails while that record is missing or names a different release**, and it says to run
`wiki sync`.[^version] A newer release can add a check, and a new check finds old pages; the record makes
that failure expected rather than surprising.[^version]

[^files]: `src/builder/cli.py` — `SKILL_NAME` names the skill; `sync()` copies every markdown file under
    `SKILL`, which `src/builder/build.py` finds with `skill_dir()`.
[^contents]: `src/skill/` — `SKILL.md`, and in `references/` the rule files `naming-and-grammar.md`,
    `infobox.md`, `reference-pages.md` and `flowcharts.md` and the worked examples `page-standard.md`, one
    ordinary page, and `reference-standard.md`, a command and an endpoint.
[^tasks]: `src/skill/SKILL.md` — the Tasks section, one list of steps for each of those five tasks.
[^sync]: `src/builder/cli.py` — `sync()`.
[^invent]: `src/skill/SKILL.md` — the Truthfulness section, whose first rule is never to invent, and the
    last item of its definition of done.
[^home]: `src/builder/cli.py` — `skill_home()` tries `.agents/skills`, then `.claude/skills`, and falls
    back to `.claude/skills`.
[^written]: `src/builder/cli.py` — `SKILL_NAME` names the folder; `sync()` compares each file's text before
    writing it, and deletes nothing.
[^skilldir]: `src/builder/cli.py` — `skill_home()` joins a given folder to the project root before trying
    either convention.
[^noskill]: `src/builder/cli.py` — `sync()` skips the copy when `skill` is false; `main()` puts
    `--no-skill` and `--skill-dir` in one mutually exclusive group.
[^record]: `src/builder/config.py` — `record_version()` replaces the `version` line inside the `[tool]`
    table, adds one under its header or appends the table, and refuses to write a file that would read
    differently anywhere outside `[tool]`; `src/builder/cli.py` — `sync()` prints the recorded release.
[^version]: `src/builder/build.py` — `version_problems()`, called from `check()`.
