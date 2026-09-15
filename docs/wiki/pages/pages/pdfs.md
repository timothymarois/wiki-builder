+++
title = "PDFs"
subtitle = "PDF files in the files folder, their links and sizes"
status = "draft"
intent = """
PDFs exist so that a page can hand a reader a document the project keeps, such as a policy, from the place
the page talks about it. A link to a PDF should work wherever the site is published, and a PDF is never a
citation.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Folder", value = "files", note = "beside images", cite = "link" },
  { label = "Link", value = "a markdown link, relative to the page", cite = "link" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Size limit", value = "20 MB", note = "20 × 1,048,576 bytes", cite = "limit" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Copied", value = "only the PDFs a page links", cite = "copied" },
  { label = "Citation", value = "refused", cite = "document" },
]
+++

A PDF is a file in the wiki's `files` folder, beside `images`, linked from a page with an ordinary markdown
link.[^link] A build copies into the site only the PDFs its pages link, so a PDF linked only from an internal
page stays out of a [user build](../commands/user.md).[^copied] **A PDF is not a citation**: a reference that
links one is refused, as [Citations](../checks/citations.md) describes.[^document] What refuses a PDF link is
described on [PDFs](../checks/pdfs.md).

## Links

A page links a PDF by its path from the page's own file, and the site points the link at its own copy of the
PDF.[^link] The PDF's size follows the link, such as `(PDF, 2.4 MB)`, rounded up, in whole kilobytes under a
megabyte and in megabytes to one decimal place above.[^size] A page's markdown copy points the same link at
the site's copy.[^copy]

```markdown
The rules are in the [Refund policy](../files/refund-policy.pdf).
```

## Publishing

**Only a PDF directly in the `files` folder is published.**[^link] A link to a PDF anywhere else, or in a
folder inside `files`, would lead nowhere once the site is on a host, so `wiki check` refuses it.[^refused]
A PDF larger than 20 MB is refused too.[^limit] A PDF that is a symbolic link to a file outside the folder
stops the build, so the file it points at is never published.[^symlink] A PDF no page links any more is
removed from the site by the next build.[^stale]

[^link]: `src/builder/build.py` — `rewrite_references()` points a link that `filed_pdf()` finds directly in
    `FILES`, `files`, at the site's copy, through `filed_name()`, which accepts only a plain file name whose
    folder resolves to the wiki's `files` folder.
[^copied]: `src/builder/build.py` — `write_site()` copies into `files` only the PDFs `rewrite_references()`
    and `markdown_copy()` add to `pdfs`, after `for_user()` has removed the references from a user build.
[^document]: `src/builder/build.py` — `citation_problems()` refuses a reference matching `PDF_DOCUMENT_LINK`.
[^size]: `src/builder/build.py` — `file_size()` rounds up to whole kilobytes, or to tenths of a megabyte, of
    1,024 bytes, and `write_site()` writes it after the link through `PDF_ANCHOR`.
[^copy]: `src/builder/build.py` — `markdown_copy()` points a PDF link `filed_pdf()` finds at the site's copy.
[^refused]: `src/builder/build.py` — `pdf_problems()`, called from `check()`.
[^limit]: `src/builder/build.py` — `pdf_problems()` refuses a PDF over `PDF_LIMIT`, 20 × `MEGABYTE`.
[^symlink]: `src/builder/build.py` — `filed_pdf()` raises `WikiError` when the file resolves outside the folder.
[^stale]: `src/builder/build.py` — `clear_stale()` deletes a file an earlier build wrote and this one did not.
