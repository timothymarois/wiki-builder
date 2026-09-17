+++
title = "Skill"
subtitle = "the writing-wiki-pages instructions that wiki sync puts in a project"
status = "approved"
intent = """
The skill exists so that an agent writing a page, in any project, writes it by the approved rules,
without each project inventing its own. A change to those rules should reach a project only when
that project asks for it, and arrive where the project reviews it.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Name", value = "writing-wiki-pages", cite = "files" },
  { label = "Command", value = "wiki sync", cite = "sync" },
]

[[infobox]]
group = "Contents"
rows = [
  { label = "Instructions", value = "SKILL.md", cite = "contents" },
  { label = "Worked examples", value = "page-standard.md, page-families.md, reference-standard.md", cite = "contents" },
  { label = "Rule files", value = "naming-and-grammar.md, infobox.md, reference-pages.md, flowcharts.md, charts.md", cite = "contents" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Sources", value = "the code, the stated requirements, an outside service's documentation", cite = "invent" },
  { label = "Readers", value = "stakeholders, product owner, engineering team, customers", cite = "readers" },
]
+++

The **skill**, `writing-wiki-pages`, is the instructions an agent follows to write a page: `SKILL.md`,
and a `references` folder of rules and worked examples beside it.[^files][^contents] `wiki sync` copies it
into a project, as [Delivery](skill/delivery.md) describes.[^sync] Some of the rules it teaches are
enforced by the [Checks](checks.md).

## Readers

The skill writes one page for four readers, the stakeholders, the product owner, the engineering team and,
in some wikis, customers, so that each learns what the system does without reading its code.[^readers] One
page serves all four; a page for customers names no team, agent, function, field or
branch.[^readers]

## Intent

Every page opens with an intent, two to four sentences from the stated requirements saying what the thing
is for, and every sentence on the page must serve it.[^intent]

## Sources

**The skill forbids an agent to invent**: everything on a page comes from the code, the stated requirements,
or an outside service's own documentation, and a fact none of these gives is marked `{missing}` or left
out.[^invent] Every sentence cites the file and function where the thing happens, or carries
`{missing}`.[^cite]

## Page standard

A page gives its answer first, in its lead and in the first line of each section, and states
consequences, not mechanisms.[^standard] A subject that outgrows its
page becomes a child page, not another heading.[^split]

## Naming

Every title, heading, infobox label and category is a noun phrase naming the answer a reader wants, never
the writer's question, and a name the software owns is written exactly as the software spells it.[^naming]

## Page families

**Pages about things of one kind share one layout**: the same headings in the same order and the same
infobox labels, under a parent page that lists and compares them.[^families]

## Reference pages

A page for a command, endpoint, published function, settings file, event or form takes a fixed set of
sections, gives every input its type, default and meaning, and quotes every error word for word.[^reference]

## Infobox

The infobox gives a thing's names, figures and rules as labeled rows, and every row cites a
footnote the prose also cites.[^infobox]

## Diagrams

A flow, a sequence or a set of states is drawn as a Mermaid diagram of about ten steps, and every
step is something the cited code does.[^diagrams] A chart draws figures the page states and
cites.[^charts]

## Exclusions

A page never carries a name only the code knows, a unit a reader cannot feel, a task or
ticket, a gap list, an apology, marketing, or an attribution to whoever asked for a rule.[^exclusions]

## Coverage

Every behavior a person meets, and every stated requirement, has a page or a section, found by
listing the code rather than the wiki.[^coverage] A requirement not built yet is written on its page and
marked `{missing}`.[^missing]

## Tasks

`SKILL.md` gives the steps for each task an agent is handed: a new page, a change in the code, a
requirement not built yet, a failing check, a review and organizing pages.[^tasks]

[^files]: `src/builder/cli.py` — `SKILL_NAME` names the skill; `sync()` copies every markdown file under
    `SKILL`, which `src/builder/build.py` finds with `skill_dir()`.
[^contents]: `src/skill/` — `SKILL.md`, and in `references/` the rule files `naming-and-grammar.md`,
    `infobox.md`, `reference-pages.md`, `flowcharts.md` and `charts.md` and the worked examples `page-standard.md`, one
    ordinary page, `page-families.md`, a family of notification channels, and `reference-standard.md`, a
    command and an endpoint.
[^sync]: `src/builder/cli.py` — `sync()`.
[^readers]: `src/skill/SKILL.md` — the opening paragraph and the Readers section, whose rules keep one page
    for every reader and keep the team, agents, functions, fields and branches off a page for
    customers; `src/skill/references/page-standard.md` — the eighth step of the self-edit.
[^intent]: `src/skill/SKILL.md` — the Vocabulary entry for an intent, the Intent section, where every
    sentence serves the intent and an intent comes from the stated requirements, and the section on
    approving an intent.
[^invent]: `src/skill/SKILL.md` — the Truthfulness section, whose first rule is never to invent, and the
    last item of its definition of done.
[^cite]: `src/skill/SKILL.md` — the Citations section, where a reference names a file and function, and
    the Citation coverage section, where every sentence carries a citation or `{missing}`.
[^standard]: `src/skill/SKILL.md` — the Page shape section, which answers first, and the Voice section,
    which states the consequence rather than the mechanism; `src/skill/references/page-standard.md` — a
    page written that way beside the same page written badly.
[^split]: `src/skill/SKILL.md` — the Page shape section, whose last rule splits a subject into a child page
    rather than another heading.
[^naming]: `src/skill/SKILL.md` — the Naming section; `src/skill/references/naming-and-grammar.md` — names
    a writer chooses as noun phrases, and names the software owns written exactly as the software spells
    them.
[^families]: `src/skill/SKILL.md` — the Page families section; `src/skill/references/page-families.md` —
    the layout rules, the parent page, and a family done well and badly.
[^reference]: `src/skill/SKILL.md` — the Reference pages section; `src/skill/references/reference-pages.md`
    — a layout for each of those surfaces, and the contract every input and error meets;
    `src/skill/references/reference-standard.md` — a command page and an endpoint page, each done well and
    badly.
[^infobox]: `src/skill/SKILL.md` — the Infobox section; `src/skill/references/infobox.md` — the groups
    Identity, Values and Rules, the keys a row takes, and an example.
[^diagrams]: `src/skill/SKILL.md` — the Diagrams section; `src/skill/references/flowcharts.md` — when a
    diagram is drawn, which kind, and its shapes, direction and labels.
[^charts]: `src/skill/SKILL.md` — the Charts section, whose rules draw only figures the page states and
    cites and refuse one that moves faster than the page; `src/skill/references/charts.md` — when a chart
    beats a table, which kind to draw, where its numbers come from, and how it is labeled.
[^exclusions]: `src/skill/SKILL.md` — the Exclusions table.
[^coverage]: `src/skill/SKILL.md` — the Coverage section, whose first rule inventories from the code, never
    from the wiki.
[^missing]: `src/skill/SKILL.md` — the Missing citations section, where a stated requirement not built yet
    is written now and marked.
[^tasks]: `src/skill/SKILL.md` — the Tasks section, one list of steps for each of those six tasks.
