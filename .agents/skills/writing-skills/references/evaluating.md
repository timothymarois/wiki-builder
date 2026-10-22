# Evaluating

A skill that reads well and changes nothing is a cost with no return. The only way to know is to
run the work twice — once with the skill and once without — and read both results.

## Run the comparison

1. **Pick realistic tasks.** Two or three, the kind of request the skill exists for, with the mess
 a real request carries. A task built to show the skill working proves only that.
2. **Run each task twice**, in separate fresh sessions: one with the skill available, one with
 nothing. Same prompt, same inputs, no hints.
3. **Read the outputs, not the summaries.** An agent's account of its own work is generous and
 omits what it skipped. Open what it produced.
4. **Read the transcripts too.** They show whether the skill sent the agent somewhere useful or had
 it reading references it never needed — the difference between guidance and ballast.

## What the result tells you

**The skilled run is better.** Find which part did it. That part earns its place; the rest of the
skill is still unproven.

**The runs are indistinguishable.** Either the task did not need the skill, or the skill says what
the agent already does. Guidance that restates default behavior is the most common kind of dead
weight, because it reads as sensible in review. Cut it, and test a harder task.

**The skilled run is worse.** Usually over-specification: the skill forced a procedure that did not
fit, or spent the agent's attention on detail the task did not need. Look for rules stated without
their reason — those are the ones applied literally to cases they were never meant for.

## Generalize, do not fit

Iterating on the same two tasks until the skill handles them perfectly produces a skill that
handles those two tasks. The skill will be used on work nobody has thought of yet.

When a problem resists fixing, try a different framing rather than another constraint. Rules
accumulated one failure at a time end up contradicting each other, and an agent reading them
cannot tell which one governs the case in front of it.

## Record the result

Write down the tasks, what each arm produced, and what changed as a result. A comparison nobody
recorded gets rerun from scratch the next time the skill is questioned, and the reasoning behind
the current wording is lost.

Keep it short: what was compared, what differed, what changed in the skill. A result is worth
rereading only if it says why the skill looks the way it does.
