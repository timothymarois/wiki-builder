+++
title = "Report shapes"
subtitle = "the JSON document and the count per check that wiki check writes for another tool"
status = "draft"
intent = """
These shapes exist so that a tool reading a check does not begin by parsing sentences written for a
person, and so that a build log too short to hold every problem still shows what is wrong. Each should be
enough on its own to decide what to fix first.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Options", value = "--json, --summary", note = "one or the other", cite = "shape" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Output", value = "standard output, and nothing else under --json", cite = "json" },
  { label = "Exit codes", value = "unchanged by either", cite = "shape" },
]
+++

`wiki check` says everything as sentences for a person, which is what [wiki check](../check.md)
describes. **One of these two shapes may be given, never both**, and neither changes the exit
code.[^shape]

## JSON

`--json` writes the page count, a record per problem, and the marked claims in a list of their
own.[^json] A record names the file, the line where there is one, the check that refused it, and the
sentence **carried unchanged**, so a problem the fields do not fit still reads.[^record] A marked claim
never joins the problems, because it fails nothing.[^json] Nothing else is written, on either stream, and
two runs write the same bytes.[^json]

```json
{
  "marks": [],
  "pages": 3,
  "problems": [
    {
      "file": "thing.md",
      "line": 22,
      "message": "thing.md:22: “It says nothing.” states something and cites nothing; give it a reference, or {missing} if there is none",
      "rule": "uncited"
    }
  ]
}
```

Each `rule` names the check that refused it; a marked claim is named `missing`.[^rules]

## Count per check

`--summary` counts the problems by check, most first and by name where two tie.[^summary] **A wiki of a
few hundred pages prints more lines than a build log holds**, and a log that drops its oldest lines drops
the problems first.[^summary]

```text
wiki:    292  family
wiki:    207  pointing
wiki:    186  uncited
wiki: 346 pages, 685 problems
```

[^shape]: `src/builder/cli.py` — `main()` puts `--json` and `--summary` in a mutually exclusive group,
    and `run()` returns the same status under either.
[^json]: `src/builder/cli.py` — `run()` writes one `json.dumps()` with `sort_keys=True` on standard
    output and returns before the sentences, the counts and the marks are printed, putting
    `missing_marks()` under `marks` instead.
[^record]: `src/builder/build.py` — `problem_record()` reads the file and line from `PROBLEM_PLACE` at the
    head of the sentence, keeps the sentence whole as `message`, and leaves `file` and `line` empty where
    it finds none.
[^rules]: `src/builder/build.py` — `check()` names each producer as it adds it, and `page_checks()` gives
    the order they are reported in.
[^summary]: `src/builder/cli.py` — `run()` counts the records by `rule` and prints them sorted by falling
    count then by name, then the page and problem count.
