+++
title = "Organization prompt"
subtitle = "a prompt that has an agent review how a wiki's pages are grouped and laid out"
status = "approved"
goals = false
intent = """
The organization prompt exists so that any agent can review how a project's wiki is organized, so that
people understand how everything works and the organization feels intentional. The review changes
nothing; each family's layout is approved before any page moves.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Skill", value = "writing-wiki-pages", cite = "skill" },
  { label = "Command", value = "wiki check", cite = "check" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Edits", value = "none, findings only", cite = "families" },
  { label = "Approval", value = "every layout, before any page moves", cite = "families" },
]
+++

The prompt below has an agent review how a wiki is organized: which pages are about things of one kind,
whether each such family shares one layout of headings and infobox labels, whether its parent page lists
and compares its members, and whether every page sits where a reader would look for it.[^families] Every
proposal waits for approval, because a family's layout decides what each of its pages covers.[^families]
It works in any project that uses wiki-builder, and names nothing about the project it is used in. Checking
what the pages say against the code has its own [Review prompt](review-prompt.md).

Before handing the prompt to an agent, replace `PART` with a sidebar section, or a page with the pages
beneath it. Left as it is, the prompt has the agent review the whole sidebar, one section at a time.

## Prompt

```text
Review how this project's wiki is organized, and report every change that would let a reader compare
pages about things of one kind and find each fact where they expect it. The readers are the
stakeholders, the product owner, the engineering team and, for pages marked for users, customers. The
review changes nothing: each family's layout needs approval before any page moves.

## Scope

Review only PART: a sidebar section, or a page with the pages beneath it. If PART was left as it is,
review the whole sidebar, one section at a time.

## Before starting

1. Load the writing-wiki-pages skill, and read SKILL.md and, in its references folder,
   page-families.md, reference-pages.md, infobox.md and naming-and-grammar.md in full. They are the
   standard you are reviewing against.
2. Read the project's agent instructions (AGENTS.md, CLAUDE.md or similar), the wiki's brief, and
   docs/wiki/wiki.toml.
3. Do not edit any page. Do not run `wiki build`, `wiki serve` or `wiki audit`, which rewrite the page
   dates; `wiki check` writes nothing and may be run.
4. Run `wiki families`, which lists every parent whose children declare no layout, with each child's
   headings. Then build an inventory with a script, not by eye. For every page under docs/wiki/pages: its path, title,
   parent (the page its folder is named after), sidebar section, second-level headings in order outside
   code blocks, and infobox group and label names. The front matter between the +++ fences is TOML.

## What to check

### 1. Families
- Every family: children of one parent that are about things of one kind. The test is the parent's
  title followed by "such as" and two of its children's titles.
- Families that exist but are scattered: pages about things of one kind under different parents or
  sidebar sections, with no parent page listing them.
- Groups presented as one kind that are not. Each of those pages keeps the shape its own subject needs.

### 2. Layouts
- For each family, every place its members differ: headings, heading order, infobox groups and labels.
- One label used for two different facts, or two labels for one fact, across the family.
- A proposed layout for each family, drawn from the questions each reader asks of every member, never
  by averaging the headings the members have now: the second-level headings in order, and the infobox
  groups and labels in order.
- Each member mapped onto that layout: every section renamed, merged, moved or left out, and every
  sentence with no place in the layout, with the page it would move to.
- A command, endpoint, published function, settings file, event or form takes the layout in
  references/reference-pages.md.

### 3. Parent pages
- The parent's lead names the sections every member covers.
- The parent lists every member in one table, a row per member and a column per value the members
  share. Propose the columns from values the member pages already state.

### 4. Placement
- Each page sits under the parent, and in the sidebar section, a first-time reader would look in.
- A nested page's title names only what sets it apart within its parent.
- A fact stated on several pages belongs on one of them, and the others link to it. Name the page that
  owns it and every page that repeats it.
- The sidebar sections, in order, lead a first-time reader from what the system is for to how each part
  of it works.

## Threshold

A finding earns its place only if acting on it lets a reader compare two pages, find a fact where they
expect it, or reach a page they could not find. Name that change before reporting a finding; if you
cannot, drop it. Never propose a layout for pages that are not one kind, a rename that only matches
your own preference, or a new fact: every proposal moves or renames what the pages already state.

## Report

1. One line: the part reviewed, the commit, and how many families you found.
2. Each family, the largest first: its members, where they differ, the proposed layout written as the
   [family] table its parent would declare, and each member's mapping onto it.
3. Parent pages to add or change: the sections the lead names, and the table's columns.
4. Placement findings, one line each: the page, what is wrong, and the move.
5. For approval, one line each: every new page that needs an intent, every sentence a change would
   cut, and every layout awaiting approval.

Rank every finding by how much it changes what a reader can compare or find.
```

## Fixing

To have the agent apply what was approved instead of reporting it, replace the third step of "Before
starting" with: "Apply only the layouts and moves I approve, declaring each layout as `[family]` on its parent,
moving every sentence with its citation and
cutting none, run `wiki check` until it reports 0 problems, and list every page you changed, one line
each." A parent page the agent adds is a draft until its intent is approved.[^draft]

[^families]: `src/skill/references/page-families.md` — the families, layout and parent page rules the prompt
    reviews against, where each layout is shown for approval before any page is rewritten to it.
[^skill]: `src/builder/cli.py` — `SKILL_NAME` names the skill, and `sync()` copies `SKILL.md` and its
    `references` into the project.
[^check]: `src/builder/build.py` — `check()` builds the site in a temporary folder and gathers every
    problem.
[^draft]: `src/builder/build.py` — `read_pages()` defaults a page's `status` to `"draft"`.
