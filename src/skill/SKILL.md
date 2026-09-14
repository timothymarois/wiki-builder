---
name: writing-wiki-pages
description: Use when writing or changing any page of the wiki under docs/wiki/ — a page, an intent, an infobox, a citation, a picture, a command or API reference page, or the name or wording of anything a person reads there. It supplies how the wiki is built, its vocabulary, the intent contract, naming and grammar, reference pages, what a page may never carry, and the voice. Do not use for engineering documentation written for builders, which follows different rules.
---

# Writing wiki pages

**Read [Page standard](references/page-standard.md) before writing anything.** It holds a page the owner
approved, the same content written badly, and why the difference matters. Rules say what to avoid; only an
example shows what good looks like. A page written from these rules alone comes out **flat, true and
unread** — the failure this skill exists to prevent, and the one that does not announce itself.

**The wiki is for people, not builders.** Its readers are the project's owner, and later its users and
product people. They do not read code and must never need to. Someone who has read the source learns
nothing new from a page; someone who never has understands all of it. Every rule below serves one job:
**the owner sees how the thing works without reading it.**

Nothing here is specific to one project. These rules travel with the wiki into any project that installs
it.

## Wiki structure

You write markdown; the generator writes the site.

| Thing | Where | What it does |
|---|---|---|
| A page | `docs/wiki/pages/**.md` | TOML front matter between `+++` fences, then markdown |
| Its address | its path | `pages/billing/invoices/refunds.md` is `/billing/invoices/refunds/` |
| Its place | its path | it nests under `pages/billing/invoices.md` in the sidebar |
| The sidebar | `docs/wiki/wiki.toml` | sections name only the pages that **start** a branch |
| Pictures | `docs/wiki/images/` | with `PICTURES.toml`, recording what each shows |
| The site | `docs/wiki/site/` | generated, ignored by git, rebuilt before it is served |
| Dates | `docs/wiki/UPDATED.toml` | written by the build; a date moves only when its page does |

```sh
wiki serve    # build, serve, open a browser
wiki check    # what the gate runs
```

Run them through the project's wrapper script if it has one.

**To add a page**, put its file where it belongs: a page in a folder named after another page nests under
it. Name it in `wiki.toml` only when it starts a new branch.

## Vocabulary

Use these words in commits, reviews and conversation. They are the generator's.

- **Page** — one markdown file, one address.
- **Intent** — two to four sentences of front matter saying what the thing is *for*. The contract.
- **Lead** — the body's opening paragraph, before any heading.
- **Infobox** — the panel at the top right: **groups** of **rows**, each a **label** and a **value**.
- **Citation** — a numbered mark in the prose. **Reference** — its entry at the foot of the page.
- **Missing citation** — the red mark for a claim with nothing to cite, written `{missing}`.
- **Category** — a cross-cutting label, in the bar at the foot of a page. Not the sidebar.
- **Reference page** — a page for something a person calls or configures: a command, an endpoint, a
  published function, a settings file.
- **Goals page** — every page's intent, collected. Generated, never written.
- **Source view** — the Source tab, showing a page's own markdown.
- **Audience** — `internal`, the default, or `player`, which `wiki player` builds.

## Intent

Every page opens with an `intent`: what the thing is **for** and what outcome it should produce — never how
it works.

```toml
intent = """
Refunds exist so that a customer who was charged wrongly gets their money back without anyone having to
ask us twice. A refund that needs a support conversation has failed. It should be possible to issue one
in seconds and impossible to issue one by accident.
"""
```

- **Every sentence serves the intent.** One that does not is **cut** — not moved, not shortened.
- **Nothing outgrows its intent.** Anything worth saying that the intent does not cover needs its own page
  and intent, approved by the owner — or it is engineering documentation and does not belong here.
- **A long page means the intent is too broad.** When every sentence serves the intent and the page still
  runs long, split the intent and nest the new page under this one. Cutting good sentences to hit a
  number makes a worse page.

**Write the intent first.** It decides what the page holds; written last, the page gets written twice.
**An intent comes from the owner.** Draft it from their words, mark the page a draft, and ask; never
invent what a thing is for.

## Naming

Naming is most of what makes a page readable, and it goes wrong first. In code a class is a noun and a
function a verb; in an encyclopedia a title is a noun phrase, never a verb or a question. A wiki has no
actions, so **every name on a page is a noun phrase** for a thing a reader wants. The failure is always the
same: the writer names their question instead of its answer.

**Read [Naming and grammar](references/naming-and-grammar.md) before naming anything, before describing a
name the software owns — a field, an option, a setting — and before the last pass over any page.**

### Method

Find the section by its question; name it by the answer.

| The question | Never call it | Call it |
|---|---|---|
| Where does it live? | "Where it is stored" | **Storage**, **Location** |
| Why is it like this? | "Why it works this way" | **Reasoning**, or the reason itself |
| How does it grow? | "How the cache fills up" | **Growth** |
| How long does it last? | "How long it lasts" | **Expiry**, **Lifespan** |
| What does it accept? | "What it takes as input" | **Input**, **Formats** |
| When does it happen? | "When it runs" | **Schedule**, **Timing** |
| What is it for? | "What it is for" | **Purpose**, **Use** |
| What makes it different? | "Two differences, and only two" | **Differences** |
| Is it any good? | "Fast enough to matter" | the subject: **Speed** |
| What does this file show? | "A worked page" | **Page standard** |

A gerund is a noun and is fine: **Caching**, **Signing out**. A gerund phrase is usually the question in
disguise: "Getting started" wants to be **Setup**.

### Tests for a name

From the encyclopedia's title policy, for titles, headings and categories alike. A name is:

- **Recognisable** — a reader who knows the subject, without being expert in it, knows what this is.
- **Natural** — what they would say aloud, and what another page would link to it as.
- **Precise** — this subject, not a neighbour. "Limits" is a size on a page about uploads and a rate on
  one about the API; the page supplies the subject.
- **Concise** — no longer than it takes to identify the thing.
- **Consistent** — the same kind of thing named the same way on every page. If one page says **Storage**,
  no page says "Where data is kept".

### Names on a page

- **A page title** is the thing the page is about: **Refunds**, **Sessions**, **Nightly run**. No leading
  "The" unless it is part of the name.
- **A heading** is the same, one level down. The gate refuses a question or a verdict.
- **A category** is a plural noun for a set: **Background jobs**, not "Jobs that run in the background".
- **An infobox label** is a noun phrase naming a property, which the value gives: **Expiry** · 30 minutes.
- **Nothing points; everything is named.** "This site", "Our setup" and "These options" point at the page
  instead of naming the thing: **Domain**, **Setup**, **Options**. In prose, "this repository" or "this
  wiki" means nothing to a reader who arrived from a search: use the project's name. The gate refuses both.

**When no good name exists, the section is wrong, not the name.** A heading that will not fit in two words
is usually two sections, or one that has not decided what it is about.

## Page shape

**Answer first, detail after**, at every level: the lead answers the page, a section's first line answers
the section, a sentence's first clause answers the sentence. A reader who stops early is still right.

- **The lead stands alone.** Whoever reads only the first paragraph gets the true shape of the thing,
  surprising fact included.
- **A heading is a label on a drawer**: it names what is inside, so a scanning reader knows whether to stop.
  One or two plain words is usually right.
  - **Never a question.** "Where it is stored" is the writer wondering what belongs there; the reader
    wanted **Storage**. A heading opening How, What, Where, Why or When makes this mistake, and **the gate
    refuses it.**
  - **Never a verdict.** "Fast enough to matter", "Important notes" and "Overview" rate the contents
    instead of naming them. **The gate refuses these too.**
- **Three to five sections.** More, and the page is two pages.
- **Split rather than swell.** A subject that needs its own treatment becomes a child page and a link, not
  another heading; the sidebar nests it.

## Voice

- **The consequence, not the mechanism.** "An expired session does not lose your draft" — not that one
  setting outlives another.
- **Short sentences, ordinary words.** A sentence that needs reading twice is the sentence's fault.
- **No sentence without a statement.** A run-up, a transition, a summary or a restatement states nothing
  a reader can check, so it has nothing to cite — and a sentence with nothing to cite has nothing to
  say. Cut it.
- **Bold what matters**, once or twice a section. If everything is bold, nothing is.
- **A number only where a person would notice it wrong.** "About thirty seconds" beats a precise figure
  nobody can perceive.
- **Units a reader can feel** — seconds, metres, kilograms, days, plain counts. Convert from whatever the
  code uses; never leave that to the reader.
- **A surprising decision gets one clause of reason.** "Expiry is meant to make a stolen session useless,
  not to punish somebody who went to lunch." A reader who knows why does not report it as a bug. The
  reason is the owner's, or a comment's in the code — never one you supply.
- **Link sideways instead of repeating**, in the prose and near the top. A thing belongs on one page, and
  every other page links to it and says so: *"Sessions live in storage, where eviction and replication are
  described; this page covers what a session is for and what it does."* Naming what a page is **not**
  about stops a reader looking for it there. Link a sibling page as `name.md`.
- **Plain present tense, no hedging.** "A session ends thirty minutes after its last request", not
  "sessions will generally tend to expire".
- **Code longer than one line is a code block**, fenced and with its language named: two commands, a
  command and its output, a settings file, a request. One name or one short command inside a sentence
  stays inline, as code.
- **Correct grammar.** Name the actor, make subjects agree with their verbs, point each pronoun at one
  thing, keep lists parallel. The rest, and the words that say nothing, are in
  [Naming and grammar](references/naming-and-grammar.md).

## Reference pages

A **reference page** documents something a person calls or configures: a command, an endpoint, a
published function, a settings file. Every rule above applies; the register changes. The names the
software owns are the content, every input has its type, default and meaning, every error is quoted
exactly, and the bar is that someone can use the surface correctly from the page alone.

**Read [Reference pages](references/reference-pages.md) and
[Reference standard](references/reference-standard.md) before writing one.**

## Exclusions

These are not style preferences. A page carrying any of them has failed its readers.

| Never | Instead |
|---|---|
| A name only the code knows: a field, constant, function or class | The behaviour it produces. A name a person uses — a command, a setting, a file they edit — is given where the page introduces the thing, and in the infobox |
| Ticks, centimetres, internal ids, requirement numbers | Seconds, metres, kilograms, plain counts |
| A task, phase, branch or ticket | Nothing; the reader cannot act on it |
| A gap list, a to-do, "not built yet" as prose | `{missing}` on the claim itself |
| An apology for what is missing | Nothing |
| A restatement of an engineering page | A link to it |
| Marketing, or persuading the reader | Description. A page that argues is in the wrong repository |

**Do not document absence in prose.** A reader who finds no mention of something has learned what they
needed. A section headed "not built yet" turns the wiki into a backlog, and backlogs are read by nobody and
rot fastest.

**A planned change is one short, marked note at the end**, never mixed into the description. A reader must
never wonder whether a sentence describes today or next month.

## Citations

A citation is a numbered mark at the claim, with its reference at the foot. Write it as a markdown
footnote; the generator does the numbering.

```markdown
A session ends thirty minutes after its last request.[^expiry]

[^expiry]: `src/session/expiry.py` — `sweep()` ends a session thirty minutes after its last request,
    and holds its draft for a day afterwards.
```

- **A reference names code**: the file and function where the thing happens — not a requirements page, a
  concepts page or another wiki page. The owner's ruling, 2026-09-14: *"sources must be code, where in the
  code is the source of this reference that satisfies the requirement"*. **The gate refuses a reference to
  a markdown document**: a page of prose is another claim that can be wrong exactly as yours is, and
  citing it turns one error into two.
- **How an outside service behaves is cited to its own documentation** — a host's settings, a platform's
  defaults: the thing the project does not run. Name the publisher, link the page by its title, and say
  what it states. The owner, 2026-09-14: *"references can use external documentation to cite how it
  is"*. A `{missing}` on such a claim means nobody looked in that documentation yet.
- **A reference marks the code; it never links to it.** Outside documentation is the one linked reference. Write `` `src/session/expiry.py` — `sweep()` ``,
  not a markdown link. A link to a source file works only while the site is served from inside the
  repository, and is dead wherever the site is published.
- **Configuration counts as code** where a number lives there: name the function that reads it *and* the
  row.
- **References are the one place a path belongs**, and a player build strips them.
- **Link other pages and pictures relative to your own file**, so the link works in the markdown and in
  the browser. A link to a page the wiki does not have is drawn red, and the gate refuses it: write the
  page, or link to one that exists.

## Citation coverage

**Every sentence is a statement, and carries its own reference.** A sentence states a fact, a behaviour,
a rule or a consequence; one that states none of those adds nothing to the page, and is cut. So every
sentence ends with a citation or `{missing}` — every one, not the surprising ones, and never on the
strength of its neighbour's. The owner, 2026-09-14: *"every statement, fact, requirement, logic, beahvior
mentions all require a citation or unknown citation."*

**The gate refuses a sentence that cites nothing.** A citation after the full stop belongs to its
sentence. A sentence that links to another page is excused, because that page carries the citations.
**Every table row cites in at least one of its cells**, or carries `{missing}`; the header row is exempt, and
one cited row never covers the rows beside it. A list item that is a bare link — the host's own guides, under **External
links** at the end of a page — states nothing and is excused too. Write an outside link as a plain link; the build
opens it in a new tab, marks it `nofollow` and adds the arrow. Only a page about the wiki itself is exempt, because it describes no
behaviour.

A reader uses the wiki **instead of** the source, so a sentence they cannot trace must be taken on faith —
and it looks exactly like one that was checked. **"No source" is a fine answer; silence is not.**

Every build and check prints how many sources each page cites and how many claims it marks as having
none, with totals. `wiki check` names every failing sentence and every marked claim by page and line;
read both before calling a page done.

## Missing citations

Write `{missing}` after the claim, or `missing = true` on an infobox row. A red mark renders where the
citation would be.

It means **nothing was cited**: either the system does not do this yet, or nobody has found where it does.
To a reader both mean the same — do not take this on faith — so one mark serves both. A player never sees
it.

It is the only sanctioned way to say a thing is not built. Use it where a reader would otherwise assume
the thing exists, and sparingly: a page that is mostly red marks was written too early.

## Infobox

The infobox is the page's reference card: a reader glances at it for the thing's name, the values that
govern it and the rules it keeps. It summarises the page, and **never says anything the page does not.**

### Contents

Rows come in three groups, in this order:

| Group | Holds | Rows, for a page about sessions |
|---|---|---|
| **Identity** | The names a person uses to find, run or change the thing, exactly as they type or search for them | Cookie · session_id; Setting · session.timeout |
| **Values** | The figures that govern it — limits, defaults, durations, counts — in units a reader can feel | Expiry · 30 minutes; Size limit · 4 kB |
| **Rules** | Its core logic, each in a phrase: what it refuses, what always happens, what never does | Overflow · refused, never truncated; Signing out · this device only |

- **A named thing opens with its name.** A page about a command, a skill, a setting or a service starts
  with a **Name** row giving the name exactly, so a reader who knows it recognises the page.
- **Identity holds the names a person uses**: what they type, search for, open or configure. Never a
  function, class or internal id; those belong in the references.
- **A group is named for what it holds**: Identity, Values and Rules, or something more precise when every
  row shares it — **Limits**, **Defaults**, **Exit codes**, **Contents**. Never "Info", which names nothing.
- **Leave out** what nobody looks up: every setting there is, a value that needs a sentence, anything the
  thing does not do.
- **Every row cites.** A row carries `cite = "<footnote>"`, naming a footnote the page's prose cites for
  the same fact, and renders with that citation's number. A row with nothing to cite carries
  `missing = true`. **The gate refuses a row with neither, or one citing a footnote no sentence uses**: a
  row is a claim in the most visible place on the page.
- **Two to eight rows.** More is the prose again, as a table.

### Labels and values

A label names a property and its value gives it, so the pair reads as a statement: "Expiry · 30 minutes"
is *the expiry is thirty minutes*.

- **A label is a noun phrase in sentence case**: **Name**, **Expiry**, **Size limit**, **Default port**.
  Never a verb ("Expires"), a question ("How long it lasts") or a clause. Singular for one value, plural
  for a list: **Command** · wiki sync; **Commands** · wiki build, wiki publish.
- **A value is a name, a figure or a short phrase**, with no full stop: a name exactly as typed; a figure
  with its unit, such as 30 minutes or 4 kB; a rule as a phrase, such as "refused, never truncated"; a list
  separated by commas. A value that needs a subject and a verb belongs in the prose.
- **Never a hedge or a yes.** "Configurable", "varies" and "yes" give a reader nothing to check. Give the
  default or the condition, or drop the row.
- **One property, one label, on every page.** If one page says **Command**, no page says "Run with".
- **A `note`** is the one clause that stops a value being misread, such as "after the last request".
  Never a second value.
- **`link = "https://…"`** links the value to an address outside the wiki, such as an author's site. A
  page is linked from the text, never from a row.
- **`missing = true`** renders the red mark beside a value nothing implements, or nobody has found.
- **`guaranteed = "<requirement id>"`** records the requirement a row satisfies, for whoever next checks
  the page against the code. It is never rendered.

```toml
[[infobox]]
group = "Identity"
rows = [
  { label = "Cookie", value = "session_id", cite = "cookie" },
  { label = "Setting", value = "session.timeout", cite = "timeout" },
]

[[infobox]]
group = "Limits"
rows = [
  { label = "Expiry", value = "30 minutes", note = "after the last request", cite = "expiry" },
  { label = "Size limit", value = "4 kB", cite = "size" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Overflow", value = "refused, never truncated", cite = "size" },
  { label = "Signing out", value = "this device only", cite = "signout" },
]
```

[Page standard](references/page-standard.md) sets this infobox beside one that fails, and says why.

## Pictures

A page shows the thing it describes. Put pictures in `docs/wiki/images/`, reference them by a relative
path, and caption every one; a caption is prose and obeys every rule here.

Each picture has an entry in `PICTURES.toml` naming what it depicts. **When a depicted file changes and
the picture has not been redrawn, the gate fails.** Redraw it, or run
`wiki bless <picture> "<why it is still true>"` when the change left the picture true. The reason is the
record that someone looked.

## Truthfulness

The page describes **what the thing actually does**, and nothing else.

**Never invent.** Everything on a page comes from one of three places: **the code**, **the owner's own
words**, or **an outside service's own documentation** for how that service behaves. Nothing else is a
source — not what is typical, what similar tools do, what seems likely, what would make the page
complete, or what you would have built. The owner, 2026-09-14: *"never invents, never makes anything up
that does not already exist, never adds information that either the owner or the code base never
mentioned or given."*

- **No invented behaviour**: no feature, option, default, limit, error, step or edge case the code does
  not have.
- **No invented reasons**: a why comes from the owner, or from a comment or commit in the code, never from
  a plausible guess about what someone intended.
- **No invented requirements, plans or audiences**: only what the owner has said.
- **No invented examples**: every sample, output and message is copied from a real run or from the code.
- **No invented names**: a thing is called what the code or the owner calls it.
- **A gap stays a gap.** Where the page needs a fact nobody has given, mark the claim `{missing}` or leave
  it out, and ask the owner. A sentence you cannot trace to one of the three sources is deleted, not
  softened into a hedge.

1. **Read the code for every claim** — not the configuration, another document, or what a task said would
   be built.
2. **Say where nobody is sure.** Where behaviour is emergent, untested or could not be determined, say so
   plainly. **A confident sentence covering a gap is the worst thing a page can hold**, because the reader
   is using it *instead of* the code and cannot catch it.
3. **Never guess a number.** Without one, describe the behaviour.
4. **When the page and the thing disagree, the page is wrong.** Fix it. A page is never grounds for calling
   the implementation wrong; only the owner says what it ought to do.

## Coverage

**Code no page mentions is as wrong as a page the code contradicts.** A reader using the wiki instead of
the source never learns it exists, and nothing on any page warns them.

- **Inventory from the code, never from the wiki**, so the wiki cannot hide its own gaps. List everything
  a person can use, configure or notice: commands and options; endpoints, public functions, events;
  settings, their keys and environment variables; stored data and fields; refusals, error messages, exit
  and status codes, limits; jobs, workflows, builds, deployments; outside services; roles and permissions.
- **Every item has a home**: a page, or a section of one. An item only mentioned in passing, without its
  behaviour, is not covered.
- **Walk it the other way too.** A source file with public behaviour that no reference cites is usually an
  undocumented feature.
- **A new behaviour gets its page in the same change as its code.** Leave out only internals a reader never
  meets, such as private helpers and test code.

## Reading budget

A page must answer in about two minutes, and the goals page must read in one sitting. The gate enforces a
word count as the proxy, and prints every page's count on every build. References and code blocks are not
counted: one is followed and the other copied, so neither is read the way prose is.

The count is a backstop; **the intent is the control.** A page inside its budget that carries a sentence
serving nothing is still wrong, and a page over it is saying its intent has grown.

## Owner approval

- **Changing an intent needs the owner's approval**, quoted where the work is recorded, because it
  changes what the thing is for.
- **Changing detail below an intent does not.** A retuned number that alters no outcome is recorded, not
  approved.
- **If a change cannot be made without altering an intent, stop and ask.** It is a design decision, and it
  is not yours to make.

## Definition of done

1. The intent is two to four sentences saying what the thing is for, not how it works.
2. Every sentence serves the intent.
3. The prose holds no name only the code knows, no unit a reader cannot feel, and no task or gap list.
4. Every sentence states something read from the code and carries its own citation, or `{missing}`;
   anything uncertain says so.
5. Mechanism links out instead of being retold, and a subject of its own is a child page.
6. The infobox gives the thing's names, values and rules under noun labels, and every row cites a
   footnote the prose cites, or is marked missing.
7. `wiki check` passes.
8. Someone who has never read the source can follow the whole page.
9. Everything in the code a person can use, configure or notice has a page or a section.
10. Nothing on the page was invented: every statement traces to the code, the owner's words, or an
    outside service's own documentation.
