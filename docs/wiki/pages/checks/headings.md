+++
title = "Headings"
subtitle = "labels, not questions"
status = "approved"
categories = ["Refusals"]
intent = """
Headings exist so that a reader scanning a page finds the section holding their answer without reading the
others. Every heading should name what its section contains, never ask about it or rate it.
"""

[[infobox]]
group = "Rules"
rows = [
  { label = "Refused openings", value = "how, what, where, why, when, which, who, whether", cite = "question" },
  { label = "Refused words", value = "matter, important, interesting, note, overview, misc, detail", cite = "verdict" },
  { label = "Refused pointers", value = "this, that, these, those, our, here", cite = "pointer" },
  { label = "Levels checked", value = "2 to 6", cite = "reach" },
]
+++

A reader scans headings to find the one holding their answer, so a heading is a label on a
drawer.[^check] The check refuses the three kinds of heading that name nothing.[^check]

## Questions

A heading that opens with *how*, *what*, *where*, *why*, *when*, *which*, *who* or *whether* is
refused.[^question] Such a heading is the writer wondering what belongs in the section, when the reader
wanted the name of the answer: "Where it lives" should be **Home**.[^question] A word that merely starts
the same way, such as "However", passes.[^question]

## Verdicts

A heading that rates its own contents is refused: any heading containing *matter*, *important*,
*interesting*, *note*, *overview*, *misc* or *detail*, anywhere in it.[^verdict]

Words are matched whole, and only *matter* and *detail* are also matched in the plural.[^verdict] **"A note
on dates" is refused, but "Release notes" passes.**[^verdict]

## Pointers

A heading that opens with *this*, *that*, *these*, *those*, *our* or *here* is refused.[^pointer] It
points at the page it sits on instead of naming anything, so "Our setup" should be **Setup**.[^pointer] A
title or an infobox label that opens the same way is refused as well, as described on
[Wording](wording.md).

## Scope

Every heading from the second level to the sixth is checked.[^reach] The page title is held only to the
pointing words and vague actors, described on [Wording](wording.md). A line inside a code sample is not a heading,
and is not checked.[^reach]

[^check]: `src/builder/build.py` — `heading_problems()`.
[^question]: `src/builder/build.py` — `QUESTION_WORD`, matched at the start of the heading and ending on a
    word boundary.
[^verdict]: `src/builder/build.py` — `EDITORIAL`, which lists `matters?`, `note` and `details?` between
    word boundaries.
[^pointer]: `src/builder/build.py` — `DEMONSTRATIVE`, matched at the start of each heading by
    `heading_problems()`.
[^reach]: `src/builder/build.py` — `heading_problems()` removes fenced code with `FENCED`, then
    `HEADING_LINE` matches two to six `#` at the start of a line; the title is front matter.
