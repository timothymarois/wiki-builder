+++
title = "Reading budgets"
subtitle = "how long a page may be"
status = "approved"
categories = ["Refusals"]
intent = """
Reading budgets exist so that a page answers in about two minutes and every goal can be read in one
sitting. A page that outgrows its budget should be split rather than squeezed.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Settings", value = "[budget] in wiki.toml", cite = "config" },
]

[[infobox]]
group = "Defaults"
rows = [
  { label = "Page limit", value = "500 words", cite = "defaults" },
  { label = "Intent limit", value = "120 words", cite = "defaults" },
  { label = "Goals limit", value = "3,500 words", cite = "defaults" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Word count", value = "references and code blocks excluded", cite = "count" },
  { label = "Page overrun", value = "listed by the check", cite = "over" },
  { label = "Intent overrun", value = "build stopped", cite = "intent" },
]
+++

A wiki has three limits, counted in words: one for a page, one for an intent, and one for the goals page
that collects every intent.[^defaults] A project can set its own under `[budget]` in `wiki.toml`, and
each must be a positive whole number.[^config]

## Counting

A page is counted from its markdown, **leaving out its references and code blocks**, so citing costs
nothing and a sample to copy, such as a prompt, costs nothing either.[^count]
Words are split on spaces, so a table's borders and a link's address count as words too.[^count]

The goals page is not held to the page limit.[^goals] What it collects is measured against the goals limit
instead.[^goals]

## Enforcement

A page over its limit is listed by the check.[^over] **An intent over its limit stops the build** before
anything else is checked.[^intent] Every build and every check prints each page's word count.[^report]

## Calibration

Until the settings file marks the budgets as calibrated, every run warns that the numbers are a guess that
happens to be enforced.[^calibrated] Nobody knows what a project's readers will read until somebody
measures it.[^calibrated]

[^defaults]: `src/builder/config.py` — `DEFAULT_BUDGET`.
[^config]: `src/builder/config.py` — `read_config()` merges
    `[budget]` over the defaults and refuses one that is not a positive integer.
[^count]: `src/builder/build.py` — `read_pages()` counts the words left after
    `strip_footnote_definitions()` and `FENCED` remove references and code blocks.
[^goals]: `src/builder/build.py` — `budget_problems()` skips `GOALS_ID`
    for the page limit and compares `goals_words` with the goals limit.
[^over]: `src/builder/build.py` — `budget_problems()`.
[^intent]: `src/builder/build.py` — `read_pages()` raises `WikiError`.
[^report]: `src/builder/build.py` — `report()`, called by `main()` in
    `src/builder/cli.py`.
[^calibrated]: `src/builder/build.py` — `report()` prints the
    provisional warning while `budget.calibrated` is false, its default in
    `src/builder/config.py`.
