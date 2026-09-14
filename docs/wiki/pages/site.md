+++
title = "Site"
subtitle = "what a build makes"
status = "approved"
intent = """
The site exists so that pages can be read by a reader who will never open the markdown, wherever they
happen to open it. It should be impossible for the site to be out of date, and nothing a reader sees
should change unless a page did.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Commands", value = "wiki build, wiki publish, wiki user", cite = "build" },
  { label = "Output", value = "docs/wiki/site", note = "for wiki build", cite = "build" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Link ending", value = "index.html", note = "none in a published build", cite = "links" },
  { label = "Search results", value = "8 at most", cite = "search" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Search scope", value = "page titles only", cite = "search" },
  { label = "Date change", value = "the page's own text only", note = "any intent, for the goals page", cite = ["dates", "goalsdate"] },
  { label = "Link to a missing page", value = "drawn red, refused by the check", cite = "redlink" },
]
+++

`wiki build` turns the pages into a website in `docs/wiki/site`, beside them.[^build] **The site is never
committed.**[^serve] It is rebuilt each time `wiki serve` starts, and a page edited while the server runs
appears after `wiki build`.[^serve] What refuses a page is described on [Checks](checks.md), and how the site is served on
[Local server](serving.md).

## Addresses

Every page is a folder holding one file, `index.html`, and every link names that file.[^links] That way the
same site works both through a server and opened straight from disk.[^links] `wiki publish` builds it with
clean addresses instead, which work only on a host.[^publish] A link that leaves the wiki opens in a new tab,
is marked `nofollow` and ends in an arrow, without its author writing anything but the link.[^outside]

The build deletes whatever it no longer makes, so a removed page leaves nothing behind.[^removed] For the
same reason, **it refuses to write into a folder it did not make**, so it never empties a folder
made by anything else.[^guard]

**A link to a wiki page that does not exist is drawn red instead of blue**, and `wiki check` refuses it,
naming the page and the line.[^redlink] A link to any other file that does not exist is not refused, and
leads nowhere.[^deadlink]

## Dates

Each page ends with the day it last changed.[^dates] **That date moves only when the page's own text
does**: restyling or rebuilding the site leaves every date alone.[^dates] The goals page is the exception:
its date moves whenever any page's intent changes, including a draft's.[^goalsdate]

The record of dates is committed with the pages, because a date taken from the clock would say "today"
forever.[^dates] Every command that builds the site records dates, and `wiki check` never does.[^record]
Instead, `wiki check` refuses a page whose text has changed since its date was recorded, and a record of a
page that no longer exists, and says to run `wiki build`.[^stale]

A page's footer also says when the page was last audited against the code, or says never, and an edit
keeps that day.[^audited] Recording an audit is described on [wiki audit](commands/audit.md).

## Search

The search box matches **page titles only**, not what the pages say, and shows at most eight
results.[^search] Its index is written into every page rather than fetched, so search works from disk
too.[^index]

## Audiences

`wiki user` builds only the pages marked for users, which say `audience = "user"` in their front
matter; an infobox group can be marked the same way.[^user] The user build strips every reference,
every red mark and the Source tab.[^strip] Every field is listed on [Front matter](front-matter.md).

[^build]: `src/builder/cli.py` — `run()` builds into `site` beside the pages unless the command is
    `publish` or `user`.
[^serve]: `src/builder/cli.py` — `run()` builds once, then calls `serve()` in `src/builder/serve.py`,
    which never rebuilds; the project's `.gitignore` excludes `docs/wiki/site/`.
[^links]: `src/builder/build.py` — `page_directory()` and `relative_directory()`, which end every link in
    `LINK_SUFFIX`, `index.html`.
[^publish]: `src/builder/build.py` — `build()` empties `LINK_SUFFIX` when `links` is `"clean"`, which
    `src/builder/cli.py` passes for `publish`.
[^outside]: `src/builder/build.py` — `rewrite_references()` adds `OUTSIDE` to a link matching `OUTSIDE_LINK`;
    `src/builder/assets/wiki.css` draws the arrow on `a.ext`.
[^removed]: `src/builder/build.py` — the end of `write_site()` unlinks every file the build did not write.
[^guard]: `src/builder/cli.py` — `guard_output()` refuses a non-empty folder with no stylesheet from an
    earlier build.
[^redlink]: `src/builder/build.py` — `rewrite_references()` adds `NEW_PAGE` to a link to a page the wiki
    does not have, and `dead_link_problems()`, called from `check()`, names it with its line;
    `src/builder/assets/wiki.css` draws `a.new` in `--red`.
[^deadlink]: `src/builder/build.py` — `rewrite_references()` turns a link into a path from the page to the
    file it resolves to, without checking that anything is there.
[^dates]: `src/builder/build.py` — `write_site()` hashes each page's markdown and moves its date in
    `UPDATED.toml` only when the hash changes.
[^record]: `src/builder/cli.py` — `run()` calls `build()`, which records dates; `src/builder/build.py` —
    `check()` builds with `record=False`.
[^stale]: `src/builder/build.py` — `date_problems()`, called from `check()`.
[^audited]: `src/builder/build.py` — `render_page()` adds `Last audited` after `Last updated`, with `never`
    when there is none, and `write_site()` keeps a page's `audited` when its date moves.
[^goalsdate]: `src/builder/build.py` — `content_of()` in `write_site()` adds every page's intent to the
    goals page's hash.
[^search]: `src/builder/assets/wiki.js` — the search listener filters on `page.t`, the title, and keeps
    eight.
[^index]: `src/builder/build.py` — `index_for()` in `write_site()`; `src/builder/assets/template.html`
    inlines it as `WIKI_INDEX`.
[^user]: `src/builder/cli.py` — `run()` builds with audience `"user"`; `src/builder/build.py` —
    `read_pages()` reads a page's `audience`, defaulting to `"internal"`, and `render_infobox()` reads a
    group's own.
[^strip]: `src/builder/build.py` — `visible_to()` for pages, `for_user()` for references and marks, and
    `with_source` in `write_site()` for the tab.
