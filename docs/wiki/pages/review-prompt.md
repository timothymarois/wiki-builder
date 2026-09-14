+++
title = "Review prompt"
subtitle = "a prompt that has an agent check a wiki against its project"
status = "approved"
goals = false
intent = """
The review prompt exists so that an owner can have any agent check a project's wiki against the project
itself, and get back everything false, undocumented, out of date, uncited or badly written, without reading the
code themselves. The review changes nothing; the owner decides what is fixed.
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
  { label = "Edits", value = "none, findings only", missing = true },
  { label = "Severity", value = "false, undocumented, uncited, stale, writing", missing = true },
]
+++

`wiki check` proves that every sentence carries a citation, not that the citation is true: a sentence with
any footnote passes, and the check never opens the file the footnote names.[^presence] The prompt below
covers the rest, by having an agent read each cited source against its sentence, and list what the code
does that no page mentions. It works in any project
that uses wiki-builder, and names nothing about the one it is used in. Installing the tool in the first
place has its own [Installation prompt](installation-prompt.md).

## Prompt

```text
Review this project's wiki against the project itself, and report what is wrong, undocumented, out of
date, uncited or badly written. The wiki is read instead of the source, so a page that disagrees with the code is
worse than no page. When they disagree, the page is wrong, unless the owner says otherwise.

## Before starting

1. Load the writing-wiki-pages skill and read its references in full: page standard, naming and
   grammar, reference pages, reference standard. They are the standard you are reviewing against.
2. Read the project's agent instructions (AGENTS.md, CLAUDE.md or similar), the wiki's brief, and
   docs/wiki/wiki.toml.
3. Run `wiki check`, through the project's wrapper script if it has one, and record the result:
   problems, sources cited, claims marked as having no source. A passing check is where the review
   starts, not a verdict.
4. Do not edit anything. Report findings; the owner decides what changes.

## What to check

Work page by page for truth, citations, writing and structure: read the page, then the code it
describes. Coverage works the other way, from the code to the wiki.

### 1. Truth
- Every citation: open the file, find the function or setting it names, and confirm it does exactly
  what the sentence says: numbers, defaults, limits, names, exit codes, messages, order of operations.
- Every citation to outside documentation (a host, a platform, a library): open the linked page and
  confirm it still says what the reference claims.
- Every command, option, field, setting and message is spelled exactly as the software spells it. Run
  --help, or the command itself where that is safe, and compare.
- Code samples and example output: run or trace them, and confirm they still work and match.

### 2. Coverage
Code that no page mentions is as wrong as a page the code contradicts: a reader using the wiki instead
of the source never learns it exists. Build the list from the code, never from the wiki, so the wiki
cannot hide its own gaps.
- Inventory everything a person can use, configure or notice, from the code itself:
  - entry points: commands, subcommands, options, arguments, flags;
  - interfaces: endpoints, public functions and classes, events, webhooks, messages;
  - configuration: settings files and their keys, environment variables, defaults;
  - data: stored models and fields, file formats, anything written or read;
  - behaviour: validations and refusals, error messages, exit and status codes, limits, retries;
  - operations: scheduled and background jobs, workflows, builds, deployments;
  - integrations: outside services called, and what the project needs from each;
  - access: roles, permissions, authentication.
- Search the wiki for each item. Mark it documented (name the page and section), mentioned in passing
  without its behaviour, or undocumented.
- Walk the other way too: list the source files no reference cites. A file with public behaviour and no
  citation anywhere is usually an undocumented feature.
- Leave out internals a reader never meets: private helpers, refactoring seams, test code. Say what you
  excluded, so the owner can disagree.

### 3. Currency
- Pages describing behaviour that no longer exists, or has been renamed.
- Every {missing} mark: search for an implementation that now exists, and report the citation that
  should replace the mark.
- Requirements the owner has stated (agent instructions, the brief, issues, commit messages) that
  appear on no page. Each belongs on a page, marked {missing} until it is built.
- The codemap or file map, if the project has one, against what is on disk.

### 4. Citations
- Every sentence states something and carries its own citation or {missing}, and the citation supports
  that sentence, not a neighbouring one.
- A reference names the file and the function or setting where the thing happens. How an outside
  service behaves is cited to that service's own documentation. A reference to another document, a
  plan, a ticket or a test is wrong.
- Every infobox row cites a footnote the page's text cites for the same fact, or is marked missing.
- A reference that exists but does not establish its claim is uncited. Say so.

### 5. Writing
- The intent says what the thing is for, not how it works, in two to four sentences, and every sentence
  on the page serves it. Report sentences that serve nothing, and intents that have outgrown one page.
- The lead answers the page on its own; each section's first line answers the section.
- Titles, headings, categories and infobox labels are noun phrases in sentence case: never a question,
  a verdict or a verb, never opening with "The", never pointing at the page ("This site").
- Prose names things instead of pointing at them ("this repository", "this tool").
- No hedges, minimisers, marketing, or vague verbs ("handles", "manages", "supports").
- Names the software owns are in code formatting; anything longer than one line is a code block.
- One term per concept across the whole wiki. Report synonyms for the same thing.
- Grammar and spelling, in one English variant.
- A subject that lives on another page is linked, not retold.

### 6. Structure
- Every page is reachable from the sidebar. Unfinished pages are drafts; nothing unfinished is approved.
- A page sits in the section a reader would look in first.
- Reference pages (commands, endpoints, settings files) follow the reference standard: usage, every
  option or field with its type and default, output, errors and exit codes, and an example.

## Report

Group findings by page, most severe first:
1. False: the page says something the code does not do.
2. Undocumented: the code does something a reader needs that no page says, or a requirement is
   absent. List each item from the coverage inventory, with where it lives in the code and the page it
   belongs on.
3. Uncited: a claim with no citation, or a citation that does not support it.
4. Stale: a {missing} mark that can now be cited, or something renamed or removed.
5. Writing: naming, grammar, structure, voice.

For each finding give the page and line; the sentence or row, quoted; what the code or source actually
shows, with its file and function or outside page; and the fix, as the corrected sentence or the
citation to add. Say which findings you verified by running something and which by reading alone, and
what you did not review and why.

End with: pages reviewed; the coverage inventory as counts (items found, documented, mentioned only,
undocumented); findings at each severity; {missing} marks that could be cleared; and whether
`wiki check` passed. Report nothing you have not checked against the code, and no preferences. A page
that is accurate, current, cited and well written gets one line saying so.
```

## Fixing

To have the agent fix what it finds instead of reporting it, replace the fourth step of "Before starting"
with: "Fix each finding, keep `wiki check` passing, and list every change you made." Intents stay out of
reach either way, because changing one changes what a page is for, and that is the owner's decision.

[^presence]: `src/builder/build.py` — `uncited_problems()` accepts a sentence containing any footnote or
    the missing mark, and reads nothing the footnote names.
[^skill]: `src/builder/cli.py` — `SKILL_NAME` names the skill, and `sync()` copies `SKILL.md` and its
    `references` into the project.
[^check]: `src/builder/build.py` — `check()` gathers every problem; `citation_counts()` and
    `missing_marks()` give the counts and marks the prompt has the agent record.
