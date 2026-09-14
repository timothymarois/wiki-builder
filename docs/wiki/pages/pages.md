+++
title = "Pages"
subtitle = "what a person writes"
status = "approved"
intent = """
A page is how someone who has read the code tells someone who will not what it does. Writing one should
need nothing but markdown and a few lines of settings, and where the file sits should decide where the
page is found, so nobody has to keep a list in step with the files.
"""

[[infobox]]
group = "Defaults"
rows = [
  { label = "Status", value = "draft", note = "until the owner approves it" },
  { label = "Readers", value = "internal" },
]

[[infobox]]
group = "Limits"
rows = [
  { label = "Intent", value = "120 words" },
  { label = "Page", value = "500 words", note = "references not counted" },
]
+++

A **page** is one markdown file with a few lines of settings at the top.[^front] Where the file sits is
both its address and its place in the sidebar: a page in a folder named after another page nests beneath
that page without being listed anywhere.[^tree] This page covers what a page holds and when it becomes
part of the wiki; what the build makes of it is on [Site](site.md).

## Intent

Every page must say what it is for, in an **intent**, or the build stops.[^required] An intent may run to
120 words, and a longer one also stops the build.[^required] Every intent is collected onto
[the goals page](goals.md) in sidebar order, so the purpose of the whole tool can be read in one
sitting.[^goals]

A page about the wiki itself, such as the front page, can opt out of the goals page. It is then also
excused from citing anything, because it describes no behaviour.[^exempt]

## Approval

**A page is a draft until it says it is approved.**[^status] A draft sits in the sidebar like any other
page, under a banner saying that nobody has agreed with it.[^draft] Search, the categories and the goals
page offer only approved pages.[^approved] What a part of the system is for is the owner's decision, and an
agent that drafts a page has not made it.

A page that nobody can reach from the sidebar stops the build, whether it is a draft or not.[^reach]

## Parts

![The parts of a page: the sidebar with search, the tabs, the title and its subtitle, the infobox, the
numbered contents, the body, the references, the categories and the date.](../images/page-anatomy.svg)

The **infobox** holds a handful of facts a reader would check, in groups of rows.[^infobox] A row can
record the requirement it satisfies, which is kept for whoever checks the page but never shown.[^infobox]

A page with more than two headings gets a **numbered contents** box.[^contents] A page's **categories**
appear at its foot, and each links to a generated page listing everything in that category.[^categories]
The **Source** tab shows the page's own markdown with a button that copies it, which is why no page may be
named "source".[^source]

[^front]: `src/builder/build.py` — `read_front_matter()` reads TOML between
    two `+++` fences, and refuses a page whose fences are missing or unreadable.
[^tree]: `src/builder/build.py` — `read_pages()` keeps a page's path as its
    id; `children_of()` and `render_nav()` nest a page under the page whose path contains it.
[^required]: `src/builder/build.py` — `read_pages()` refuses a page with no
    title or intent, or an intent over `budget.intent`, which
    `src/builder/config.py` sets to 120 in `DEFAULT_BUDGET`.
[^goals]: `src/builder/build.py` — `goals_page()` walks the sections in
    order and collects each approved page's intent.
[^exempt]: `src/builder/build.py` — `goals = false` is skipped by
    `goals_page()` and by `uncited_problems()`.
[^status]: `src/builder/build.py` — `read_pages()` defaults `status` to
    `"draft"`.
[^draft]: `src/builder/build.py` — `render_nav()` lists every page whatever
    its status; `render_page()` adds the draft banner.
[^approved]: `src/builder/build.py` — `collect_categories()`,
    `goals_page()` and the search index in `write_site()` take approved pages only.
[^reach]: `src/builder/build.py` — `write_site()` refuses any page that is
    in no section and beneath no page that is.
[^infobox]: `src/builder/build.py` — `render_infobox()` renders groups of
    rows and never renders a row's `guaranteed`.
[^contents]: `src/builder/build.py` — `render_contents()` returns nothing
    for two headings or fewer.
[^categories]: `src/builder/build.py` — `render_categories()` for the
    foot, and the category pages at the end of `write_site()`.
[^source]: `src/builder/build.py` — `render_source()` and the source
    directory in `write_site()`; `read_pages()` refuses a page named `source.md`.
