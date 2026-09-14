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
  { label = "Checks", value = "pointing words, vague actors, attribution, empty words", cite = "checks" },
  { label = "Refused openings", value = "this, that, these, those, our, here", note = "in a title or infobox name", cite = "names" },
  { label = "Pages checked", value = "every page, including one excused from citations", cite = "pages" },
  { label = "Code", value = "not checked", cite = "code" },
]
+++

The wording checks refuse a name or a sentence that points at the page, hides who acts, quotes the owner
instead of stating a rule, or uses a word that carries no fact.[^checks] Each names the field it found, or
the page and line of the sentence.[^checks] Every page is checked, including one excused from
citations.[^pages] Words inside code are left alone, because a sample shows text as written, and capital
letters make no difference.[^code] Headings are held to the pointing words on
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
hyphen.[^actors] The check reads the title, subtitle and
intent, every infobox group, label, value and note, and every sentence, but no heading.[^actors] Such a
word hides the one fact a reader needs, so a page names the reader, the owner, an agent or the part of the
system that acts.[^actors]

## Attribution

A page that tells a rule as a quote of the owner is refused, because the quote dates the page and argues
instead of describing.[^attribution] Where a requirement came from is recorded with the work that
implements it.[^attribution] Two kinds of wording are refused: `the owner` or `the owner's ruling`, with or
without a comma, followed by a date written as year, month and day, such as `the owner, 2026-09-14`; and
`the owner` followed by `said`, `says`, `asked`, `wrote` or `ruled`.[^attribution] The check reads the subtitle, intent and every sentence, but no title, heading or
infobox row.[^attribution]

## Empty words

A word that carries no fact is refused wherever the vague-actor check looks, and the problem says what to
write instead.[^empty] `may`, `just`, `some` and `new` have plain uses too, so the writer
judges them.[^empty]

| Kind | Words refused |
|---|---|
| Marketing | `powerful`, `seamless`, `robust`, `cutting-edge`, `best-in-class`[^empty] |
| Minimisers | `simply`, `easily`, `obviously`, `of course`, `clearly`[^empty] |
| Hedges | `appears to`, `seems to`, `typically`, `usually`, `generally`, `probably`, `likely`, `in some cases`, `tends to`[^empty] |
| Preamble | `note that` opening a clause or after `please` or `to`[^note], `it is worth noting`, `please be aware`, `in order to` |
| Open lists | `etc.`, `and so on`, `and/or`, `various`[^empty] |
| Time words | `currently`, `at the moment`, `for now`[^empty] |
| Empty amounts | `a number of`, `reasonable`[^empty] |
| Infobox values | a value that is only `yes`, `configurable`, `varies` or `depends`[^values] |

[^checks]: `src/builder/build.py` — `pointing_problems()`, `vague_actor_problems()`, `attribution_problems()`
    and `empty_word_problems()`, each called from `check()`, and each naming the field, or the page and line.
[^pages]: `src/builder/build.py` — none of the four skips a page whose front matter says `goals = false`.
[^code]: `src/builder/build.py` — `wording_places()` removes `INLINE_CODE` before a sentence or field is
    matched, `page_statements()` has already blanked fenced code, and every pattern ignores case.
[^empty]: `src/builder/build.py` — `empty_word_problems()` matches each pattern in `EMPTY_WORDS` against the
    places `wording_places()` gives the vague-actor check, and names what to write instead; the comment on
    `EMPTY_WORDS` gives the reason for the words left out.
[^values]: `src/builder/build.py` — `empty_word_problems()` refuses an infobox value that `EMPTY_VALUE`
    matches whole.
[^note]: `src/builder/build.py` — the preamble pattern in `EMPTY_WORDS` matches `note that` after
    `please`, `also`, `to`, `should` or `must`, or where no word and space come before it, so "each note
    that is archived" passes.
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
