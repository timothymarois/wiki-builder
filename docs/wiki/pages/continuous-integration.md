+++
title = "Continuous integration"
subtitle = "the check on every push, here and in any project"
status = "approved"
intent = """
Continuous integration exists so that a wiki cannot be merged while it is not fit to read: every push and
pull request runs the same check a person runs on their own machine. A project should get it by adding one
step, and the result should not depend on which machine ran it.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Action", value = "timothymarois/wiki-builder", cite = "action" },
  { label = "Inputs", value = "root, wiki, python-version", cite = "inputs" },
]

[[infobox]]
group = "Defaults"
rows = [
  { label = "Project", value = ".", cite = "inputs" },
  { label = "Wiki", value = "docs/wiki", cite = "inputs" },
  { label = "Python", value = "3.12", cite = "inputs" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Failure", value = "any problem wiki check reports", cite = "action" },
  { label = "Release checked", value = "the tag named in uses", cite = "install" },
]
+++

wiki-builder is also a GitHub Action that installs wiki-builder and runs `wiki check` on a project's
wiki, failing the job on any problem the check reports.[^action] What the check refuses is described on
[Checks](checks.md).

## Action

A project adds one step after checking out its code, naming a wiki-builder release tag.[^action]
```yaml
# .github/workflows/wiki.yml
name: wiki
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: timothymarois/wiki-builder@TAG
```

| Input | Meaning | Default |
|---|---|---|
| `root` | the project, relative to the checkout[^inputs] | `.` |
| `wiki` | where the wiki lives, relative to the project[^inputs] | `docs/wiki` |
| `python-version` | the Python that runs the check, 3.11 or newer[^inputs] | `3.12` |

The action installs the tool from its own copy, at the release named in `uses:`, so the check that runs is
the check that release ships.[^install] A wiki synced against a different release fails, and the check says
to run `wiki sync`.[^version]

## Repository workflows

Every push to `main` and every pull request runs two workflows in the wiki-builder repository, and a push
to `main` also runs a third that publishes the wiki.[^ci] One runs the tool's own tests on Python 3.11 and
3.12, against the installed package.[^tests] Another checks wiki-builder's own wiki with the same action a
project uses, so the action is exercised on every change to it.[^wiki] Publishing that wiki once
it passes is described on [GitHub Pages](deployment-github.md).

[^action]: `action.yml` — a composite action whose last step runs `wiki check` in the project's folder.
[^inputs]: `action.yml` — `inputs`: `root`, `wiki` and `python-version`, with their defaults; `wiki` is
    empty by default, which leaves the tool's own `docs/wiki`.
[^install]: `action.yml` — installs `github.action_path` with `pip`, after `actions/setup-python`.
[^version]: `src/builder/build.py` — `version_problems()`, called from `check()`.
[^ci]: `.github/workflows/tests.yml` and `.github/workflows/wiki.yml` — both run `on` a push to `main`
    and on a pull request; `.github/workflows/pages.yml` — runs `on` a push to `main`.
[^tests]: `.github/workflows/tests.yml` — the `python-version` matrix, then `pip install .` and the
    tests.
[^wiki]: `.github/workflows/wiki.yml` — a job whose only step after checkout uses `./`, this
    repository's `action.yml`.
