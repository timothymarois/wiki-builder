+++
title = "Plain English"
subtitle = "British spellings, old and legal words, and one word that is not a word"
status = "approved"
categories = ["Refusals"]
intent = """
The plain-English check exists so that every page of one wiki reads in one English, in words a reader
would use themselves. A spelling from another English, or a word out of a contract, makes a reader stop
on the word instead of the fact — and a word no dictionary holds tells them no person read the page.
"""

[[infobox]]
group = "Rules"
rows = [
  { label = "Refusals", value = "British spellings, old and legal words, one non-word", cite = "check" },
  { label = "Message", value = "the word to write instead", cite = "check" },
  { label = "Scope", value = "fields and sentences, no headings", cite = "scope" },
  { label = "Exceptions", value = "words inside code", cite = "code" },
]
+++

A wiki is read by people who did not write it, so every page uses one English: American, and words a
person says out loud.[^check] Each refusal names the page, the line and **the word to write instead**, so a writer
fixes it without looking the spelling up.[^check] The other wording refusals are
described on [Wording](../wording.md).

## Refusals

### British spellings

A British spelling is refused with its American word: `behaviour` for `behavior`, `colour` for `color`,
`licence` for `license`, `labelled` for `labeled`, `centre` for `center`, `judgement` for `judgment`,
`grey` for `gray`, `towards` for `toward`, `analyse` for `analyze`, and every verb spelled `-ise` where
American English spells it `-ize`, in each of its `-s`, `-d`, `-ing` and `-ation` forms.[^british]

**Every word is listed by name, never matched by its ending.**[^british] A rule on `-ise` would take
`raise`, `precise`, `promise`, `otherwise`, `surprise`, `advise`, `revise` and `exercise` with it, and
each of those is correct English already in use on these pages.[^british]

### Old and legal words

A word from the old register, or from the register of contracts, is refused with the plain word that
replaces it: `whilst` for `while`, `amongst` for `among`, `shall` for `will` or `must`, `ought` for
`should`, `thus` and `hence` for `so`, `notwithstanding` for `even so`, `albeit` for `though`.[^old] A
word that points where a name belongs — `thereof`, `therein`, `wherein`, `aforementioned` — is refused
with the instruction to name the thing.[^old] `hereby` and `herein` carry ceremony and no fact, and are
deleted.[^old]

### A word that is not a word

`fellen` is refused by name: agents write it, and no dictionary holds it.[^word]

## Scope

The check reads the places the empty-word check reads: the title, the subtitle, the intent, every infobox
group, label, value and note, and every sentence.[^scope] Headings are left out.[^scope]

## Exceptions

A word inside code is left alone, so a name the software owns, such as `chartColours()`, is written the
way the software spells it.[^code]

[^check]: `src/builder/build.py` — `plain_english_problems()`, called from `check()`, names the field, or
    the page and line, and gives the word to write instead.
[^british]: `src/builder/build.py` — `BRITISH` maps each refused spelling to its American word, one entry
    per word; the comment above it gives the reason the list is not a pattern.
[^old]: `src/builder/build.py` — `OLD_ENGLISH` maps each refused word to what a writer puts in its place.
[^word]: `src/builder/build.py` — `NOT_A_WORD` holds `fellen`, and `plain_english_problems()` reports a
    word from it as not a word.
[^scope]: `src/builder/build.py` — `plain_english_problems()` reads the places `wording_places()` gives it,
    which are the title, subtitle and intent, every infobox group, label, value and note, and every
    sentence from `page_statements()`, which blanks headings.
[^code]: `src/builder/build.py` — `wording_places()` removes `INLINE_CODE` before a field or a sentence is
    matched, and `PLAIN_ENGLISH` ignores case.
