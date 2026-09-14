+++
title = "wiki bless"
subtitle = "record that a picture is still true"
status = "approved"
intent = """
wiki bless exists so that a person who has looked at a picture whose subject changed can clear the check,
and leave a record of why. It should never clear a picture without a reason.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki bless" },
  { label = "Arguments", value = "PICTURE, REASON" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Reason", value = "required" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0" },
  { label = "Problems", value = "1" },
  { label = "Misuse", value = "2" },
]
+++

`wiki bless` records a picture's current fingerprint, and the reason it is still true, in the picture
record.[^bless] When a picture needs it is described on [Pictures](../checks/pictures.md).

## Usage

Both arguments are required.[^usage]
```sh
wiki bless [--root ROOT] [--wiki WIKI] PICTURE REASON
wiki bless page-anatomy.svg "only the placeholder's name changed"
```

## Arguments

| Argument | Meaning |
|---|---|
| `PICTURE` | the picture's file name, as its record names it[^usage] |
| `REASON` | why the picture is still true, which cannot be empty |

## Output

It prints the picture and the reason it recorded.[^bless]

## Exit codes

It exits with 0 once the blessing is recorded, 1 when the picture has no record or the reason is empty,
and 2 when an argument is missing or there is no wiki.[^exit]

[^bless]: `src/builder/build.py` — `bless()` writes `digest` and `blessed` through `write_ledger()`, and
    returns the line `run()` prints.
[^usage]: `src/builder/cli.py` — `main()` gives `bless` the positional `picture` and `reason`.
[^exit]: `src/builder/build.py` — `bless()` raises `WikiError` for an unrecorded picture or an empty
    reason; `src/builder/cli.py` — `main()` returns 1 for it, and argparse exits 2 on a missing argument.
