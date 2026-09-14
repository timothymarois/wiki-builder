+++
title = "Citations"
subtitle = "every statement traced to its source"
status = "approved"
categories = ["Refusals"]
intent = """
Citations exist so that a reader who cannot read the code can still tell a checked sentence from a guess.
Every statement should lead to the code it came from, or to the documentation of the outside service it
describes, or say plainly that nothing was found.
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
  { label = "Unit checked", value = "sentence", cite = "uncited" },
  { label = "Infobox rows", value = "cited, or marked missing", cite = "rows" },
  { label = "Code samples", value = "not checked", cite = "sample" },
  { label = "Refused reference", value = "a link to a markdown document", cite = "document" },
  { label = "Outside documentation", value = "allowed, as a link", cite = "document" },
  { label = "Exempt pages", value = "pages about the wiki itself", cite = "exempt" },
]
+++

A **citation** is a numbered mark at a claim, with its reference listed at the foot of the page.[^render]
It is written as a markdown footnote.[^render] Two checks hold citations to account: one for a sentence
that cites nothing, and one for a reference that cites the wrong kind of thing.[^uncited]

## Silence

Every sentence must carry a citation, or the red mark that says there is none.[^uncited] If one does not,
the check names the page and the line, and quotes the sentence.[^uncited]

A citation after the full stop belongs to its sentence, and **a sentence never borrows its neighbour's
citation**.[^uncited] A version number or an abbreviation does not end a sentence.[^boundary] A sentence
written directly under its heading is checked like any other.[^heading]

A sentence that links to another page is excused, because that page carries the citations, and a table is
held as a whole.[^excused] A list item that is only a link, such as an entry under External links, states
nothing and is excused as well.[^excused] A code sample needs no citation, because it is the thing itself rather than a
claim about it; the sentence introducing it does.[^sample]

An infobox row is held to the same rule.[^rows] It names a footnote the page's text cites for the same
fact, and carries that citation's number, or it is marked as having no source; a row with neither is
refused, and so is one citing a footnote no sentence uses.[^rows]

Pages about the wiki itself, such as the front page, are excused.[^exempt]

## Red mark

Where nothing can be cited, the writer puts the word *missing* in curly braces, and it renders as a red
question mark in brackets where a citation would go.[^mark] **It is a fine answer; silence is
not.**[^uncited] It means either that the thing is not built or that nobody has found where it happens,
and to a reader both mean the same thing: do not take this on faith.[^mark] A reader-facing build removes
all of them.[^player]

Every build and check prints how many sources each page cites and how many claims it marks as having none,
with totals for the wiki, so how much of it is taken on faith is visible on every run.[^counts]
`wiki check` also lists every claim marked as having no source, with its page and line, without
failing.[^marks]

## Documents

A reference that links to a markdown document is refused.[^document] A page of prose is only another
claim, and it can be wrong in exactly the way the citing page is.[^document]

A reference to an outside service's own documentation, such as a host's guide, is a link that does not end
in `.md`, so it passes; it is how a page cites the behaviour of something outside the project.[^document]

Only a link is recognised: **a reference that names a document without linking to it passes**, and so does
a reference that names nothing at all.[^document]

[^render]: `src/builder/build.py` — `footnote_reference()`, `footnote_item()` and `footnote_block()`,
    registered in `make_markdown()`.
[^uncited]: `src/builder/build.py` — `uncited_problems()` reads each sentence from `page_statements()` and
    accepts one containing a footnote or `CLAIM` match; `citation_problems()` checks each reference.
[^boundary]: `src/builder/build.py` — `BOUNDARY` ends a sentence only at a full stop, question or
    exclamation mark followed by a space and a capital, a digit, code, emphasis or an opening bracket.
[^heading]: `src/builder/build.py` — `page_statements()` blanks every heading line with `HEADING_ANY`
    before reading the body.
[^excused]: `src/builder/build.py` — `uncited_problems()` skips a sentence matching `PAGE_LINK` or `LINK_ONLY`, and
    `statements()` returns a block that starts with `|` whole.
[^sample]: `src/builder/build.py` — `page_statements()` blanks fenced code with `FENCED`, so a sample is
    never read as sentences.
[^rows]: `src/builder/build.py` — `infobox_problems()`, and `render_infobox()`, which gives a cited row
    the number `footnote_reference()` recorded for its footnote.
[^exempt]: `src/builder/build.py` — `uncited_problems()` skips a page whose front matter says
    `goals = false`.
[^mark]: `src/builder/build.py` — `MISSING` and `MISSING_CITATION`, applied in `write_site()`.
[^player]: `src/builder/build.py` — `for_player()` removes every `INTERNAL_MARKER`.
[^counts]: `src/builder/build.py` — `citation_counts()`, printed by `report()`.
[^marks]: `src/builder/build.py` — `missing_marks()`, printed by `run()` in `src/builder/cli.py`.
[^document]: `src/builder/build.py` — `citation_problems()` matches `DOCUMENT_LINK`, a markdown link
    ending in `.md`, inside each footnote.
