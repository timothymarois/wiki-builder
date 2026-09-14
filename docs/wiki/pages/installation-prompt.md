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
  { label = "Instructions", value = "Installation" },
  { label = "Skill", value = "writing-wiki-pages", cite = "skill" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Finished", value = "wiki check reports 0 problems", cite = "check" },
]
+++

The prompt below sends an agent to [Installation](installation.md) to install the tool, then has it write
the project's first pages by the skill that installation puts in the project.[^skill] The agent is done
when `wiki check` reports no problems.[^check] The prompt names nothing about the project it is used in,
and checking the wiki once it exists has its own [Review prompt](review-prompt.md).

## Prompt

```text
Install wiki-builder in this project and start its wiki.

1. Before changing anything, read this project's agent instructions (AGENTS.md, CLAUDE.md or
   similar) and run `git status`. Ask me before anything those instructions say needs approval.
2. Follow the installation guide exactly. It is published as markdown, as a web page, and in the
   tool's repository; read whichever you can reach:
   https://wiki-builder.marois.dev/installation/index.md
   https://wiki-builder.marois.dev/installation/
   https://github.com/timothymarois/wiki-builder/blob/main/docs/wiki/pages/installation.md
   Wherever it says TAG, use the newest release tag:
   git ls-remote --tags https://github.com/timothymarois/wiki-builder
3. Once `wiki sync` has run, load the writing-wiki-pages skill it installed and read it in full,
   references included. Write the first pages by it: a brief, then a page or a section for everything
   in the code a person can use, configure or notice. Never invent: every statement comes from the
   code or from me, and a fact neither gives is marked {missing}. Anything I describe that is not built
   yet is written on its page too, every statement of it marked {missing} until code does it. New pages
   are drafts; list their intents for me to approve.
4. Finish when `wiki check` reports 0 problems.

Report the release tag used, every file created or changed, the output of the last `wiki check`, each
draft page with its intent, and anything you could not find in the code. Do not commit or push unless I
ask.
```

[^skill]: `src/builder/cli.py` — `SKILL_NAME` names the skill, and `sync()` copies it into the project.
[^check]: `src/builder/cli.py` — `run()` returns 1 when `check()` finds a problem.
