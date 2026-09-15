+++
title = "Pictures"
subtitle = "pictures in the text and the infobox, captions and the lightbox"
status = "approved"
intent = """
Pictures exist so that a page can show the thing it describes, with a caption, and a reader can open any
picture whole without leaving the page. A picture should never go on showing something that has changed
without the check saying so.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Folder", value = "images", cite = "ledger" },
  { label = "Record", value = "PICTURES.toml", cite = "ledger" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Caption", value = "the title, else the alt text", cite = "caption" },
  { label = "Opening whole", value = "a click, closed by Close, Escape or the backdrop", cite = "lightbox" },
  { label = "Unrecorded picture", value = "the build stops", cite = "ledger" },
]
+++

A picture is a file in the wiki's `images` folder, shown on a page as a markdown image or at the top of the
infobox.[^ledger][^infobox] Every picture has a record in `PICTURES.toml`, and the build stops when a page
shows a picture that has none.[^ledger] A build copies only the pictures its pages show, so a picture on
an internal page stays out of a [user build](../commands/user.md).[^copied] What the record holds is described on
[PICTURES.toml](../pictures-toml.md), and how a changed picture is caught on
[Pictures](../checks/pictures.md).

## Text pictures

A picture in the text is a markdown image, and the site finds it in `images` by its file name, whatever
folder the link names.[^ledger] Its title, in quotes after the address, becomes its caption, or its alt
text when it has no title.[^caption] A picture alone in its paragraph is drawn as a figure of its own.[^figure]

```markdown
![The parts of a page](../images/page-anatomy.svg "The parts of a page")
```

## Infobox picture

A page's front matter names a picture for the top of its infobox with `image`, and its caption with
`image_caption`.[^infobox] Both fields are listed on [Front matter](../front-matter.md).

```toml
image = "page-anatomy.svg"
image_caption = "The parts of a page"
```

## Lightbox

Clicking a picture in the text or in the infobox opens it over the page, sized to the window, with its
caption beneath.[^lightbox] The Close button, the Escape key or a click on the dark backdrop closes it, and a
click on the picture itself does not.[^lightbox] **A PDF opens in the same lightbox**, as [PDFs](pdfs.md)
describes, and it behaves the same way for both.[^dialog] While it is open, the page behind cannot be used or scrolled, and Tab
moves only between the lightbox's own controls.[^dialog] Closing it puts focus back on the picture that
opened it.[^dialog]

[^ledger]: `src/builder/build.py` — `rewrite_references()` points a picture at `images/` by its file name,
    and raises when that name has no entry in `LEDGER`, which is `PICTURES.toml`.
[^copied]: `src/builder/build.py` — `write_site()` copies into `images/` only the pictures that
    `rewrite_references()` and a written page's `image` add to `shown`, after `for_user()` has removed the
    references from a user build.
[^infobox]: `src/builder/build.py` — `render_infobox()` shows the front matter's `image` at the top of the
    infobox with `image_caption` under it, and raises when the picture has no entry in `LEDGER`.
[^caption]: `src/builder/build.py` — `WikiRenderer.image()` draws a figure captioned with the title, or with
    the alt text when there is no title.
[^figure]: `src/builder/build.py` — `write_site()` takes a lone figure out of its paragraph with
    `LONE_FIGURE`.
[^lightbox]: `src/builder/assets/wiki.js` — a click on `figure.fig img` or `.ib .pic img` opens the lightbox
    with the picture and its caption, which closes from its Close button, from Escape, or from a click that
    lands on the dialog itself rather than the picture; `src/builder/assets/wiki.css` — `.lightbox img` holds
    the picture within 96% of the window's width and 88% of its height, and `.lightbox::backdrop` darkens the
    page.
[^dialog]: `src/builder/assets/wiki.js` — `show()` opens one native `dialog` with `showModal()` for a picture
    or a PDF and marks the page `lightbox-open`, which `src/builder/assets/wiki.css` stops scrolling; `stop()`
    keeps Tab inside the dialog, and its `close` listener in `lightbox()` puts focus back on the opener.
