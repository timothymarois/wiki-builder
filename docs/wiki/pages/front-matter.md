+++
title = "Front matter"
subtitle = "the settings at the top of every page"
status = "approved"
intent = """
Front matter exists so that everything about a page that is not its text, such as its title, its purpose,
its approval and its infobox, sits in the page itself. A mistake in it should stop the build with a
sentence naming the page, never be read as nothing.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Format", value = "TOML between +++ lines", cite = "fences" },
  { label = "Required fields", value = "title, intent", cite = "fields" },
]

[[infobox]]
group = "Defaults"
rows = [
  { label = "Status", value = "draft", cite = "fields" },
  { label = "Audience", value = "internal", cite = "fields" },
]
+++

Front matter is TOML between two `+++` lines at the top of a page, before its markdown.[^fences] What a
page is for and how it is laid out is described on [Pages](pages.md), and the fields of an infobox on
[Infobox fields](front-matter/infobox.md).

## Fields

| Field | Type | Default | Meaning |
|---|---|---|---|
| `title` | string | required | the page's name, at its top and in the sidebar[^fields] |
| `intent` | string | required | what the thing is for, at most `budget.intent` words[^budget] |
| `subtitle` | string | empty | a line under the title[^shown] |
| `status` | string | `"draft"` | `"approved"` approves the page; any other value leaves it a draft[^status] |
| `goals` | true or false | true | `false` keeps the intent off the goals page and excuses the page from the checks that its sentences and infobox rows cite[^goals] |
| `audience` | string | `"internal"` | `"player"` puts the page in the build `wiki player` makes[^audience] |
| `categories` | list of strings | none | the categories named at the page's foot[^categories] |
| `hatnote` | string | empty | a note shown above the page's text[^shown] |
| `image` | string | none | a picture recorded in `PICTURES.toml`, shown at the top of the infobox[^image] |
| `image_caption` | string | empty | the caption under that picture[^image] |
| `infobox` | list of tables, written `[[infobox]]` | none | the infobox's groups, in the order written[^infobox] |

Any other field is ignored, except `kicker`, which is refused.[^fields]

## Validation

Every problem below stops the build, and names the page's file.[^validation]

| Condition | Message |
|---|---|
| the page does not open with `+++`[^validation] | `wiki: refunds.md does not open with a +++ front-matter fence` |
| the front matter never closes | `wiki: refunds.md never closes its +++ front-matter fence`[^fences] |
| the TOML cannot be read | `wiki: refunds.md has unreadable front matter:` and the parser's error[^fences] |
| `title` or `intent` is missing or empty | `wiki: refunds.md has no intent; every page must say what it is for`, naming `title` instead when that is the one missing[^refusals] |
| the intent is over its budget | `wiki: refunds.md's intent runs to 130 words, over the 120 an intent may use; say what the system is for, not how it works`[^refusals] |
| the page gives `kicker` | `wiki: refunds.md gives its subtitle as kicker, which is now called subtitle; rename kicker to subtitle`[^refusals] |
| `image` names a picture with no record | `wiki: refunds.md shows flow.svg, which has no entry in PICTURES.toml`[^image] |

## Example

The front matter of an approved page marked for players, with its fences:[^fences]

```toml
+++
title = "Refunds"
subtitle = "money back for a wrong charge"
status = "approved"
audience = "player"
categories = ["Payments"]
intent = """
Refunds exist so that a customer who was charged wrongly gets their money back without asking twice.
"""
+++
```

[^fences]: `src/builder/build.py` — `read_front_matter()` reads TOML between an opening `+++` line and the
    next, and raises the first three messages.
[^fields]: `src/builder/build.py` — `read_pages()` reads `title`, `intent`, `subtitle`, `hatnote`,
    `audience` with its default `"internal"`, `status` with its default `"draft"` and `categories`, and
    refuses `kicker`; `goals_order()`, `uncited_problems()` and `infobox_problems()` read `goals`;
    `render_infobox()` reads `image`, `image_caption` and `infobox`.
[^validation]: `src/builder/build.py` — `read_front_matter()`, `read_pages()` and `render_infobox()` raise
    `WikiError`, which `main()` in `src/builder/cli.py` prints.
[^budget]: `src/builder/config.py` — `read_config()` reads `budget.intent` from `wiki.toml`, 120 words when
    it is absent; `read_pages()` in `src/builder/build.py` refuses an intent longer than that.
[^shown]: `src/builder/build.py` — `read_pages()` leaves `subtitle` and `hatnote` empty when absent, and
    `render_page()` fills `template.html` with the subtitle under the title and the hatnote above the text.
[^status]: `src/builder/build.py` — `write_site()` renders a page as a draft when its `status` is anything
    but `"approved"`.
[^goals]: `src/builder/build.py` — `goals_order()` leaves out a page whose `goals` is false, and
    `uncited_problems()` and `infobox_problems()` skip it; each reads an absent `goals` as true.
[^audience]: `src/builder/build.py` — `write_site()` renders only the pages `visible_to()` its audience,
    which in a player build are those whose `audience` is `"player"`; `run()` in `src/builder/cli.py`
    builds for players on `wiki player`.
[^categories]: `src/builder/build.py` — `read_pages()` reads no categories when `categories` is absent, and
    `render_categories()` names them in the bar `template.html` puts after the page's text.
[^image]: `src/builder/build.py` — `render_infobox()` shows `image` at the top of the infobox with
    `image_caption`, empty when absent, under it, and raises the message for a picture with no entry in
    `PICTURES.toml`.
[^infobox]: `src/builder/build.py` — `render_infobox()` shows the `infobox` groups in the order written, and
    none when it is absent.
[^refusals]: `src/builder/build.py` — `read_pages()` raises the messages for a missing or empty `title` or
    `intent`, an intent over its budget, and `kicker`.
