+++
title = "Layout"
subtitle = "how a page sits on the screen"
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

## Article

Every code block has a Copy button in its top right corner.[^copy] A code block beside the infobox is
narrowed to fit beside it, so its button is never hidden underneath.[^beside] A table in a page is drawn
as a wiki table, and scrolls inside its own frame when it is wider than the screen.[^table] A list is
indented and spaced like the references at the foot of the page.[^lists] A link that leaves the wiki
opens in a new tab and ends in an arrow.[^outside] A flowchart or other diagram written in a `mermaid` code block is drawn as a
diagram, the way GitHub draws one, and the page's markdown keeps the block as written.{missing}

## Narrow screens

Below 900 pixels wide, the sidebar sits above the article, and its page list opens from a Menu
button.[^narrow]

[^rail]: `src/builder/assets/wiki.css` — `.rail-in` is sticky and the window's height; `.rail #nav` takes
    the space left under the logo and search, scrolls with `overflow-y: auto`, and keeps the scroll with
    `overscroll-behavior: contain`.
[^current]: `src/builder/assets/wiki.js` — scrolls `#nav` so its `a.on` link is in view, without moving
    the article.
[^copy]: `src/builder/build.py` — `write_site()` wraps every code block in `srcbox` with a Copy button;
    `src/builder/assets/wiki.js` copies the block when it is pressed.
[^beside]: `src/builder/assets/wiki.css` — `.srcbox` sets `display: flow-root`.
[^table]: `src/builder/build.py` — `write_site()` wraps every table in `wt` and gives it the class `w`;
    `src/builder/assets/wiki.css` draws both.
[^lists]: `src/builder/assets/wiki.css` — `.art :where(ul,ol)` and `.art :where(li)`.
[^outside]: `src/builder/build.py` — `rewrite_references()` adds `OUTSIDE` to a link matching
    `OUTSIDE_LINK`; `src/builder/assets/wiki.css` draws the arrow on `a.ext`.
[^narrow]: `src/builder/assets/wiki.css` — the rules under `max-width: 900px`; `src/builder/assets/wiki.js`
    opens the list from `.navtoggle`.
