+++
title = "PDFs"
subtitle = "a PDF link that would be dead once published, and a PDF over 20 MB"
status = "draft"
categories = ["Refusals"]
intent = """
The PDF check exists so that a PDF a page links is still there once the site is published. A link that
works only while the project is served, or a PDF over the size limit, should be refused before the site is
published.
"""

[[infobox]]
group = "Rules"
rows = [
  { label = "Refusals", value = "a link outside files, a missing PDF, a PDF over 20 MB", cite = ["outside", "missing", "limit"] },
  { label = "Scope", value = "every PDF link the build writes, in any markdown form", cite = "scope" },
  { label = "Exceptions", value = "code, addresses outside the wiki", cite = "scope" },
  { label = "Enforcement", value = "listed by wiki check; a link out of the folder, or a linked folder, stops the build", cite = ["check", "symlink"] },
  { label = "Clearing", value = "the fix each refusal names", cite = "check" },
]
+++

`wiki check` refuses a link to a PDF that would lead nowhere once the site is published, and a PDF over the
size limit.[^check] Where PDFs are kept and how a page links one is described on
[PDFs](../pages/pdfs.md).

## Refusals

A build publishes a PDF only from the wiki's `files` folder, so every other place a link can lead is
refused.[^outside]

| Refused | Message |
|---|---|
| A link to a PDF outside the `files` folder, or in a folder inside it[^outside] | `wiki: refunds.md:12: links to ../policy.pdf, which is outside the wiki's files folder and would be dead once published; put policy.pdf in the files folder and link it as ../files/policy.pdf` |
| A link to a PDF the `files` folder does not hold[^missing] | `wiki: refunds.md:14: links to ../files/old-policy.pdf, which does not exist; put old-policy.pdf in the wiki's files folder, or correct the link` |
| A PDF over 20 MB[^limit] | `wiki: refunds.md:16: links to ../files/big.pdf, which is 20.1 MB, over the 20 MB a PDF may be; make it smaller, such as by compressing its pictures, or split it into parts` |

**The limit is 20 MB, counted as 20 × 1,048,576 bytes**, so a PDF of exactly 20 MB passes and one byte more
is refused.[^limit]

## Scope

**The check judges the links the build writes**, so it and the build never disagree about a link.[^scope]
Every link whose file name ends in `.pdf`, in any case, is checked, whether markdown writes it plainly, with a
title, in angle brackets, by reference or with a query after the name.[^scope] A link in a reference is
checked too, and the citation check also refuses a PDF there, as [Citations](citations.md) describes.[^scope]

## Exceptions

A link shown in code is not checked, and neither is a link to an address outside the wiki, such as a
vendor's own PDF.[^scope]

## Enforcement

`wiki check` lists every problem and exits with 1.[^check] **A PDF that is a symbolic link to a file
outside the `files` folder stops the build, and so does a `files` folder that is itself a symbolic link**, so
no build publishes a file from outside the wiki.[^symlink]

```text
wiki: refunds.md links to terms.pdf, which links to a file outside the files folder; put the PDF itself in the wiki's files folder
wiki: the wiki's files folder is a symbolic link, so a build would publish whatever it points at; make files a folder of its own inside the wiki, and put the PDFs in it
```

## Clearing

Each refusal names its fix: put the PDF in the `files` folder and link it there, add the missing PDF or
correct the link, or make the PDF smaller.[^check]

[^check]: `src/builder/build.py` — `pdf_problems()`, called from `check()`, names the page, the line, the
    link and the fix; `src/builder/cli.py` — `run()` returns 1 when there is a problem.
[^outside]: `src/builder/build.py` — `pdf_problems()` refuses a link for which `filed_name()` finds no plain
    file name directly in `FILES`.
[^missing]: `src/builder/build.py` — `pdf_problems()` refuses a name the `files` folder holds no file for.
[^limit]: `src/builder/build.py` — `pdf_problems()` refuses a file larger than `PDF_LIMIT`, 20 × `MEGABYTE`,
    and gives its size with `file_size()`.
[^scope]: `src/builder/build.py` — `rewrite_references()` records every link `is_pdf()` accepts, read back
    from the rendered page with `html.unescape()` and its query set aside, into the `pdf_links` list `check()`
    hands `build()`; `pdf_problems()` judges each one and finds its line with `link_line()`. Code is rendered
    as text, and an address outside the wiki matches `SETTLED_LINK` first.
[^symlink]: `src/builder/build.py` — `filed_pdf()`, called from `rewrite_references()`, raises `WikiError`
    when the file resolves outside the folder, and `write_site()` raises it when `FILES` is a symbolic link.
