+++
title = "Pictures"
subtitle = "a picture refused once the files it depicts change"
status = "approved"
categories = ["Refusals"]
intent = """
The picture check exists so that a page never shows something that has since changed. When a picture's
subject moves, the picture should have to be redrawn, or given a reason why it is still true.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Record", value = "images/PICTURES.toml", cite = "ledger" },
  { label = "Command", value = "wiki bless", cite = "bless" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Scope", value = "bytes of every depicted file", cite = "digest" },
  { label = "Exceptions", value = "a new picture, unguarded until blessed", cite = "unguarded" },
  { label = "Enforcement", value = "build stopped for a picture with no record", cite = "missing" },
  { label = "Clearing", value = "wiki bless, with a reason", cite = "bless" },
]
+++

Every picture has a record in `images/PICTURES.toml` naming the files or folders in the project that it
shows.[^ledger] The check fingerprints those files and fails when **they have changed since the picture
was made**.[^check] Nothing about the files is assumed, so any project can say what a picture shows
without adopting a convention for its own assets.[^digest]

## Scope

A record naming a folder covers every file in it, so a change to any of those files flags the
picture.[^digest]

## Exceptions

A picture whose record has no fingerprint yet is never checked.[^unguarded] **A new picture is unguarded
until it is blessed for the first time.**[^unguarded]

## Enforcement

A page showing a picture that has no record stops the build, and so does a record for a picture file that
is missing.[^missing] A record whose `depicts` names a path that is not in the project, or a folder holding
no files, stops the check.[^subject]

## Clearing

`wiki bless` takes a picture and a reason, and records the current fingerprint along with the
reason.[^bless] **A reason is required**, because it is the record that the picture was looked at.[^bless]

[^ledger]: `src/builder/build.py` — `read_ledger()` reads `LEDGER` from the images folder.
[^check]: `src/builder/build.py` — `picture_problems()` compares each recorded `digest` with
    `subject_digest()`.
[^digest]: `src/builder/build.py` — `subject_digest()` hashes the bytes of every file under each `depicts`
    path.
[^missing]: `src/builder/build.py` — `rewrite_references()` and `render_infobox()` refuse an unrecorded
    picture; `write_site()` refuses a record with no file.
[^subject]: `src/builder/build.py` — `subject_digest()` raises `WikiError` for both, when
    `picture_problems()` or `bless()` reads the record.
[^bless]: `src/builder/build.py` — `bless()` refuses an empty reason and writes `digest` and `blessed`
    through `write_ledger()`.
[^unguarded]: `src/builder/build.py` — `picture_problems()` checks an entry only when it has a `digest`.
