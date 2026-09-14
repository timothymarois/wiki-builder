+++
title = "Pictures"
subtitle = "showing a picture on a page, and opening it whole"
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
  { label = "Opening whole", value = "a click, closed by a click or Escape", cite = "lightbox" },
  { label = "Unrecorded picture", value = "the build stops", cite = "ledger" },
]
+++

A picture is a file in the wiki's `images` folder, shown on a page as a markdown image or at the top of the
infobox.[^ledger][^infobox] Every picture has a record in `PICTURES.toml`, and the build stops when a page
shows a picture that has none.[^ledger] What the record holds is described on
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
caption beneath.[^lightbox] A click or the Escape key closes it again.[^lightbox]

[^ledger]: `src/builder/build.py` — `rewrite_references()` points a picture at `images/` by its file name,
    and raises when that name has no entry in `LEDGER`, which is `PICTURES.toml`.
[^infobox]: `src/builder/build.py` — `render_infobox()` shows the front matter's `image` at the top of the
    infobox with `image_caption` under it, and raises when the picture has no entry in `LEDGER`.
[^caption]: `src/builder/build.py` — `WikiRenderer.image()` draws a figure captioned with the title, or with
    the alt text when there is no title.
[^figure]: `src/builder/build.py` — `write_site()` takes a lone figure out of its paragraph with
    `LONE_FIGURE`.
[^lightbox]: `src/builder/assets/wiki.js` — the lightbox opens a clicked `figure.fig img` or `.ib .pic img`
    with its caption, and a click anywhere or Escape closes it; `src/builder/assets/wiki.css` — `.lightbox img`
    holds the picture within 96% of the window's width and 88% of its height.
