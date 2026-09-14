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
  { label = "Refused openings", value = "how, what, where, why, when, which, who, whether" },
  { label = "Refused words", value = "matter, important, interesting, note, overview, misc, detail" },
  { label = "Levels checked", value = "2 to 6" },
]
+++

A reader scans headings to find the one holding their answer, so a heading is a label on a drawer. The
check refuses the two kinds of heading that name nothing.[^check]

## Questions

A heading that opens with *how*, *what*, *where*, *why*, *when*, *which*, *who* or *whether* is
refused.[^question] Such a heading is the writer wondering what belongs in the section, when the reader
wanted the name of the answer: "Where it lives" should be **Home**. A word that merely starts the same
way, such as "However", passes.[^question]

## Verdicts

A heading that rates its own contents is refused: any heading containing *matter*, *important*,
*interesting*, *note*, *overview*, *misc* or *detail*, anywhere in it.[^verdict]

Words are matched whole, and only *matter* and *detail* are also matched in the plural. **"A note on
dates" is refused, but "Release notes" passes.**[^verdict]

## Scope

Every heading from the second level to the sixth is checked, but the page title is not.[^reach] A line inside a
code sample that looks like a heading is checked as one.[^reach]

[^check]: `src/builder/build.py` — `heading_problems()`.
[^question]: `src/builder/build.py` — `QUESTION_WORD`, matched at the
    start of the heading and ending on a word boundary.
[^verdict]: `src/builder/build.py` — `EDITORIAL`, which lists
    `matters?`, `note` and `details?` between word boundaries.
[^reach]: `src/builder/build.py` — `HEADING_LINE` matches two to six `#`
    at the start of any line of the body, fenced code included; the title is front matter.
