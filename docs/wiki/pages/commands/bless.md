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
  { label = "Command", value = "wiki bless", cite = "usage" },
  { label = "Arguments", value = "PICTURE, REASON", cite = "usage" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Reason", value = "required", cite = "exit" },
  { label = "Record file", value = "rewritten whole", cite = "ledger" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", cite = "exit" },
]
+++

`wiki bless` records a picture's current fingerprint, and the reason it is still true, in the picture
record.[^bless] When a picture needs it is described on [Pictures](../checks/pictures.md), and every key
of the record on [PICTURES.toml](../pictures-toml.md).

## Usage

Both arguments are required, and a reason with spaces is quoted.[^usage]
```sh
wiki bless [-h] [--root ROOT] [--wiki WIKI] PICTURE REASON
wiki bless refund-flow.svg "the arrows still match the code"
```

## Arguments

| Argument | Meaning |
|---|---|
| `PICTURE` | the picture's file name, as its record names it[^usage] |
| `REASON` | why the picture is still true, which cannot be empty[^exit] |

## Output

It prints the picture and the reason it recorded.[^bless]
```text
wiki: refund-flow.svg blessed -- the arrows still match the code
```

**It rewrites the whole of `PICTURES.toml`**: every comment becomes the tool's own header, any key other
than `made`, `digest`, `depicts` and `blessed` is dropped, and an earlier reason is replaced.[^ledger]

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | the blessing is recorded[^exit] | `wiki: refund-flow.svg blessed -- the arrows still match the code` |
| `1` | the picture has no record[^exit] | `wiki: missing.png has no entry in PICTURES.toml` |
| `1` | the reason is empty[^exit] | `wiki: a blessing needs a reason; it is the record that the picture was looked at` |
| `1` | the record names a path that is not in the project[^exit] | `wiki: a picture says it shows src/gone.py, which is not in this project` |
| `2` | an argument is missing[^exit] | `wiki bless: error: the following arguments are required: REASON` |
| `2` | there is no wiki where it was pointed[^nowiki] | `wiki: no wiki at nowhere` |

[^bless]: `src/builder/build.py` — `bless()` writes `digest` and `blessed` through `write_ledger()`, and
    returns the line `run()` prints.
[^usage]: `src/builder/cli.py` — `main()` gives `bless` the positional `picture` and `reason`, each read
    as one argument.
[^ledger]: `src/builder/build.py` — `write_ledger()` writes its own header and, for each picture, only
    `made`, `digest`, `depicts` and `blessed`.
[^exit]: `src/builder/build.py` — `bless()` raises `WikiError` for an unrecorded picture or an empty
    reason, and `subject_digest()` for a missing path; `src/builder/cli.py` — `main()` returns 1 for it,
    and argparse exits 2 on a missing argument.
[^nowiki]: `src/builder/cli.py` — `main()` prints `no wiki at` and the path, and returns 2, when the wiki
    folder does not exist.
