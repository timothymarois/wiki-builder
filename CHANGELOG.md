# Changelog

A release that adds a check is a **breaking** release: new rules find old pages, which is what they are
for. Every such entry says what it will fail, so the failure is expected rather than alarming.

## 0.1.0

First release. Extracted from the wiki it was written for, with everything that named that project
removed and a test that fails if any of it comes back.

**Builds** a static wiki from markdown with TOML front matter: one directory per page, addresses that
work served and off disk alike, a sidebar nested from the page paths, generated category pages, a
collected-goals page built from every page's intent, inlined search, pictures, a source view per page,
and a theme that follows the reader's.

**Refuses** a page that states something and cites nothing; a reference citing a document rather than
code; a heading that asks a question or rates its own contents; a page or a goals page over its budget;
a page edited since its date was recorded; a picture whose subject has changed; a page in no navigation
section; a category nobody belongs to; a page with no intent, or an intent over its budget.

**Carries** the skill that tells an agent how to write a page, written into the consuming project by
`wiki sync` and recorded against the release it came from.

**If you are adopting this into a project that already has pages**, expect `check` to fail on the first
run and to name everything at once. That is the tool doing its job.
