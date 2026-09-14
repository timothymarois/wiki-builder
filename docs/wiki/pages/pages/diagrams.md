+++
title = "Diagrams"
subtitle = "flowcharts and other drawings, written as text"
status = "approved"
intent = """
Diagrams exist so that a flow, a sequence or a decision can be drawn on a page, written as text the way
GitHub and markdown already allow. A diagram should be readable wherever the page is read, with or
without a network.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Syntax", value = "a mermaid code block", cite = "block" },
  { label = "Drawn by", value = "Mermaid 12.0.0", cite = "script" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Network", value = "none needed", cite = "script" },
  { label = "Citation", value = "on the sentence before it", cite = "rules" },
  { label = "Reading budget", value = "not counted", cite = "budget" },
]
+++

A **diagram** is a code block whose language is `mermaid`, and the site draws it as a picture instead of
showing its text.[^block] Mermaid is the diagram language GitHub draws from the same block, so one page
reads as a diagram on GitHub and on the wiki.[^github] How a page is written in general is described on
[Pages](../pages.md).

## Writing

A diagram is written between fences that name its language as `mermaid`.[^block]

````markdown
Every push checks the wiki before it is published.[^flow]

```mermaid
flowchart LR
  accTitle: Checking before publishing
  accDescr: A push checks the wiki; a problem stops it with nothing published, otherwise the site is published.
  pushed(["Push to main"]) --> check["Check the wiki"] --> passed{"Check passed?"}
  passed -- "No" --> stopped(["Nothing published"])
  passed -- "Yes" --> publish["Publish the site"] --> published(["Site published"])
```
````

Only a page with a mermaid block loads Mermaid, and its block is drawn in three steps.[^block][^script]

```mermaid
flowchart LR
  accTitle: How a diagram is drawn
  accDescr: When a page is built, a page without a mermaid block is shown without Mermaid. A page with one has the block marked as a diagram, loads Mermaid, and has the diagram drawn in its theme.
  built(["Page built"]) --> has{"Mermaid block<br/>on the page?"}
  has -- "No" --> plain(["Page shown without Mermaid"])
  has -- "Yes" --> mark["Mark it as a diagram"] --> load["Load Mermaid on the page"]
  load --> draw["Draw it in the page's theme"] --> shown(["Diagram shown"])
```

## Drawing

**A diagram needs no network**: Mermaid ships inside wiki-builder, and a build copies it, with its
licence, into a site only when some page has a diagram.[^script] Only a page with a diagram loads
it.[^script] A diagram is drawn in the page's theme, light or dark, and is drawn again whenever the theme changes,
whether the reader switches it or the system does.[^theme] It sits centred without a frame, and scrolls sideways
inside itself when it is wider than the page.[^style]

## Citations

A diagram states what something does, so the sentence introducing it carries the citation, and every box
and arrow must be something the cited code does.[^rules] The check does not read inside a code block, so a
diagram is never refused for citing nothing.[^cite] It costs nothing against the page's reading
budget.[^budget]

## Copies

A page's markdown copy keeps a diagram as the block it was written as, which is how an agent reads
it.[^copy] The copies are described on [Agent markdown](../site/agent-markdown.md), and wiki-builder's own
diagrams are on [Checks](../checks.md), [Citations](../checks/citations.md) and
[Deployment (GitHub)](../deployment-github.md).

[^block]: `src/builder/build.py` — `write_site()` turns a rendered block matching `MERMAID_BLOCK`, a
    `language-mermaid` code block, into `pre.mermaid`.
[^github]: GitHub Docs — [Creating diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams):
    GitHub draws a fenced code block marked `mermaid` as a diagram.
[^script]: `src/builder/build.py` — `MERMAID` and `MERMAID_LICENSE` sit in the package's assets;
    `write_site()` gives a page the script only when it has a diagram, and copies both into the site only
    when some page does.
[^theme]: `src/builder/assets/wiki.js` — `drawDiagrams()` keeps each diagram's text, sets Mermaid's theme
    to dark when the page's theme is dark or follows a dark system, and draws every `pre.mermaid`; the
    theme button and a change in the system's colour scheme call it again.
[^style]: `src/builder/assets/wiki.css` — `.art pre.mermaid`.
[^rules]: `src/skill/SKILL.md` — the Diagrams section.
[^cite]: `src/builder/build.py` — `page_statements()` blanks fenced code with `FENCED` before reading
    sentences.
[^budget]: `src/builder/build.py` — `read_pages()` counts words after `FENCED` removes code blocks.
[^copy]: `src/builder/build.py` — `markdown_copy()` passes fenced code through `outside_code()` unchanged.
