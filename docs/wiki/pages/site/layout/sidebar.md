+++
title = "Sidebar"
subtitle = "the page tree, the sections a reader shuts, and what the browser remembers"
status = "approved"
intent = """
The sidebar exists so that a reader can see where they are in the wiki and reach any other page from
wherever they are reading. A wiki with many pages should not cost a reader a walk past the parts they are
not using, and moving from one page to the next should not undo what they set up.
"""

[[infobox]]
group = "Rules"
rows = [
  { label = "Section header", value = "shuts and opens its pages", cite = "control" },
  { label = "Stored", value = "the sections a reader shut", cite = "stored" },
  { label = "Direct arrival", value = "opens the page's own section", cite = "arrival" },
  { label = "Page list", value = "scrolls on its own", note = "logo and search stay put", cite = "rail" },
]
+++

The sidebar holds the whole wiki, with the site's name and the search box above the page list.[^rail] **The
sidebar is exactly the window's height and never scrolls as a whole**: only the list beneath the search box
scrolls, and scrolling it never moves the article.[^rail] The rest of the layout is described on
[Layout](../layout.md).

## Page tree

Pages beneath another hang from it as a tree.[^nest] **The sidebar marks where the reader is**: pages above
the current one are bold, and its tree lines take the link color.[^branch] A page far down a long list opens
with its own link in view.[^current] Lines across the sidebar set off the logo, the search box and each
section, whose name is in capitals, and the scroll bar sits at the edge.[^section]

## Sections

**A section's name is a button across the full width of the sidebar**, with a mark at its right that turns
as the section shuts.[^control] Pressing it slides that section's pages up or down.[^slide] A shut section
is out of reach of the keyboard as well as out of sight, so tabbing through the sidebar walks past
it.[^slide] The button beside the search box shuts every section at once, and opens every section once all
of them are shut.[^all] No section may go without a name, and no two may share one, because the name is
what a section is remembered by.[^named]

## Storage

The sections a reader shut are stored in their browser under a key carrying the site's name, so two wikis
published at one address remember their own.[^stored] They are applied before the sidebar is drawn, so a reader never
sees a section opening or closing as a page arrives.[^stored] Where the page list was scrolled belongs to
the browser tab rather than the device, and the list opens where the reader left it.[^place]

**Following a link straight to a page opens the section that page sits in**, whatever was stored, and
stores nothing — so one shared link cannot undo what the reader chose.[^arrival] Reloading is not
arriving: a section just shut stays shut.[^arrival]

[^rail]: `src/builder/assets/wiki.css` — `.rail-in` is sticky and the window's height; `.rail #nav` takes
    the space left under the logo and search, scrolls with `overflow-y: auto`, and keeps the scroll with
    `overscroll-behavior: contain`.
[^nest]: `src/builder/assets/wiki.css` — `.rail li li::before` draws the line beside a nested page and
    stops it at the leg on `:last-child`, `.rail li li::after` draws the leg, and `.rail li li a` sets
    the link smaller.
[^branch]: `src/builder/build.py` — `render_nav()` gives the link of every page above the current one the
    class `up`, and the list beneath the current page or a page above it the class `here`;
    `src/builder/assets/wiki.css` makes `a.up` bold and draws the line and legs of `ul.here` in the link
    color.
[^current]: `src/builder/assets/wiki.js` — `placeList()` scrolls `#nav` so its `a.on` link is in view,
    without moving the article, and only when the restored place left it out of sight.
[^section]: `src/builder/assets/wiki.css` — `.logo::after` and `.sbox::after` draw the lines below the
    logo and the search box, `.rail h5` draws each section's name in capitals under a line that reaches
    both edges of the rail, `.rail #nav > h5:first-child` leaves the line off the first, and
    `.rail #nav` reaches the rail's edges and carries its padding inside, so its scroll bar is on the edge.
[^control]: `src/builder/build.py` — `render_nav()` writes each section as an `h5` carrying its key,
    holding a button and `CHEVRON`; `src/builder/assets/wiki.css` — `.rail h5 button` carries the header's
    padding and its bleed to the rail's edges, so the whole row takes a press, and `h5.shut .chev` turns
    the mark.
[^slide]: `src/builder/assets/wiki.css` — `.fold` goes from `grid-template-rows: 1fr` to `0fr`, and
    `h5.shut + .fold > ul` sets `visibility: hidden` after the slide, which takes its links out of the
    page; `src/builder/assets/wiki.js` — a click on a section's button toggles `shut` and sets
    `aria-expanded`.
[^all]: `src/builder/assets/template.html` — the `foldall` button stands beside the search box;
    `src/builder/assets/wiki.js` — its click shuts every section, or opens every one when all are shut,
    and `showFoldAll()` names which it will do next.
[^named]: `src/builder/config.py` — `read_config()` refuses a section with no title, and two sections that
    share one.
[^stored]: `src/builder/build.py` — `render_page()` fills `nav_key` with `wiki-nav-shut:` and the site's
    name slugged; `src/builder/assets/template.html` — the script in the head reads that key and writes a
    rule shutting each stored section before the sidebar is parsed; `src/builder/assets/wiki.js` —
    `rememberShut()` writes back the sections marked `shut`.
[^place]: `src/builder/assets/wiki.js` — `keepPlace()` writes `#nav.scrollTop` to the tab's own storage on
    `pagehide` and on `visibilitychange`, and `placeList()` reads it back; the `pageshow` listener restores
    nothing when the page came from the back/forward cache.
[^arrival]: `src/builder/build.py` — `current_section()` gives the key of the section holding the page
    being drawn; `src/builder/assets/template.html` — the head leaves that section out of the rule it
    writes when the tab has seen no page yet and the browser reports no reload, and records what it
    decided on the document for `src/builder/assets/wiki.js` to apply.
