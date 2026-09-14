+++
title = "Agent markdown"
subtitle = "what an agent reads instead of the rendered page"
status = "approved"
intent = """
Agent markdown exists so that an agent reading the wiki gets each page as it was written, not as text
picked back out of HTML. An agent should find every page from one index, without a person pointing it there.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Page copy", value = "index.md", cite = "copy" },
  { label = "Index", value = "llms.txt", cite = "index" },
  { label = "Link", value = "in the Source view", cite = "tab" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "User build", value = "no copies, no index", cite = "user" },
]
+++

Every page is published a second time as markdown, beside its rendered page, for agents to read.[^copy]
What the rendered page holds is described on [Site](../site.md).

## Copies

A page's copy sits in the same folder as its rendered page, as `index.md`.[^copy] It holds the page's
title, subtitle, intent and whether it is a draft, then its body and references as written.[^copy] A link
in a copy to another page points at that page's copy, and a link shown inside code is left as
written.[^links] The goals page's copy carries every collected intent.[^goals] The local server answers a
copy as plain text.[^serve] **A page's Source view links to its markdown file**, which opens the copy as
the file itself, so a person or an agent can read the page as pure markdown.[^tab]

## Index

The root of the site holds `llms.txt`, listing every page's copy with its subtitle, in sidebar
order.[^index] It takes the shape the llms.txt proposal describes: a heading with the site's name, then
sections of links.[^proposal]

Every rendered page names its copy with `rel="alternate" type="text/markdown"`, and the index with
`rel="describedby"`.[^head] Those are the link relations the proposal recommends for finding both.[^proposal]

## Audiences

A user build carries no copies and no index, because a copy holds the references and red marks a user
build withholds.[^user]

[^copy]: `src/builder/build.py` — `write_site()` writes `markdown_copy()` as `AGENT_COPY`, `index.md`,
    beside each page's `index.html`.
[^links]: `src/builder/build.py` — `markdown_copy()` points a link to a page at `copy_address()`, and a
    picture at the site's `images` folder, through `outside_code()`, which leaves code alone.
[^goals]: `src/builder/build.py` — `goals_markdown()`, over the same `goals_order()` the rendered goals
    page uses.
[^serve]: `src/builder/serve.py` — `shown_as_text()` answers a file in `AS_TEXT`, which includes `.md`,
    as plain text.
[^tab]: `src/builder/build.py` — `render_source()`, given `AGENT_COPY` by `write_site()`, links the source
    view to the page's markdown copy; a user build has no source view.
[^index]: `src/builder/build.py` — `agent_index()`, written as `AGENT_INDEX` by `write_site()`.
[^head]: `src/builder/build.py` — `write_site()` passes both links to `render_page()`, which fills
    `llm_links` in `src/builder/assets/template.html`.
[^user]: `src/builder/build.py` — `write_site()` writes neither a copy nor the index for the
    `"user"` audience.
[^proposal]: llmstxt.org — [The /llms.txt file](https://llmstxt.org/): a markdown file at the site root
    with the site's name as a heading and sections of links to markdown versions of pages, found through
    `rel="alternate" type="text/markdown"` and `rel="describedby"`.
