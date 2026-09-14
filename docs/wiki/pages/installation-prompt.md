+++
title = "Installation prompt"
subtitle = "a prompt that has an agent install wiki-builder in a project"
status = "approved"
goals = false
intent = """
The installation prompt exists so that an owner can have their own agent install wiki-builder in any
project and start its wiki correctly, without learning the tool first. The agent should finish with a wiki
that covers what the code does and passes its checks, and first pages whose intents wait for the owner's
approval.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Skill", value = "writing-wiki-pages", cite = "skill" },
  { label = "Commands", value = "wiki sync, wiki build, wiki check", cite = ["sync", "check"] },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Required files", value = "wiki.toml, goals.md, every page a section lists", cite = ["sync", "nav"] },
  { label = "Finished", value = "wiki check reports 0 problems", cite = "check" },
]
+++

The prompt below takes an agent from a project with no wiki to one that covers everything its code does
and passes `wiki check`, following the steps [Installation](installation.md) describes. It works in any
project, and names nothing about the one it is used in. Checking the wiki once it exists has its own [Review prompt](review-prompt.md).

## Prompt

```text
Install wiki-builder in this project and start its wiki. wiki-builder renders markdown pages into a
wiki a person can read, and refuses what makes documentation rot: a sentence that cites nothing, a
heading that asks a question, a page longer than anyone will read. Its source is
https://github.com/timothymarois/wiki-builder.

## Before starting

1. Read the project's agent instructions (AGENTS.md, CLAUDE.md or similar), its README and any
   existing documentation. Note what the project is, who reads its documentation, and anything the
   instructions say needs approval, such as new scripts, CI changes or edits to agent instructions.
2. Run `git status`, and say what is already changed before you change anything.
3. Find the newest release tag of wiki-builder, and use it wherever TAG appears below:
   git ls-remote --tags https://github.com/timothymarois/wiki-builder
4. Confirm Python 3.11 or newer is available.

## Install

1. Add a wrapper script that runs the pinned release, so every person and agent runs the same one, and
   make it executable:

   #!/bin/sh
   # scripts/dev-wiki.sh
   set -eu
   WIKI_VERSION=TAG
   ROOT="$(cd "$(dirname "$0")/.." && pwd)"
   exec uvx --from "git+https://github.com/timothymarois/wiki-builder@$WIKI_VERSION" \
        wiki "$@" --root "$ROOT"

   The script needs uv. A project without uv installs the release with pip instead,
   pip install "git+https://github.com/timothymarois/wiki-builder@TAG", and runs `wiki` directly.

2. Create docs/wiki/wiki.toml, with the project's name and a first section. Every page a section lists
   must exist, or the build stops.

   [site]
   name = "PROJECT NAME"

   [[section]]
   title = "Start"
   pages = ["index", "goals"]

3. Create docs/wiki/pages/goals.md, which collects every page's intent, and docs/wiki/pages/index.md,
   the front page. Both are pages about the wiki itself, so both say goals = false:

   +++
   title = "Goals"
   status = "approved"
   goals = false
   intent = """
   This page collects what each part of the project is for.
   """
   +++

   What each part is for.

   index.md takes the same shape: the project's name as its title, an intent saying the front page
   sends a reader to the part of the project they came for, and a link to [Goals](goals.md).

4. Add docs/wiki/site/ to .gitignore. The rendered site is generated, and never committed.
5. Run `./scripts/dev-wiki.sh sync`. It writes the writing-wiki-pages skill into .agents/skills, or
   into .claude/skills when there is no .agents/skills, and records the release in wiki.toml.
6. Run `./scripts/dev-wiki.sh build`, then `./scripts/dev-wiki.sh check`. The check must report
   0 problems. Commit docs/wiki/UPDATED.toml with the pages; the build writes each page's date there.

## First pages

1. Load the writing-wiki-pages skill you just installed, and read its references in full.
2. Draft a Brief page: what the project is, who it is for, and how it works.
3. Inventory the code before planning any other page, working from the code and not from existing
   documentation, which may already have gaps. List everything a person can use, configure or notice:
   commands and options; endpoints, public functions, events and webhooks; settings files, their keys
   and environment variables; stored data and fields; refusals, error messages, exit and status codes
   and limits; scheduled jobs, workflows, builds and deployments; outside services; roles and
   permissions. Leave out internals a reader never meets, such as private helpers and test code.
4. Plan the pages so every inventory item has a home, a page or a section of one, then draft them and
   list each in a section of wiki.toml. Code no page mentions is a gap, as much as a page that is wrong.
5. Read the code for every claim. Every sentence carries a footnote naming the file and function where
   the thing happens, or the documentation of an outside service for how that service behaves, or
   {missing} when nothing can be found. Never guess.
6. Every intent says what the thing is for, not how it works. Intents are the owner's to approve, so
   give each new page status = "draft", and list every intent in your report.
7. Run build and check until check reports 0 problems. Then read the claims check lists as having no
   source, and try once more to cite each one.

## Continuous integration

Only if the project uses GitHub Actions and the owner agrees: add a workflow that fails on any wiki
problem. TAG must be a release that includes the action.

   # .github/workflows/wiki.yml
   name: wiki
   on: [push, pull_request]
   jobs:
     check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: timothymarois/wiki-builder@TAG

## Report

- The release tag used, and every file created or changed.
- The output of the last check: pages, problems, sources cited, claims marked as having no source.
- The inventory as counts: items found, and items documented. Any item left without a page, and why.
- Every draft page with its intent, for the owner to approve.
- Anything you could not determine from the code, and where you looked.
- A suggested line for the agent instructions, keeping docs/wiki true in the same change as the code.
  Suggest it; do not add it without approval.

Do not commit or push unless the owner asks.
```

## Requirements

`wiki sync` stops when there is no `wiki.toml`, so the prompt writes that file before running it.[^sync]
A build stops when a section lists a page that does not exist, which is why `index.md` is written with
`goals.md`.[^nav] `wiki check` exits with a failure while any problem remains, so the agent is not done
until it reports none.[^check] The workflow in the last step uses the action described on
[Continuous integration](continuous-integration.md).

[^sync]: `src/builder/config.py` — `record_version()`, called by `sync()` in `src/builder/cli.py`, refuses
    a wiki with no `wiki.toml`; `skill_home()` in `src/builder/cli.py` chooses `.agents/skills`, then
    `.claude/skills`.
[^nav]: `src/builder/build.py` — `render_nav()` refuses a section listing a page that does not exist, and
    `write_site()` refuses a wiki with no `goals.md`.
[^check]: `src/builder/cli.py` — `run()` returns 1 when `check()` finds a problem.
[^skill]: `src/builder/cli.py` — `SKILL_NAME` names the skill, and `sync()` copies it into the project.
