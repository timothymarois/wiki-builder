+++
title = "Pointing words"
subtitle = "names and sentences that point instead of naming"
status = "approved"
categories = ["Refusals"]
intent = """
The pointing check exists so that every name and sentence on a page still means something to a reader who
arrived from a search or a link. A page should name the project and its parts, never point at the page it
sits on.
"""

[[infobox]]
group = "Rules"
rows = [
  { label = "Refused pointers", value = "this, that, these, those, our, here", note = "at the start of a name", cite = "names" },
  { label = "Refused phrases", value = "this, these or our before repository, project, site, wiki or tool", note = "and the words listed below", cite = "prose" },
  { label = "Code", value = "not checked", cite = "code" },
]
+++

The pointing check refuses a name or a sentence that points at the page or the project instead of naming
it.[^check] To a reader who arrived from a search, `this repository` is no repository at all, and
`This site` reads as nothing in a contents box.[^check] Headings are held to the same openings, as
described on [Headings](headings.md).

## Names

A page title, infobox group or infobox label that opens with *this*, *that*, *these*, *those*, *our* or
*here* is refused.[^names] The check names the title, group or label, and asks for the thing
itself.[^names]

## Prose

A sentence, subtitle or intent is refused when *this*, *these* or *our* comes directly before *repository*,
*repositories*, *repo*, *project*, *site*, *website*, *wiki*, *tool*, *package* or *codebase*.[^prose] The
check quotes the sentence with its page and line, and asks for the project's name.[^prose]

Words inside code are left alone, because a message the software prints is quoted as it is.[^code]

[^check]: `src/builder/build.py` — `pointing_problems()`, called from `check()`.
[^names]: `src/builder/build.py` — `pointing_problems()` matches `DEMONSTRATIVE` against the title and
    every infobox group and label.
[^prose]: `src/builder/build.py` — `pointing_problems()` matches `POINTING` against the subtitle, the
    intent and every sentence from `page_statements()`, and `quoted()` quotes the sentence.
[^code]: `src/builder/build.py` — `pointing_problems()` removes `INLINE_CODE` before matching, and
    `page_statements()` has already blanked fenced code.
