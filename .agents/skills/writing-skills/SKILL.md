---
name: writing-skills
description: Use when creating, editing, reviewing, splitting, or testing a skill, including writing or repairing a SKILL.md description that fires at the wrong time or never fires, deciding whether new guidance belongs in an existing skill or a new one, and moving detail into references or scripts. It supplies the authoring contract, the routing rules that decide whether a skill loads at all, and the comparison that proves it earns its context. Do not use it to carry out an existing skill's workflow, or to write one-off automation that belongs in the project it serves.
---

# Writing skills

A skill is instructions an agent loads when it recognizes the work. Two things decide whether it
earns its keep: whether it **fires at the right moment**, and whether the agent that loads it then
does **better work than it would have unaided**. Every rule below serves one of those two.

## Extend before you create

Read the skills that already exist before adding to them. Match the new capability against each
one's description, then read the bodies of the plausible matches.

Extend the existing owner when the new capability shares its trigger, its workflow and its
judgment — add a reference, a script or a section there. A second skill covering neighboring work
splits the routing decision in two, and an agent then loads one of them and misses the other half.

Create a new skill only when the work has a genuinely different trigger. Write down what that
difference is; a name that sounds adjacent is not a reason on its own.

**Never copy a skill under a new name to change part of it.** The copy and the original drift, and
because their names differ, nothing compares them again — the divergence becomes invisible rather
than reviewable. Work that needs different wording for one stack gets a **variant**: an overlay
carrying only the files that differ, so the shared rules stay shared.

## Choose the artifact

- A **skill** is the instruction boundary: when to act, what judgment to apply, which procedure to
 follow, and how to prove the result.
- A **reference** is detail the skill points at, read only when the work reaches it.
- A **script** is deterministic mechanism — work better done identically every time than described
 in prose for an agent to reinterpret.

One-off automation stays in the project it serves. Package a script in a skill only when future
work needs routing or judgment to reach it. Read
[Workflow scripts](references/workflow-scripts.md) before shipping one.

## Shape

```text
<name>/
├── SKILL.md required: routing and the core procedure
├── references/ optional: detail loaded only when needed
├── scripts/ optional: deterministic commands
├── assets/ optional: templates and output material
└── variants/ optional: overlays carrying only the files that differ
```

Create a directory only when it has content. No README, no changelog, no record of how the skill
came to be: an agent pays context for every line that is not guidance, and the history lives in
version control.

## Name the work

When the catalog has its own naming convention, such as one prefix per group of skills, follow it.
Otherwise name a skill `<verb>-<object>`: one verb from this table, then what it acts on — `using-haskell`,
`designing-onboarding`. The verb says what kind of work loads the skill, so an agent scanning names and a
person choosing a project's skills read the catalog the same way, and two skills for the same kind
of work cannot hide behind different verbs. Pick the verb whose meaning fits. Add a verb only when
none here fits the work, and add it to this table in the same change.

| Verb | The work it names |
|---|---|
| `using-` | working in one technology: a language, framework, engine, data store or tool |
| `designing-` | deciding what something should be, before or while it is built |
| `building-` | making a particular kind of product |
| `engineering-` | a technical concern that cuts across the code |
| `creating-` | producing assets: images, models, documents |
| `writing-` | producing text for people or for agents |
| `editing-` | improving text someone already wrote |
| `naming-` | choosing the terms a system uses |
| `researching-` | gathering outside evidence on a subject |
| `analyzing-` | interpreting data already gathered |
| `verifying-` | checking that supplied material can be trusted |
| `reviewing-` | judging finished work |
| `testing-` | proving behaviour with automated checks |
| `playtesting-` | learning from people playing a build |
| `debugging-` | finding the cause of a failure |
| `optimizing-` | improving a live result against a measure |
| `enforcing-` | applying rules that must hold every time |
| `generating-` | producing content from rules and seeds |
| `planning-` | sequencing work before it starts |
| `managing-` | coordinating work or a hosted workflow |
| `maintaining-` | keeping a record current while work goes on |
| `operating-` | acting on a live system through its integration |
| `reading-` | reading a live system without changing it |

## Write the description first

Frontmatter carries `name` and `description`, nothing else.

The description is the whole trigger. It is the only part in context before the skill fires, the
agent pays for it on every turn, and the body is unreachable until routing succeeds. Write it
first — it decides what the skill is, and a body written ahead of it gets written twice.

- Match `name` to the directory: lowercase letters, digits and single hyphens, starting with a verb
  from the table above.
- Route on **user intent**, including indirect requests that never name the skill. Start with
 `Use when`.
- State applicability, then what the skill supplies. Add `Do not use` only for a near-miss that
 would otherwise steal the trigger.
- Name a tool, format or file type only where it decides whether the skill should fire.
- Leave out steps, tests, benefits and implementation detail. None of it can help routing, and all
 of it is paid for every turn.

**Lean toward firing.** The common failure is a skill that never loads, not one that loads too
often: the agent works from habit, produces something plausible, and nothing reports that a skill
existed. When a trigger is genuinely borderline, name it. A skill that loads and proves unneeded
costs one read; a skill that stays silent costs the whole task.

```yaml
# Bad: implementation and verification, none of which can route.
description: Use when creating release notes. It reads Git history, writes Markdown, groups
 commits, checks links, runs validation, and produces internal and public versions.

# Good: intent, the judgment supplied, and the nearest boundary.
description: Use when preparing release notes from shipped repository changes. It supplies an
 audience-focused workflow grounded in verified history. Do not use for unreleased plans.
```

Read [Descriptions](references/descriptions.md) before writing or repairing one. It holds the
failure modes and how to test a trigger against realistic requests.

## Write for an agent that can already think

Use imperative steps in execution order. Assume the reader reasons well, edits code and uses
ordinary tools. Keep a sentence only when it changes what the agent does, prevents a failure it
would otherwise walk into, or points at detail worth loading.

**Explain why a rule exists.** An agent given the reason applies the rule to the case you did not
foresee; an agent given a bare imperative applies it literally and stops there. Writing ALWAYS or
NEVER in capitals is usually a sentence missing its reason — add the failure it prevents, and the
emphasis becomes unnecessary.

- Keep the core procedure, one strong default and the non-obvious traps in `SKILL.md`.
- Give exact commands for fragile operations; give judgment where several approaches work.
- Introduce every reference with when to read it. Keep one source of truth and link rather than
 restate — a fact written in two files drifts in one of them.
- Teach a trap as symptom, cause, replacement, and the proof it is fixed.
- Cut background, history, dated claims, and anything the agent's other rules already say.
- Name no machine path, repository or other skill. A skill is copied wherever the work happens,
 and those names point nowhere there; describe the work instead ("the stack's own guidance").

Keep `SKILL.md` under 500 lines. Past that, move conditional detail one level down into
`references/`, leaving a pointer that says when to read it.

## Budget the context

| Part | Paid | Keep there |
|---|---|---|
| `description` | every turn | the shortest complete trigger |
| `SKILL.md` | when the skill fires | core procedure, defaults, traps |
| `references/` | when read | conditional detail, long examples |
| `scripts/` | output only | deterministic work, bounded output |
| `assets/` | when used | templates and output material |

A skill covering several stacks organizes by stack — one reference per stack, named so the agent
reads only the one it needs — rather than one long page covering all of them.

## Prove it

A skill is not done when it reads well. It is done when it fires on the right work and improves the
result.

1. **Validate the shape.** The directory name, the frontmatter `name` that must match it, and a
 description long enough to route on.
2. **Test the trigger.** In separate fresh sessions, try a direct request, an indirect request that
 never names the skill, and a near-miss that should *not* load it. Fix routing by category, not
 by pasting the failing phrase into the description.
3. **Compare against no skill.** Run the same realistic task twice, once with the skill and once
 without, and read both results rather than a summary of them. Guidance that earns no visible
 improvement is spending context for nothing — cut it.
4. **Review the writing separately from correctness:** routing precision, execution order,
 duplication, reference discipline. A passing script proves nothing about the prose.

Read [Evaluating](references/evaluating.md) for how to run that comparison and record a result
worth rereading later.

## Keep it current

A skill that has sat untouched while its subject moved is worse than no skill, because an agent
trusts it. When work proves a rule wrong, fix the skill in the same change rather than working
around it, and say in your reply what you changed.
