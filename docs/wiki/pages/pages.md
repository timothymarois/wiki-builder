+++
title = "Pages"
subtitle = "page files, their intent and approval, and the parts of a page"
status = "approved"
intent = """
A page is how a writer who has read the code tells a reader who will not what it does. Writing one should
need nothing but markdown and a few lines of settings, and where the file sits should decide where the
page is found, so no list has to be kept in step with the files.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Location", value = "docs/wiki/pages", cite = "front" },
  { label = "Format", value = "markdown, with TOML front matter", cite = "front" },
]

[[infobox]]
group = "Defaults"
rows = [
  { label = "Status", value = "draft", note = "until the owner approves it", cite = "status" },
  { label = "Intent limit", value = "120 words", cite = "required" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Required fields", value = "title, intent", cite = "required" },
  { label = "Sidebar place", value = "the page's path", cite = "tree" },
  { label = "Reserved name", value = "source", cite = "source" },
]
+++

A **page** is one markdown file in `docs/wiki/pages`, with a few lines of TOML front matter at the
top.[^front] Every field the front matter can hold is listed on [Front matter](front-matter.md). Where the file sits is both its address and its place in the sidebar: a page in a folder
named after another page nests beneath that page without being listed anywhere.[^tree] What the build
makes of a page is described on [Site](site.md).

## Intent

Every page must have a title and say what it is for, in an **intent**, or the build stops.[^required] An
intent may run to 120 words by default, and a longer one also stops the build.[^required] A page that
still gives its subtitle as `kicker` stops the build too, with a message to rename it.[^kicker] Every
approved page's intent is collected onto the goals page in sidebar order, so the purpose of the whole
project can be read in one sitting.[^goals]

A page about the wiki itself, such as the front page, says `goals = false` to stay off the goals
page.[^exempt] The same setting excuses a page from citing anything, whatever it describes.[^exempt]

## Approval

**A page is a draft until its front matter says `status = "approved"`.**[^status] A draft is listed in the sidebar like any other
page, and opens with a banner saying that the owner has not approved it.[^draft] Search, the categories and the goals
page offer only approved pages.[^approved] What a part of the system is for is the owner's decision, and
an agent that drafts a page has not made it.[^status]

A page that no reader can reach from the sidebar stops the build, whether it is a draft or not.[^reach]

## Parts

![The parts of a page: the sidebar with search, the tabs, the title and its subtitle, the infobox, the
numbered contents, the body, the references, the categories and the footer.](../images/page-anatomy.svg)

The **infobox** holds a handful of facts a reader would check, in groups of rows.[^infobox] Every row cites
a footnote that a sentence on the page also cites, or is marked as having no source.[^rows] Its fields are
listed on [Infobox fields](front-matter/infobox.md).

A page gets a **numbered contents** box once it has more than two second- or third-level headings, and
the References heading at its foot counts as one.[^contents] A page's **categories**
appear at its foot once an approved page carries them, and each links to a generated page listing the
approved pages in that category.[^categories]
The **Source** tab shows the page's own markdown with a button that copies it, which is why no page file
may be named `source.md`, in any folder.[^source]

A flowchart or other **diagram** is written as a `mermaid` code block and drawn on the page, as described
on [Diagrams](pages/diagrams.md). The markdown a page is written in is described on
[Markdown syntax](pages/markdown.md), and pictures on [Pictures](pages/pictures.md).

[^front]: `src/builder/build.py` — `wiki_of()` puts the wiki in `docs/wiki`, whose `pages` `write_site()`
    reads; `read_front_matter()` reads TOML between two `+++` fences, and refuses a page whose fences are
    missing or unreadable.
[^tree]: `src/builder/build.py` — `read_pages()` keeps a page's path as its id; `children_of()` and
    `render_nav()` nest a page under the page whose path contains it.
[^required]: `src/builder/build.py` — `read_pages()` refuses a page with no title or intent, or an intent
    over `budget.intent`, which `src/builder/config.py` sets to 120 in `DEFAULT_BUDGET`.
[^goals]: `src/builder/build.py` — `goals_order()` walks the sections in order and keeps each approved
    page, and `goals_page()` collects their intents.
[^kicker]: `src/builder/build.py` — `read_pages()` refuses a page whose front matter has `kicker`.
[^exempt]: `src/builder/build.py` — `goals = false` is skipped by `goals_order()`, `uncited_problems()`
    and `infobox_problems()`.
[^status]: `src/builder/build.py` — `read_pages()` defaults `status` to `"draft"`, and
    `collect_categories()`, `goals_order()`, the search index and the draft banner each compare it with
    `"approved"`.
[^draft]: `src/builder/build.py` — `render_nav()` lists every page whatever its status; `render_page()` adds
    the draft banner.
[^approved]: `src/builder/build.py` — `collect_categories()`, `goals_order()` and the search index in
    `write_site()` take approved pages only.
[^reach]: `src/builder/build.py` — `write_site()` refuses any page that is in no section and beneath no
    page that is.
[^infobox]: `src/builder/build.py` — `render_infobox()` renders an infobox as groups of rows.
[^rows]: `src/builder/build.py` — `infobox_problems()` refuses a row with neither a `cite` nor
    `missing = true`, or one citing a footnote no sentence on the page cites, and `render_infobox()` shows
    the cited footnote's number.
[^contents]: `src/builder/build.py` — `number_headings()` numbers every `h2` and `h3` in the body, the
    References heading included, and `render_contents()` returns nothing for two or fewer.
[^categories]: `src/builder/build.py` — `collect_categories()` gathers categories from approved pages
    only; `render_categories()` shows at a page's foot only the categories gathered, and `write_site()`
    writes a page for each at its end.
[^source]: `src/builder/build.py` — `render_source()` and the source directory in `write_site()`;
    `read_pages()` refuses a page whose file is named `source.md`, in any folder.
