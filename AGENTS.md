# AGENTS

Rules for every agent in this repository. This is **wiki-builder**: a tool that renders markdown into a
wiki a person can read, and refuses the things that make documentation rot. `docs/BRIEF.md` says what it
is and why; `docs/CODEMAP.md` says where everything lives.

## What this repository is

A package other projects install. It knows nothing about any of them, and a test fails if that stops
being true. Every rule below follows from that one fact.

- **Nothing here may name a project.** Not a domain word, not a directory, not an example. `PackageTests`
  greps the code *and* the skill for this and will catch you.
- **A project's shape is not an assumption.** Where its wiki lives, how long its pages may be, what its
  pictures depict — all of it comes from `wiki.toml` or a parameter, never from a path this tool guessed.
- **The rendered site is generated output.** It is never committed, here or in a consuming project.

## Before starting

1. **Load the skills the work calls for, all of them, before anything else.**

   | The work | Load |
   |---|---|
   | Any Python | `using-python` |
   | Any change in behaviour | `testing-code` |
   | Something broken and the cause not yet proved | `debugging-code` |
   | The pages this tool renders, or the skill it ships | `writing-the-wiki` — the one in `src/skill/` |

2. Read this file, `docs/BRIEF.md`, and the task you were handed in full.
3. State the outcome and the observable proof. Check `git status` before editing.
4. Read each file before editing it. Search for existing behaviour before adding logic.
5. **Make the smallest change that does the job.** Touch nothing adjacent.

## A check, not a rule

This tool exists because rules in documents do not survive contact with the person writing the next page.
That applies here too.

- **A rule worth having is a check.** If prose must obey something, the tool refuses it and a test proves
  the refusal. Everything in `check` was added after the failure it prevents actually happened.
- **Watch it fail before you believe it.** Break the thing on purpose, see the gate go red, then restore.
  A check nobody has seen fail is a check that reports success.
- **A new check is a breaking release.** It will find pages that already exist — that is what it is for.
  Say in `CHANGELOG.md` what it will fail.
- **A message names what to do.** Not "invalid configuration": the file, what is wrong, and the command
  that fixes it.

## Python

- Standard library, plus `mistune`, pinned exactly. **A second dependency is an approval gate.**
- The house style is the one already here: a one-sentence docstring saying what, then why; no type hints;
  problems returned as full sentences a person can act on; `main(argv=None)` returning an int.
- Exit codes: **2** misuse, **1** something is wrong with the wiki, **0** fine.
- Determinism: sorted iteration everywhere, no wall-clock in output, no absolute paths. Two builds of one
  wiki are byte-identical, and a test says so.

## Tests

```sh
uv run --with mistune==3.3.4 python -m unittest discover -s tests -t tests
```

- Every case **breaks one rule and asserts the tool names it.** A test that only proves the code ran is
  not a test.
- Tests import the installed package. They prove what a project gets, not what the source tree holds.
- An empty result is a failure, never a pass: a check that found nothing did not run.

## Releases

- `pyproject.toml` and `src/builder/__init__.py` carry the version; they change together.
- Tag only when the owner says. **Never push without the owner's yes.**
- `CHANGELOG.md` is written in the same commit as the change, not afterwards.

## Approval gates

Get explicit owner approval before: adding a dependency; changing the Python floor; deleting files
outside the task's scope; tagging a release; pushing; editing `AGENTS.md` or `CLAUDE.md` (byte-identical,
changed in the same commit).

## Definition of done

1. The tests pass, and any new one was watched failing first.
2. Nothing in the code or the skill names any project.
3. `docs/CODEMAP.md` matches what is on disk; `CHANGELOG.md` records behaviour that changed.
4. The change was proved against a real wiki through the installed command, not only a fixture.
5. Re-read this file and verify every applicable item with observed evidence.
