+++
title = "wiki audit"
subtitle = "record that pages were checked against the code"
status = "approved"
intent = """
wiki audit exists so that a reader can see when a page was last checked against the code, and an owner can
see which pages have gone longest without a check. It should record only a check of the page as it stands,
and never move the day a page was updated.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki audit", cite = "usage" },
  { label = "Arguments", value = "PAGE, one or more", cite = "usage" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Record", value = "UPDATED.toml", cite = "record" },
  { label = "Edited page", value = "refused until built", cite = "exit" },
  { label = "Footer", value = "Last audited, or never", cite = "footer" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki audit` records today as the day each page it names was last checked against the code, beside the
page's date in `UPDATED.toml`.[^record] The page itself is not touched, so the day it was updated stays
where it is.[^record] Which pages a review audits is described on [Review prompt](../review-prompt.md).

## Usage

At least one page is named, by its path under `pages`, with or without `.md`.[^usage]
```sh
wiki audit [-h] [--root ROOT] [--wiki WIKI] PAGE [PAGE ...]
wiki audit refunds index.md
```

## Arguments

| Argument | Meaning |
|---|---|
| `PAGE` | a page's path under `pages`, such as `checks/budgets`, with or without `.md`; one or more[^usage] |

## Output

It prints one line for each page it recorded, with the day it ran.[^record]
```text
wiki: refunds audited 14 September 2026
wiki: index audited 14 September 2026
```

Each page's footer then says when it was last audited, after the day it was last updated, or says
never.[^footer] An edit keeps the audit date, and a user build leaves it out.[^footer] A page that says
`goals = false` cites nothing, so it is never audited and its footer carries no audit date.[^footer]

## Exit codes

Every page is checked before any is recorded, so a refused audit records nothing.[^exit]

| Code | Condition | Message |
|---|---|---|
| `0` | every page is recorded[^exit] | `wiki: refunds audited 14 September 2026` |
| `1` | a page does not exist[^exit] | `wiki: there is no page nope.md to audit; name a page by its path under pages, such as checks/budgets` |
| `1` | a page says `goals = false`[^exit] | `wiki: goals.md says goals = false, so it cites nothing and has nothing to audit; leave it out` |
| `1` | a page has changed since its date was recorded[^exit] | ``wiki: refunds.md has changed since its date was recorded; run `wiki build`, then audit it again`` |
| `2` | no page is named[^exit] | `wiki audit: error: the following arguments are required: PAGE` |
| `2` | an option it does not know[^exit] | `wiki: error: unrecognized arguments: --unknown` |
| `2` | there is no wiki where it was pointed[^nowiki] | `wiki: no wiki at nowhere` |

[^record]: `src/builder/build.py` — `audit()` writes `audited` for each page through `write_dates()`, and
    returns the line `run()` in `src/builder/cli.py` prints.
[^usage]: `src/builder/cli.py` — `main()` gives `audit` the positional `pages`, one or more, shown as
    `PAGE`; `src/builder/build.py` — `audit()` drops a trailing `.md`.
[^footer]: `src/builder/build.py` — `render_page()` adds `Last audited` after `Last updated`, with `never`
    when there is none; `write_site()` keeps `audited` when a page's date moves, and passes none to a user
    build or to a page whose front matter says `goals = false`.
[^exit]: `src/builder/build.py` — `audit()` checks that every page exists, does not say `goals = false`, and
    matches its recorded digest before `write_dates()`, raising `WikiError`; `src/builder/cli.py` — `main()` returns 1 for it, and
    argparse exits 2 when no page is named or an option it does not know is given.
[^nowiki]: `src/builder/cli.py` — `main()` prints `no wiki at` and the path, and returns 2, when the wiki
    folder does not exist.
