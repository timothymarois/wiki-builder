# Workflow scripts

A script belongs in a skill when the work is deterministic, repeated, and better done identically
every time than described in prose for an agent to reinterpret. Prose describing an exact sequence
is a script that has not been written yet, and every agent that reads it reconstructs it slightly
differently.

## Make it earn its place

Ship a script when it replaces work an agent would otherwise redo each time: a transformation with
one correct answer, a validation with a fixed rule, an assembly step with an exact order.

Leave it out when the work needs judgment that changes with the situation. A script that encodes a
decision an agent should be making removes the reasoning without removing the responsibility.

A strong signal: if several runs of the same task each produce a near-identical helper, write that
helper once and point the skill at it.

## Define the contract

State, in the skill or beside the script, what it takes and what it returns:

- **Inputs** — arguments and their order, what each means, which are required.
- **Output** — what lands on standard output, and what lands on disk.
- **Exit codes** — zero for success, and what each failure code means.
- **Side effects** — every file or directory it creates, changes or removes.

An agent that knows the contract can use the script without reading it. An agent that does not will
read it, and pay for the whole file.

## Bound the output

Whatever a script prints enters the context of the agent that ran it. Print what the next decision
needs and nothing else: a count rather than the rows, the failures rather than every check, a path
rather than the file.

Give a long result a file and print its path. A script that prints a thousand lines costs more than
the work it saved.

## Fail honestly

Exit non-zero when the work did not happen. An agent reads a zero exit as success and moves on, so
a script that swallows its own failure produces a confident wrong result downstream — the most
expensive failure mode there is.

Say what failed and what would fix it. `no input file at <path>` ends the task; `error` starts an
investigation.

Never repair state the caller did not ask about, and never widen a script's authority to make a
failure go away.

## Test the contract

Test what the contract promises: each documented exit code, the empty input, the input that is
already correct, and the malformed input. Those are the cases an agent hits in practice and the
ones a demonstration run never covers.

Run the script directly, the way the skill tells an agent to run it. A test calling an internal
function proves the function works and leaves the entry point — the only part the agent uses —
unproven.
