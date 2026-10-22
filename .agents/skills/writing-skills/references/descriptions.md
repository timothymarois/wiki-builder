# Descriptions

The description decides whether a skill is ever used. It is the only part of a skill in context
before it fires, so an agent chooses from it alone, and a body written perfectly behind a
description that never matches is dead weight.

## The shape that routes

Two sentences, sometimes three:

1. **`Use when` + the work**, in the words a person would use for it — including the indirect ways
 they ask. A request rarely names the skill.
2. **`It supplies` + the judgment or workflow** the skill adds. This is what separates it from a
 neighbor with a similar trigger.
3. **`Do not use` + the nearest near-miss**, and only that one. A boundary against work nobody
 would confuse costs context and buys nothing.

## Failure modes

**Never fires.** The most common failure, and the quietest: the agent works from habit, the output
looks reasonable, and nothing reports that a skill existed. Usually the description lists
implementation rather than intent, or covers one phrasing of a request when people use five.

Fix by naming the intents, not the words. "Use when preparing release notes" catches "write up
what shipped", "draft the changelog" and "summarize this release"; a description mentioning
`CHANGELOG.md` catches only the request that names the file.

**Fires on everything.** A trigger written so broadly it matches any adjacent task. The agent loads
it, finds nothing that applies, and pays for the read. Narrow by naming the work it does *not*
cover, rather than by deleting triggers that are genuine.

**Two skills fight.** Two descriptions cover overlapping work and the agent picks whichever it
matched first. Decide which one owns the overlap, then give the other a `Do not use` naming it.
Overlapping triggers left unresolved make both skills unreliable rather than either one safe.

**Routes on a file type that is not the trigger.** Naming a format is right only when the format
decides whether the skill applies. A skill for spreadsheets should name spreadsheets; a skill for
release notes should not name Markdown, because Markdown is not why it applies.

## Length

Use the shortest description that routes correctly. The ceiling is around a thousand characters,
but it is a ceiling and not a target: every holder pays for every character on every turn, whether
or not the skill fires.

Cut anything that cannot change the routing decision — steps, tool names, benefit claims, output
formats, and any sentence explaining how the skill works rather than when it applies.

## Testing a trigger

Write realistic requests, not abstract ones. A real request carries detail: a file path, a
deadline, a complaint, a half-formed idea. `"Format this data"` tests nothing; `"the export my
manager wants has the columns in the wrong order and three of the dates are text"` tests whether
the description matches how people actually write.

Cover three kinds:

- **Direct** — the request names the work plainly. It should fire.
- **Indirect** — the request describes the problem without naming the work. It should still fire,
 and this is where most descriptions fail.
- **Near-miss** — the request shares vocabulary but needs something else. It should not fire.
 Make these genuinely hard; an obviously unrelated request proves nothing.

Run each in a fresh session, because a skill already loaded in the current one cannot be tested for
whether it loads. When one fails, change the category the description covers rather than pasting
the failing sentence into it — a description patched with specific phrasings fits those phrasings
and nothing else.

## Simple work may not route at all

An agent reaches for a skill on work it cannot already do well. A one-step request often will not
fire a skill however well the description matches, because the agent simply does the thing. This is
correct behavior, not a routing bug: test triggers with work substantial enough that guidance would
genuinely help.
