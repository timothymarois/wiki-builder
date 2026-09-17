+++
title = "Reading budgets"
subtitle = "word limits for a page, an intent and the goals page"
status = "approved"
categories = ["Refusals"]
intent = """
Reading budgets exist so that a page answers in about two minutes and every goal can be read in one
sitting. A page that outgrows its budget should be split rather than squeezed.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Setting", value = "[budget] in wiki.toml", cite = "config" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Page limit", value = "500 words", cite = "defaults" },
  { label = "Intent limit", value = "120 words", cite = "defaults" },
  { label = "Goals limit", value = "3,500 words", cite = "defaults" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Scope", value = "words outside references and code blocks", cite = "count" },
  { label = "Exceptions", value = "the goals page, held to the goals limit", cite = "goals" },
  { label = "Enforcement", value = "page overrun listed, intent overrun stopping the build", cite = ["over", "intent"] },
]
+++

A wiki has three limits, counted in words: one for a page, one for an intent, and one for the goals page
that collects every intent.[^defaults] A project can set its own under `[budget]` in `wiki.toml`, and
each must be a positive whole number.[^config]

## Scope

A page is counted from its markdown, **leaving out its references and code blocks**, so citing costs
nothing and a sample to copy, such as a prompt, costs nothing either.[^count]
A table counts only the words in its cells, not its borders.[^count]

## Exceptions

The goals page is not held to the page limit.[^goals] What it collects is measured against the goals limit
instead.[^goals]

## Enforcement

A page over its limit is listed by the check.[^over] **An intent over its limit stops the build** before
the other checks run.[^intent] Every build and every check prints each page's word count.[^report]

### Calibration

Until `[budget]` in `wiki.toml` sets `calibrated = true`, every build and check warns that the numbers are
a guess that happens to be enforced.[^calibrated] What a project's readers will read is unknown until it is
measured.[^calibrated]

[^defaults]: `src/builder/config.py` — `DEFAULT_BUDGET`.
[^config]: `src/builder/config.py` — `read_config()` merges
    `[budget]` over the defaults and refuses one that is not a positive integer.
[^count]: `src/builder/build.py` — `counted_words()` counts the words left after
    `strip_footnote_definitions()` and `FENCED` remove references and code blocks, and drops a table's
    `TABLE_SEPARATOR` lines and pipes.
[^goals]: `src/builder/build.py` — `budget_problems()` skips `GOALS_ID`
    for the page limit and compares `goals_words` with the goals limit.
[^over]: `src/builder/build.py` — `budget_problems()`.
[^intent]: `src/builder/build.py` — `read_pages()` raises `WikiError`.
[^report]: `src/builder/build.py` — `report()`, called by `run()` in
    `src/builder/cli.py`.
[^calibrated]: `src/builder/build.py` — `report()` prints the provisional warning while
    `budget.calibrated` is false, its default in `DEFAULT_BUDGET` in `src/builder/config.py`;
    `src/builder/cli.py` — `run()` calls `report()` for every command but `sync` and `bless`.
