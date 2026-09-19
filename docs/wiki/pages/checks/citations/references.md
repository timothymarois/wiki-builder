+++
title = "References"
subtitle = "a reference that cites a document rather than the code or an outside service"
status = "approved"
categories = ["Refusals"]
intent = """
This check exists so that a reference leads to something that can settle the claim above it. A citation to
another document moves the question rather than answering it, and a reader following one should arrive at
the code, or at the documentation of the service being described.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Syntax", value = "markdown footnote", cite = "document" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Refusals", value = "a reference linking to .md, or to a PDF the wiki keeps", cite = ["document", "pdfcite"] },
  { label = "Scope", value = "every reference on every page", cite = "document" },
  { label = "Exceptions", value = "a document named without a link", cite = "document" },
  { label = "Enforcement", value = "listed with every other problem", cite = "order" },
  { label = "Clearing", value = "cite the code, or the service's own documentation", cite = "document" },
]
+++

A reference whose link contains `.md` anywhere, **or names a PDF inside the wiki**, is refused, because a
document is another claim that can be wrong in the same way.[^document][^pdfcite] What every sentence must
carry is described on [Citations](../citations.md).

## Refusals

Outside documentation passes when its address has no `.md`, so **a README on GitHub is refused like a
project document**.[^document]

## Scope

Every reference on every page is read, and the check names the page rather than the line.[^document]

## Exceptions

A reference naming a document without linking it passes, as does one naming nothing.[^document]

## Enforcement

Each problem is listed with every other problem `wiki check` finds.[^order]

## Clearing

A refused reference passes once it names the file and function that do the thing, or the outside service's
own documentation at an address that is not a markdown file.[^document]

[^document]: `src/builder/build.py` — `citation_problems()` matches `DOCUMENT_LINK`, a markdown link whose
    address contains `.md` anywhere, inside each footnote; its comment gives the reason.
[^pdfcite]: `src/builder/build.py` — `citation_problems()` also matches `PDF_DOCUMENT_LINK`, a markdown link to
    a `.pdf` address with no scheme and no leading `//`, inside each footnote.
[^order]: `src/builder/build.py` — `check()` adds `citation_problems()` to the problems it lists.
