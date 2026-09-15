+++
title = "Layout"
subtitle = "the sidebar, article, footer and narrow-screen layout"
status = "approved"
intent = """
The layout exists so that a reader can always see where they are and get somewhere else, whatever they
are reading. Moving through a long page should never cost them the sidebar, and a sample on the page
should be as easy to copy as it is to read.
"""

[[infobox]]
group = "Rules"
rows = [
  { label = "Sidebar", value = "scrolls on its own", note = "logo and search stay put", cite = "rail" },
  { label = "Code block", value = "copy button", cite = "copy" },
  { label = "Outside link", value = "new tab, nofollow, arrow", cite = "outside" },
  { label = "Narrow screen", value = "sidebar above the page", cite = "narrow" },
]
+++

A page has the sidebar on the left and the article beside it, and the two scroll separately.[^rail] How
a page's parts are named is described on [Pages](../pages.md).

## Sidebar

**The sidebar is exactly the window's height and never scrolls as a whole**: the logo and the search box
stay at its top, and only the list of pages beneath them scrolls.[^rail] Scrolling that list never moves
the article, and scrolling the article never moves the sidebar.[^rail] A page far down a long list opens
with its own link scrolled into view.[^current]

Pages beneath another hang from it as a tree.[^nest] **The sidebar marks where the reader is**: pages
above the current one are bold, and its tree lines take the link colour.[^branch] Lines across the
sidebar set off the logo, the search box and each section, whose name is in capitals, and the scroll bar
sits at the edge.[^section]

## Article

A page beneath another shows the pages above it, as links, over its title.[^crumbs]

Every code block has a Copy button in its top right corner.[^copy] A code block beside the infobox is
narrowed to fit beside it, so its button is never hidden underneath.[^beside] A table in a page is drawn
as a wiki table, and scrolls inside its own frame when it is wider than the screen.[^table] A list is
indented and spaced like the references at the foot of the page.[^lists] A link that leaves the wiki
opens in a new tab and ends in an arrow.[^outside] A flowchart or other diagram written in a `mermaid` code block is drawn as a
diagram, the way GitHub draws one, and the page's markdown keeps the block as written.[^diagram] The drawing needs no network,
and a page loads it only as a diagram nears the screen.[^diagram] How to write one is described on
[Diagrams](../pages/diagrams.md).

A picture written in the page's markdown is captioned with the title given after its address, or with its
alt text when it has no title.[^picture] Clicking a picture opens it whole, with its caption, and a click or
Escape closes it again.[^lightbox] The theme button beside the tabs steps through Auto, Light and Dark, and
the browser remembers the choice; Auto follows the system.[^theme]

## Footer

Every page ends with a footer the build writes: when the page last changed, when it was last audited or
never, how many words it has, about how long it takes to read, how many sources it cites, and how many of
its claims have no source.[^footer] A reader-facing build leaves out the audit date and the two citation
counts.[^footer] A page excused from citations, such as the goals page, leaves out the citation counts,
because it has nothing to count.[^footer] The reading time counts 250 words
a minute, the pace a 500-word page answering in about two minutes assumes.[^pace]

## Narrow screens

Below 900 pixels wide, the sidebar sits above the article, and its page list opens from a Menu
button.[^narrow]

[^rail]: `src/builder/assets/wiki.css` — `.rail-in` is sticky and the window's height; `.rail #nav` takes
    the space left under the logo and search, scrolls with `overflow-y: auto`, and keeps the scroll with
    `overscroll-behavior: contain`.
[^current]: `src/builder/assets/wiki.js` — scrolls `#nav` so its `a.on` link is in view, without moving
    the article.
[^crumbs]: `src/builder/build.py` — `render_crumbs()` links each page above the current one that the build
    has, in order, and `render_page()` fills it into `src/builder/assets/template.html` before the title.
[^nest]: `src/builder/assets/wiki.css` — `.rail li li::before` draws the line beside a nested page and
    stops it at the leg on `:last-child`, `.rail li li::after` draws the leg, and `.rail li li a` sets
    the link smaller.
[^branch]: `src/builder/build.py` — `render_nav()` gives the link of every page above the current one the
    class `up`, and the list beneath the current page or a page above it the class `here`;
    `src/builder/assets/wiki.css` makes `a.up` bold and draws the line and legs of `ul.here` in the link
    colour.
[^section]: `src/builder/assets/wiki.css` — `.logo::after` and `.sbox::after` draw the lines below the
    logo and the search box, and
    `.rail h5` draws each section's name in capitals under a
    line that reaches both edges of the rail, `.rail #nav > h5:first-child` leaves the line off the first,
    and `.rail #nav` reaches the rail's edges and carries its padding inside, so its scroll bar is on the
    edge.
[^copy]: `src/builder/build.py` — `write_site()` wraps every code block in `srcbox` with a Copy button;
    `src/builder/assets/wiki.js` copies the block when it is pressed.
[^beside]: `src/builder/assets/wiki.css` — `.srcbox` sets `display: flow-root`.
[^table]: `src/builder/build.py` — `write_site()` wraps every table in `wt` and gives it the class `w`;
    `src/builder/assets/wiki.css` draws both.
[^lists]: `src/builder/assets/wiki.css` — `.art :where(ul,ol)` and `.art :where(li)`.
[^diagram]: `src/builder/build.py` — `write_site()` turns a block matching `MERMAID_BLOCK` into
    `pre.mermaid`, names the `MERMAID` script for that page, and copies the script only when a page uses
    it; `src/builder/assets/wiki.js` — `loadMermaid()` fetches it as a diagram nears the screen, and
    `drawDiagrams()` draws every `pre.mermaid` in the page's theme.
[^footer]: `src/builder/build.py` — `write_site()` gives each page `page_stats()`, built from its word count
    and `citation_counts()`, and leaves the citation counts out for the `"user"` audience and for a page that says `goals = false`; `render_page()`
    writes them into the footer, after `Last updated` and `Last audited`, which `write_site()` passes as
    none to the `"user"` audience.
[^picture]: `src/builder/build.py` — `WikiRenderer.image()` captions a picture with its title, or its alt
    text when it has none.
[^lightbox]: `src/builder/assets/wiki.js` — the lightbox opens a clicked picture from the page or the
    infobox with its caption, sized to the window, and a click or Escape closes it.
[^theme]: `src/builder/assets/wiki.js` — the theme button steps through `auto`, `light` and `dark` and keeps
    the choice in the browser's storage; `src/builder/assets/template.html` applies it before the page is
    drawn.
[^pace]: `src/builder/build.py` — `reading_minutes()` divides by `READING_PACE`, 250, and rounds up to a
    whole minute, never fewer than one.
[^outside]: `src/builder/build.py` — `rewrite_references()` adds `OUTSIDE` to a link matching
    `OUTSIDE_LINK`; `src/builder/assets/wiki.css` draws the arrow on `a.ext`.
[^narrow]: `src/builder/assets/wiki.css` — the rules under `max-width: 900px`; `src/builder/assets/wiki.js`
    opens the list from `.navtoggle`.
