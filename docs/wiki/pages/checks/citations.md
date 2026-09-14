+++
title = "Citations"
subtitle = "every statement traced to the code"
status = "approved"
categories = ["Refusals"]
intent = """
Citations exist so that a reader who cannot read the code can still tell a checked sentence from a guess.
Every statement should lead to the code it came from, or say plainly that nothing was found.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Syntax", value = "markdown footnote", cite = "render" },
  { label = "Mark", value = "{missing}", note = "for no source", cite = "mark" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Unit checked", value = "paragraph", cite = "uncited" },
  { label = "Infobox rows", value = "cited, or marked missing", cite = "rows" },
  { label = "Code samples", value = "not checked", cite = "sample" },
  { label = "Refused reference", value = "a link to a markdown document", cite = "document" },
  { label = "Exempt pages", value = "pages about the wiki itself", cite = "exempt" },
]
+++

A **citation** is a numbered mark at a claim, with its reference listed at the foot of the page. It is
written as a markdown footnote.[^render] Two checks hold citations to account: one for prose that cites
nothing, and one for references that cite the wrong kind of thing.

## Silence

Every paragraph, list and table must carry a citation, or the red mark that says there is none.[^uncited]
If one does not, the check names the page and quotes the start of the paragraph.[^uncited]

The check works **by paragraph, not by sentence**: one citation anywhere in a paragraph covers all of
it.[^uncited] A paragraph written directly under its heading, with no blank line between them, is not
checked at all.[^heading] A code sample needs no citation, because it is the thing itself rather than a
claim about it; the sentence introducing it does.[^sample]

An infobox row is held to the same rule. It names a footnote the page's text cites for the same fact,
and carries that citation's number, or it is marked as having no source; a row with neither is refused,
and so is one citing a footnote no sentence uses.[^rows]

Pages about the wiki itself, such as the front page, are excused.[^exempt]

## Red mark

Where nothing can be cited, the writer puts the word *missing* in curly braces, and it renders as a red
question mark in brackets where a citation would go.[^mark] **It is a fine answer; silence is not.** It
means either that the thing is not built or that nobody has found where it happens, and to a reader both
mean the same thing: do not take this on faith. A reader-facing build removes all of them.[^player]

Every build and check prints how many sources each page cites and how many claims it marks as having
none, with totals for the wiki, so how much of it is taken on faith is visible on every run.[^counts]

## Documents

A reference that links to a markdown document is refused.[^document] A page of prose is only another
claim, and it can be wrong in exactly the way the citing page is.

Only a link is recognised: **a reference that names a document without linking to it passes**, and so does
a reference that names nothing at all.[^document]

[^render]: `src/builder/build.py` — `footnote_reference()`,
    `footnote_item()` and `footnote_block()`, registered in `make_markdown()`.
[^uncited]: `src/builder/build.py` — `uncited_problems()` splits the
    body on blank lines and accepts a block containing any footnote or `CLAIM` match.
[^heading]: `src/builder/build.py` — `uncited_problems()` skips any block
    that starts with `#`.
[^sample]: `src/builder/build.py` — `uncited_problems()` removes fenced code with `FENCED` before
    splitting the body.
[^rows]: `src/builder/build.py` — `infobox_problems()`, and `render_infobox()`, which gives a cited row
    the number `footnote_reference()` recorded for its footnote.
[^exempt]: `src/builder/build.py` — `uncited_problems()` skips a page
    whose front matter says `goals = false`.
[^mark]: `src/builder/build.py` — `MISSING` and `MISSING_CITATION`,
    applied in `write_site()`.
[^player]: `src/builder/build.py` — `for_player()` removes every
    `INTERNAL_MARKER`.
[^counts]: `src/builder/build.py` — `citation_counts()`, printed by `report()`.
[^document]: `src/builder/build.py` — `citation_problems()` matches
    `DOCUMENT_LINK`, a markdown link ending in `.md`, inside each footnote.
