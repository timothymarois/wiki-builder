---
name: writing-wiki-pages
description: Use when writing or changing any page of the wiki under docs/wiki/ — a page, an intent, an infobox, a citation, a picture, or the wording of anything a person reads there. It supplies how the wiki is built, the terms for its parts, the intent contract, what may and may not appear on a page, and the voice. Do not use for engineering documentation written for builders, which follows different rules.
---

# Write a wiki page

**Read [the standard](references/the-standard.md) before you write anything.** It holds the page the owner
approved, the same content written badly, why the difference matters line by line, and a self-edit pass.
Rules tell you what to avoid; only an example shows what good looks like. A page written from the rules below
without reading that one comes out **flat and true and unread** — which is the failure this whole skill
exists to prevent, and the one that does not announce itself.

**The wiki is for people, not for builders.** Its readers are the owner of the project, and later players
and product people. They do not read code and must never need to. Someone who has read the source should
learn nothing new from a page; someone who never has should understand the whole of it.

Every rule below serves one job: **the owner sees how the thing works without reading it.**

Nothing here is specific to any one game. The wiki and its generator are meant to be lifted into another
project whole, and these rules travel with them.

## How the wiki works

You are writing markdown. A generator turns it into a site; you never write HTML.

| Thing | Where | What it does |
|---|---|---|
| A page | `docs/wiki/pages/**.md` | TOML front matter between `+++` fences, then markdown |
| Its address | derived from its path | `pages/billing/invoices/refunds.md` is `/billing/invoices/refunds/` |
| Its place | derived from its path | it nests under the page at `pages/billing/invoices.md` in the sidebar |
| The sidebar | `docs/wiki/nav.toml` | names only the pages that **start** a branch; children nest by themselves |
| Pictures | `docs/wiki/images/` | plus `PICTURES.toml`, recording what each shows |
| The site | `docs/wiki/site/` | generated, ignored by git, rebuilt before it is served |
| When it changed | `docs/wiki/UPDATED.toml` | written by the build; a page's date moves only when its own content does |

```sh
./scripts/dev-wiki.sh          # build, serve, open a browser
./scripts/dev-wiki.sh --check  # what the gate runs
```

**To add a page**, put the file where it belongs in the tree. Only name it in `nav.toml` if it starts a
new branch. To add a page *under* an existing one, put it in a directory named after that page.

## The words for its parts

Use these, in commits, in review and in conversation. They are the names the generator uses.

- **Page** — one markdown file, one address.
- **Intent** — the two-to-four sentences of front matter saying what the system is *for*. The contract.
- **Lead** — the opening paragraph of the body, before any heading.
- **Infobox** — the panel at the top right. **Groups** of **rows**; a row is a **label** and a **value**.
- **Citation** — a numbered mark in the prose. **Reference** — its entry at the foot of the page.
- **Missing citation** — the red mark for a claim with nothing to cite. Written `{missing}`.
- **Category** — a cross-cutting label; the bar at the foot of a page. Not the sidebar.
- **The goals page** — every page's intent, collected. Generated, never written by hand.
- **Source view** — the Source tab, showing the page's own markdown.
- **Audience** — `internal` or `player`. Internal is the default and the only one built today.

## The intent is the contract

Every page opens with an `intent`: what this system is **for**, and what outcome it should produce. Not
how it works.

```toml
intent = """
Refunds exist so that a customer who was charged wrongly gets their money back without anyone having to
ask us twice. A refund that needs a support conversation has failed. It should be possible to issue one
in seconds and impossible to issue one by accident.
"""
```

Then the rule that governs everything else:

- **Every sentence must serve the intent.** One that does not is **cut** — not moved down the page, not
  shortened.
- **Nothing may outgrow its intent.** Something worth saying that the intent does not cover needs its own
  page with its own intent, which the owner approves — or it is engineering documentation and does not
  belong here.
- **A long page is a diagnosis, not a failure of discipline.** If every sentence honestly serves the
  intent and the page still runs long, **the intent is too broad**: split it, and let the new page nest
  under this one. Cutting good sentences to hit a number makes a worse page.

Write the intent first. It decides what the page contains, so writing it last means writing the page
twice.

## Naming things

Naming is most of what makes a page readable, and it is the thing that goes wrong first. Two settled
conventions agree, from either side of this problem:

- **Code**: a class is a **noun**, a function is a **verb**. A thing is named for what it is; an action
  is named for what it does.
- **An encyclopedia**: a title is a **noun phrase**, never a verb construction and never a question.

A wiki has no actions in it. Every name in one — a page, a heading, a category, an infobox label — names
a **thing a reader might want**. So every name is a noun phrase, and the failure is always the same: the
writer names their own question instead of its answer.

### Ask the question, then name the answer

This is the whole method. The question is how you find the section; the answer is what you call it.

| The question you were answering | Never call it | Call it |
|---|---|---|
| Where does it live? | "Where it goes", "Where they go" | **Home**, **Ground**, **Range** |
| Why is it like this? | "Why it is this way" | **Reasoning**, or the reason itself — **Thirst** |
| How does it spread? | "How a forest spreads" | **Spreading** |
| How long does it take? | "How long it takes" | **Pace**, **Growth**, **Lifespan** |
| What does it eat? | "What it eats" | **Diet**, **Food** |
| When does it happen? | "When it drinks" | **Water**, **Timing**, **The day** |
| What is it for? | "What they are for" | **Yield**, **Use**, **Purpose** |
| What makes it different? | "Two differences, and only two" | **Differences** |
| Is it any good? | "Fast enough to matter" | Name the subject — **Speed** |
| What does this file show? | "A worked page" | **The standard** |

A gerund is a noun and is fine: **Spreading**, **Hunting**, **Breeding**. A gerund *phrase* is usually
the question in disguise — "Growing up" wants to be **Growth**.

### Five tests for a name

From the encyclopedia's own title policy, and they work on headings and categories too. A name should be:

- **Recognisable** — a reader who knows the subject, without being expert in it, knows what this is.
- **Natural** — what they would say out loud, and what another page would link to it as.
- **Precise** — it identifies this subject and not a neighbouring one. "Limits" on a page about uploads
  is a size; on a page about the API it is a rate. Both are right, because the page gives the name its
  subject.
- **Concise** — no longer than it takes to identify the thing. Cut every word that is not doing that.
- **Consistent** — the same kind of thing is named the same way across pages. If one page calls it
  **Ground**, another does not call it "Terrain it accepts".

### Where this applies

- **A page title** is the thing the page is about. **Refunds.** **Sessions.** **The nightly run.**
- **A heading** is the same, one level down, and the gate refuses a question or a verdict.
- **A category** is a plural noun for a set: **Wild animals**, not "Animals that are wild".
- **An infobox label** is a noun, and the value completes it. Prefer **Expiry**, **Size limit**,
  **Retries**. A short verb form is allowed where the pair genuinely reads better as a phrase — "Runs
  every · four hours" — but a label that only works as a sentence is a label doing too much.

**When no good name exists, the section is wrong, not the name.** A heading you cannot name in two words
is usually two sections, or one section that has not decided what it is about.

## How a page is shaped

**Answer first, detail after.** This holds at every level: the lead answers the page, the first line of a
section answers the section, the first clause of a sentence answers the sentence. A reader who stops
early should still be right.

- **The lead stands alone.** Someone who reads only the first paragraph should come away with the true
  shape of the thing. Put the surprising fact there, not in a later section.
- **A heading is a label on a drawer. Name what is inside it — nothing else.** Water. Predators. Ground.
  Hunting. A reader scans headings to find the one holding their answer, and a label either tells them to
  stop or it does not.
  - **Never a question.** "Where they go" is the writer wondering what belongs in the section; the reader
    wanted "Ground". Anything opening How, What, Where, Why, When is this mistake. **The gate refuses it.**
  - **Never a verdict.** "Fast enough to matter", "Important notes", "Overview" rate the contents instead
    of naming them. **The gate refuses these too.**
  - One or two plain words is usually right. If no short label fits, the section is two sections.
- **Three to five sections.** More than that and the page is two pages.
- **Split rather than swell.** A subject that needs its own treatment becomes a child page and a link,
  not another heading. The sidebar nests it for you.

## How it reads

- **Say the consequence, not the mechanism.** "An expired session does not lose your draft" — not that
  one configuration value outlives another.
- **Short sentences. Ordinary words.** If a sentence needs reading twice, it is the sentence's fault.
- **Bold the thing that matters**, once or twice per section. If everything is bold, nothing is.
- **Give a number only when a person would notice it being wrong.** "About thirty seconds" beats a precise
  figure nobody can perceive.
- **Units a reader can feel** — seconds, metres, kilograms, days, plain counts. Convert from whatever the
  code uses; never make the reader do it.
- **Explain a surprising decision in one clause.** "Expiry is meant to make a stolen session useless, not
  to punish somebody who went to lunch." A reader who understands why will not report it as a bug.
- **Link sideways rather than repeating**, in the prose and near the top. A thing belongs on one page;
  every other page links to it and says so plainly: *"They live in storage, which is where eviction and
  replication are described — this page covers what a session is for and what it does."* Naming what a
  page is **not** about is how a reader stops looking for it here. Write a sibling page link as
  `name.md`, which the tool turns into a clean address.
- **Plain present tense, no hedging.** "A tree seeds about once every eight days", not "trees will
  generally tend to".

## Never on a page

These are not style preferences. A page carrying any of them has failed its readers.

| Never | Instead |
|---|---|
| A field, constant, function, file or class name | The behaviour it produces |
| Ticks, centimetres, internal ids, requirement numbers | Seconds, metres, kilograms, plain counts |
| A task, phase, branch or ticket | Nothing. The reader cannot act on it |
| A gap list, a to-do, "not built yet" as prose | The `{missing}` mark on the claim itself |
| An apology for what is missing | Nothing |
| A restatement of an engineering page | A link to it |
| Marketing, or persuading the reader | Description. A page that argues is in the wrong repository |

**Do not document absence in prose.** A reader who wants something and finds no mention of it has learned
what they needed. A section headed "not built yet" turns the wiki into a backlog, and backlogs are read by
nobody and rot fastest.

**A planned change may appear, clearly marked and never mixed into the description** — one short note, at
the end. A reader must never have to work out whether a sentence describes today or next month.

## Citing sources

Sources are cited the way an encyclopedia cites them: a numbered mark at the claim, the reference at the
foot. Write them as markdown footnotes and the generator does the numbering.

```markdown
A tree is full-grown six days after it takes root.[^growth]

[^expiry]: `src/session/expiry.py` — `sweep()` ends a session thirty minutes after its last request,
    and holds its draft for a day afterwards.
```

- **A reference names code, and only code.** Not a requirements page, not a concepts page, not another
  wiki page — the file and the function where the thing actually happens. The owner's ruling, 2026-09-14:
  *"sources must be code, where in the code is the source of this reference that satisfies the
  requirement"*. **The gate refuses a reference that cites a document.**
- **Why that rule and not a friendlier one.** A page of prose is not an answer to "where does this happen";
  it is another claim, written by someone else, that can be wrong in exactly the way your page is wrong.
  Citing it launders one document's error into two. Following a reference must land in the thing that runs.
- **Configuration counts as code** where a number lives there. Name the function that reads it *and* the row.
- **The references are the one place a path belongs**, and they are stripped from a player build.
- **Every non-obvious claim gets one.** If you cannot cite it, see below.
- **Links are written relative to your own file**, so they resolve while reading the markdown *and* in the
  browser. The gate checks every one of them.

## Everything is cited, or marked as uncited

**Every statement of fact, behaviour, rule or consequence carries a reference.** Not most of them, not the
surprising ones — every one. The owner, 2026-09-14: *"every statement, fact, requirement, logic, beahvior
mentions all require a citation or unknown citation."*

**The gate refuses a paragraph that states something and cites nothing.** A page about the wiki itself is
exempt, because it describes no behaviour; everything describing the game is not.

The reason is the whole point of the wiki. A reader is using this **instead of** reading the source, so a
sentence they cannot trace is a sentence they must take on faith — and it looks exactly like one that was
checked. Silence is the failure; **"no source" is a fine answer and silence is not.**

## When there is nothing to cite

Write `{missing}` after the claim, or `missing = true` on an infobox row. It renders as a red mark where
the citation would be.

It means **nothing was cited**, for either of two reasons: the game does not do this yet, or nobody has
found where it does. To a reader the consequence is the same — do not take this on faith — which is why one
mark serves both. It is never shown to a player.

It is also the only sanctioned way to say a thing is not built. Use it where a reader would otherwise
assume the thing exists, and sparingly: a page that is mostly red marks was written too early.

## The infobox

A handful of facts a person would actually check, in their language. Not every setting, arranged prettily.

- **Choose what a reader would verify by watching**, and say it as they would describe it.
- **Group rows** under a heading that names the question the group answers.
- A row may carry `guaranteed = "<requirement id>"`. That identifier is **traceability for whoever next
  checks the page against the code** and is never rendered.
- A `note` on a row is for the one clause that stops a figure being misread.

## Pictures

A page shows the thing it describes. Put pictures in `docs/wiki/images/`, reference them by a real
relative path, and give every one a caption — the caption is prose and obeys every rule above.

Each picture has an entry in `PICTURES.toml` saying what it depicts. **When a depicted asset changes and
the picture has not been re-made, the gate fails.** Clear it by re-rendering, or by
`dev-wiki.sh --bless <picture> "<why it is still true>"` when the change did not alter what the picture
shows. The reason is the record that someone looked.

## Writing a page truthfully

The page describes **what the thing actually does**, so:

1. **Read the code for every claim.** Not the configuration, not another document, not what a task said it
   would build — the code that runs.
2. **Say where nobody is sure.** Where behaviour is emergent, untested, or you could not determine it, say
   so in plain words. **A confident sentence covering a gap is the worst thing you can put here**, because
   the reader is using this *instead of* the code and has no way to catch it.
3. **Never guess a number.** If you cannot find it, describe the behaviour without one.
4. **A page and the thing disagreeing means the page is wrong.** It is stale; fix it. A page is never
   grounds for calling the implementation wrong — only the owner says what it ought to do.

## The reading budget

A page you consult must answer in about two minutes, and the goals page must be readable in one sitting.
The gate enforces a word count as the proxy and prints every page's count on every build.

The number is a backstop, not the control. **The control is the intent**: a page inside the budget that
carries a sentence serving nothing is still wrong, and a page over it is telling you its intent has grown.

## What needs the owner, and what does not

- **Changing an intent needs the owner's approval**, quoted where the work is recorded. It changes what
  the thing is trying to be.
- **Changing detail below an intent does not.** A retuned number that alters no outcome is logged, not
  approved.
- **If you cannot make your change without altering an intent, stop and ask.** You have found a design
  decision rather than an implementation detail, and it is not yours to make.

## A page is done when

1. The intent is two to four sentences and says what the system is for, not how it works.
2. Every sentence serves the intent; anything that did not is gone.
3. No field name, unit, identifier, file path, task or gap list appears in the prose.
4. Every claim was read from the code; anything uncertain says so; anything uncitable carries `{missing}`.
5. Mechanism links out rather than being retold, and a subject of its own is a child page.
6. `./scripts/dev-wiki.sh --check` passes.
7. Someone who has not read the source can follow the whole page.
