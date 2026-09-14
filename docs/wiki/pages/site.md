+++
title = "Site"
subtitle = "what a build makes"
status = "approved"
intent = """
The site exists so that pages can be read by someone who will never open the markdown, wherever they
happen to open it. It should be impossible for the site to be out of date, and nothing a reader sees
should change unless a page did.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Commands", value = "wiki build, wiki publish, wiki player" },
  { label = "Output", value = "docs/wiki/site", note = "for wiki build" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Link ending", value = "index.html", note = "none in a published build" },
  { label = "Search results", value = "8 at most" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Search scope", value = "page titles only" },
  { label = "Date change", value = "the page's own text only", note = "any intent, for the goals page" },
  { label = "Dead links", value = "not refused" },
]
+++

`wiki build` turns the pages into a website in `docs/wiki/site`, beside them.[^build] **The site is never
committed.** It is rebuilt every time it is served, so what is served never falls behind the pages.[^serve]
What refuses a page is described on [Checks](checks.md), and reading the site with its sources on
[Local server](serving.md).

## Addresses

Every page is a folder holding one file, `index.html`, and every link names that file.[^links] That way the same site
works both through a server and opened straight from disk. `wiki publish` builds it with clean addresses
instead, which work only on a host.[^publish]

The build deletes whatever it no longer makes, so a removed page leaves nothing behind.[^removed] For the
same reason, **it refuses to write into a folder it did not make**, so it never empties someone else's.[^guard]

A link to a page or file that does not exist is not refused. It is written as it stands, and it leads
nowhere.[^deadlink]

## Dates

Each page ends with the day it last changed. **That date moves only when the page's own text does**:
restyling or rebuilding the site leaves every date alone.[^dates] The goals page is the exception: its date
moves whenever any page's intent changes, including a draft's.[^goalsdate]

The record of dates is committed with the pages, because a date taken from the clock would say "today"
forever.[^dates]

## Search

The search box matches **page titles only**, not what the pages say, and shows at most eight
results.[^search] Its index is written into every page rather than fetched, so search works from disk
too.[^index]

## Audiences

`wiki player` builds a second view for people outside the project.[^player] It holds only the pages marked
for players, and it strips every reference, every red mark and the Source tab.[^strip]

[^build]: `src/builder/cli.py` — `main()` builds into `site` beside the pages
    unless the command is `publish` or `player`.
[^serve]: `src/builder/cli.py` — `main()` builds before it serves; the
    project's `.gitignore` excludes `docs/wiki/site/`.
[^links]: `src/builder/build.py` — `page_directory()` and
    `relative_directory()`, which end every link in `LINK_SUFFIX`, `index.html`.
[^publish]: `src/builder/build.py` — `build()` empties `LINK_SUFFIX` when
    `links` is `"clean"`, which `src/builder/cli.py` passes for `publish`.
[^removed]: `src/builder/build.py` — the end of `write_site()` unlinks every
    file the build did not write.
[^guard]: `src/builder/cli.py` — `guard_output()` refuses a non-empty folder
    with no stylesheet from an earlier build.
[^deadlink]: `src/builder/build.py` — `rewrite_references()` turns a link
    into a relative path without checking that anything is there.
[^dates]: `src/builder/build.py` — `write_site()` hashes each page's
    markdown and moves its date in `UPDATED.toml` only when the hash changes.
[^goalsdate]: `src/builder/build.py` — `content_of()` in `write_site()`
    adds every page's intent to the goals page's hash.
[^search]: `src/builder/assets/wiki.js` — the search listener filters
    on `page.t`, the title, and keeps eight.
[^index]: `src/builder/build.py` — `index_for()` in `write_site()`;
    `src/builder/assets/template.html` inlines it as
    `WIKI_INDEX`.
[^player]: `src/builder/cli.py` — `main()` builds with audience `"player"`.
[^strip]: `src/builder/build.py` — `visible_to()` for pages, `for_player()`
    for references and marks, and `with_source` in `write_site()` for the tab.
