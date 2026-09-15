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
does that no page mentions. The check never reads inside a code block, so the prompt is also the only
check a diagram gets.[^fenced] It works in any project
that uses wiki-builder, and names nothing about the project it is used in. Installing the tool in the first
place has its own [Installation prompt](installation-prompt.md), and reviewing how the pages are grouped
and laid out has its own [Organization prompt](organization-prompt.md).

Before handing the prompt to an agent, replace `PART` with the part to review: a sidebar section, a page
with the pages beneath it, or a component of the project. Left as it is, the prompt has the agent choose
the section audited longest ago, which keeps a large wiki to one careful review at a time. Pages are
audited with [wiki audit](commands/audit.md).

## Prompt

```text
Review this project's wiki against the project itself, and report what is wrong, undocumented, out of
date, uncited or badly written. The wiki is read instead of the source, so a page that disagrees with the code is
worse than no page. When they disagree, the page is wrong, unless the owner says otherwise.

## Scope

Review only PART, and the code it describes: a sidebar section, a page with the pages beneath it, or one
component of the project. If PART was left as it is, choose the part yourself: read docs/wiki/UPDATED.toml
and wiki.toml, and take the sidebar section whose pages were audited longest ago, counting a page never
audited as the oldest. Review the whole wiki only when the owner asks for it.

## Before starting

1. Load the writing-wiki-pages skill, and read SKILL.md and every file in its references folder in
   full, flowcharts included. They are the standard you are reviewing against.
2. Read the project's agent instructions (AGENTS.md, CLAUDE.md or similar), the wiki's brief, and
   docs/wiki/wiki.toml.
3. Run `wiki check`, through the project's wrapper script if it has one, and record the result:
   problems, sources cited, claims marked as having no source. A passing check is where the review
   starts, not a verdict. `wiki check` writes nothing; run every other command, and every experiment,
   in a scratch copy of the project, because a build rewrites the site and the page dates, and serving
   opens a browser.
4. Do not edit any page. Report findings; the owner decides what changes. The only thing a review
   writes is its audit record, once the report is done.
5. Note the commit you are reviewing. A file that changes while you work is read again before you
   report on it.

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
- Every claim that a check refuses or accepts something: build a small wiki in the scratch copy that
  breaks the rule, and watch what the check does. Pages go wrong at the edges: abbreviations, links,
  empty values, a file that does not exist.
- Nothing is invented. Every behaviour, reason, example and name traces to the code, the owner's own
  words or an outside service's own documentation; a sentence with none of those is false until a
  source is found.

### 2. Coverage
Behaviour that no page mentions is as wrong as a page the code contradicts: a reader using the wiki
instead of the source never learns it exists. Coverage means behaviour and requirements. Build the list
from the code, never from the wiki, so the wiki cannot hide its own gaps.
- Inventory the behaviour a person meets in the part under review, from the code itself:
  - entry points: commands, subcommands, options, arguments, flags;
  - interfaces: endpoints, public functions and classes, events, webhooks, messages;
  - configuration: a setting only where it changes behaviour a person notices, and a settings file only
    where the project defines it and a person edits it;
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

### 5. Diagrams
The check never reads inside a code block, so a mermaid diagram is checked only here, against the
Flowcharts reference.
- Truth: every box is a step the cited code takes, every diamond a condition it tests, and every arrow
  the order it runs in. Nothing is drawn that the code does not do. The sentence before the diagram
  carries the citation, and the page's text still says everything the diagram shows.
- Shape: one question, answered in about ten steps; the right kind, a flowchart, sequence or state
  diagram; each shape used only for its one meaning; top to bottom or left to right, the main path
  straight, no crossing lines, every loop labelled; one start, an end for each outcome, and every path
  reaching an end.
- Labels and grammar: a step is a verb and its object in sentence case, with no full stop; a decision is
  a short yes-or-no question, every exit is labelled, and yes and no leave in the same order in every
  diagram; an end is an outcome, as a noun phrase; labels use the page's own words, no abbreviations,
  in about five words; `accTitle` is a noun phrase and `accDescr` is whole sentences, spelled like the
  rest of the wiki; a label says `End`, never `end`.
- Drawing: where a browser is available, open the built page and confirm the diagram draws; say so if
  you could not.

### 6. Writing
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

### 7. Structure
- Every page is reachable from the sidebar. Unfinished pages are drafts; nothing unfinished is approved.
- A page sits in the section a reader would look in first.
- Reference pages (commands, endpoints, settings files) follow the reference standard: usage, every
  option or field with its type and default, output, errors and exit codes, and an example.

## Threshold

A finding earns its place only if fixing it changes what a reader believes, does or can find. Name that
change before reporting a finding; if you cannot, drop it.
- Report: a false or untraceable claim; something a reader needs that no page says; a name, heading,
  label or diagram that breaks a named rule of the skill; wording a reader could take two ways; one
  term used for two things, or two terms for one.
- Never report: rewording a sentence that is already true, cited and within the skill's rules; a
  synonym you prefer; reordered clauses, sentences or rows; punctuation or style the skill does not rule
  on; a {missing} mark on something the owner asked for that is not built yet, which is correct as it
  is; any change whose only effect is that the page reads more the way you would write it.
- A writing finding names the rule it breaks, in the skill's words, and what a reader would get wrong
  because of it. Without both it is a preference, and a preference is not a finding.
- Report a pattern once, with every place it occurs, not once for each page.
- The fix is the smallest change that corrects the fault. The sentences around it stay as they are.

## Report

Keep it short. The owner reads it to decide what to fix, not to follow your work: no preamble, no
method, no quoted evidence.

1. One line: the part reviewed, and why if you chose it; the commit; whether `wiki check` passed; and
   how many findings of each severity.
2. What to fix, most severe first, one line each:
   page.md:line — severity — what is wrong — the fix, as the corrected text or the citation to add.
   Name the code or the outside page only where the fix needs it. A pattern is one line, listing every
   place it occurs.
3. For the owner, one line each: code that may be what is wrong, an intent a page now contradicts, and
   anything that needs an approval.
4. Not reviewed, one line each, with why.

Severities, most severe first: false, the page says what the code does not do; undocumented, a reader
needs something no page says, or a stated requirement is on no page; uncited, a claim with no citation
or one that does not support it; stale, a {missing} mark that can now be cited, or something renamed or
removed; writing, a name, sentence or diagram that breaks a named rule of the skill, which the line
names.

Leave out pages with no findings and how each finding was verified. Report nothing you have not checked
against the code, and no preferences.

Then run `wiki audit` with every page that has no finding, leaving out any page that says
goals = false, which cites nothing and is never audited. A page with a finding is audited once it is
fixed.
```

## Fixing

To have the agent fix what it finds instead of reporting it, replace the fourth step of "Before starting"
with: "Fix each finding, change nothing a finding does not name, keep `wiki check` passing, run
`wiki build` and then `wiki audit` on every page reviewed that cites anything, and list every change you made, one line
each." An edit that fixes nothing still moves the page's date, and tells every reader
the page changed when it did not.[^dates] Intents stay out of reach either way, because changing one
changes what a page is for, and that is the owner's decision.

[^presence]: `src/builder/build.py` — `uncited_problems()` accepts a sentence containing any footnote or
    the missing mark, and reads nothing the footnote names.
[^fenced]: `src/builder/build.py` — `page_statements()` blanks fenced code with `FENCED` before reading
    sentences.
[^dates]: `src/builder/build.py` — `write_site()` moves a page's date in `UPDATED.toml` whenever its
    markdown changes.
[^skill]: `src/builder/cli.py` — `SKILL_NAME` names the skill, and `sync()` copies `SKILL.md` and its
    `references` into the project.
[^check]: `src/builder/build.py` — `check()` gathers every problem; `citation_counts()` and
    `missing_marks()` give the counts and marks the prompt has the agent record.
