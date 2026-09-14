+++
title = "Wording"
subtitle = "names and sentences that say nothing"
status = "approved"
categories = ["Refusals"]
intent = """
The wording checks exist so that every name and sentence on a page still says something to a reader who
arrived from a search or a link. A page should name the project, the thing and whoever acts, and state a
rule plainly rather than quoting who asked for it.
"""

[[infobox]]
group = "Rules"
rows = [
  { label = "Checks", value = "pointing words, vague actors, attribution", cite = "checks" },
  { label = "Refused openings", value = "this, that, these, those, our, here", note = "in a title or infobox name", cite = "names" },
  { label = "Pages checked", value = "every page, including one excused from citations", cite = "pages" },
  { label = "Code", value = "not checked", cite = "code" },
]
+++

The wording checks refuse a name or a sentence that says nothing to a reader who arrived from a search or a
link: one that points at the page instead of naming a thing, one that hides who acts, and one that quotes
the owner instead of stating a rule.[^checks] Each names the field it found, or the page and line of the
sentence.[^checks] Every page is checked, including one excused from citations.[^pages] Words inside code
are left alone, because a sample shows text as written.[^code] Headings are held to the pointing words on
[Headings](headings.md).

## Pointing words

A page title, infobox group or infobox label that opens with *this*, *that*, *these*, *those*, *our* or
*here* is refused, and the check asks for the thing itself.[^names] `This site` reads as nothing in a
contents box.[^names] A sentence, subtitle or intent is refused when *this*, *these* or *our* comes directly
before *repository*, *repositories*, *repo*, *project*, *site*, *website*, *wiki*, *tool*, *package* or
*codebase*, because to a reader who arrived from a search, `this repository` is no repository at
all.[^prose]

## Vague actors

A word that says an unnamed person acts is refused wherever it stands whole: `nobody`, `somebody`,
`someone`, `anyone`, `anybody`, `everyone`, `everybody`, and `no one` written with a space or a
hyphen.[^actors] Capital letters make no difference.[^actors] The check reads the title, subtitle and
intent, every infobox group, label, value and note, and every sentence, but no heading.[^actors] Such a
word hides the one fact a reader needs, so a page names the reader, the owner, an agent or the part of the
system that acts.[^actors]

## Attribution

A page that tells a rule as a quote of the owner is refused, because the quote dates the page and argues
instead of describing.[^attribution] Where a requirement came from is recorded with the work that
implements it.[^attribution] Two kinds of wording are refused: `the owner` or `the owner's ruling`, with or
without a comma, followed by a date written as year, month and day, such as `the owner, 2026-09-14`; and
`the owner` followed by `said`, `says`, `asked`, `wrote` or `ruled`.[^attribution] Capital letters make no
difference.[^attribution] The check reads the subtitle, intent and every sentence, but no title, heading or
infobox row.[^attribution]

[^checks]: `src/builder/build.py` — `pointing_problems()`, `vague_actor_problems()` and
    `attribution_problems()`, each called from `check()`, and each naming the field, or the page and line.
[^pages]: `src/builder/build.py` — none of `pointing_problems()`, `vague_actor_problems()` and
    `attribution_problems()` skips a page whose front matter says `goals = false`.
[^code]: `src/builder/build.py` — each of the three removes `INLINE_CODE` before matching, and
    `page_statements()` has already blanked fenced code.
[^names]: `src/builder/build.py` — `pointing_problems()` matches `DEMONSTRATIVE` against the title and
    every infobox group and label; the comment on `DEMONSTRATIVE` gives the reason.
[^prose]: `src/builder/build.py` — `pointing_problems()` matches `POINTING` against the subtitle, the
    intent and every sentence from `page_statements()`; the comment on `POINTING` gives the reason.
[^actors]: `src/builder/build.py` — `VAGUE_ACTOR` matches each word between word boundaries, ignoring case,
    and `no one` with a space or a hyphen; `vague_actor_problems()` reads `title`, `subtitle`, `intent`,
    each infobox `group`, `label`, `value` and `note`, and each sentence from `page_statements()`, which
    blanks headings; the comment on `VAGUE_ACTOR` gives the reason.
[^attribution]: `src/builder/build.py` — `attribution_problems()` matches `ATTRIBUTION`, ignoring case,
    against `subtitle`, `intent` and each sentence from `page_statements()`; its docstring and the comment
    on `ATTRIBUTION` give the reason.
