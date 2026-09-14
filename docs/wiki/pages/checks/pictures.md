+++
title = "Pictures"
subtitle = "a picture of something that still exists"
status = "approved"
categories = ["Refusals"]
intent = """
The picture check exists so that a page never shows something that has since changed. When a picture's
subject moves, someone should have to redraw it, or say why it is still true.
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
  { label = "Fingerprint", value = "bytes of every depicted file", cite = "digest" },
  { label = "Blessing", value = "reason required", cite = "bless" },
  { label = "New picture", value = "unguarded until blessed", cite = "unguarded" },
]
+++

Every picture has a record in `images/PICTURES.toml` naming the files or folders in the project that it
shows.[^ledger] The check fingerprints those files and fails when **they have changed since the picture
was made**.[^check] Nothing about the files is assumed, so any project can say what a picture shows
without adopting a convention for its own assets.[^digest]

## Records

A page showing a picture that has no record stops the build, and so does a record for a picture file that
is missing.[^missing] A record whose `depicts` names a path that is not in the project, or a folder holding
no files, stops the check.[^subject] A record naming a folder covers every file in it, so a change to any of those files
flags the picture.[^digest]

## Blessing

`wiki bless` takes a picture and a reason, and records the current fingerprint along with the
reason.[^bless] **A reason is required**, because it is the record that somebody looked.[^bless]

A picture whose record has no fingerprint yet is never checked.[^unguarded] **A new picture is unguarded
until it is blessed for the first time.**[^unguarded]

## Page anatomy

The picture of a page's parts shows the page template.[^here] If the template changes, the check on wiki-builder's
own wiki fails until the picture is redrawn or blessed.[^here]

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
[^here]: `docs/wiki/images/PICTURES.toml` — `page-anatomy.svg` depicts `src/builder/assets/template.html`,
    read by `picture_problems()`.
