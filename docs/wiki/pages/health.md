+++
title = "Health"
subtitle = "every page's status, sources, claims with no source, and dates"
goals = false
status = "approved"
intent = """
The health page exists so that a reader sees which pages of the wiki to trust least, and which to check
against the code first, without running a command.
"""
+++

The health page lists every page of the wiki with its status, its words, the sources it cites, the claims it
marks as having no source, and the days it was last updated and last audited. Pages are listed A to Z by
title, and a count of claims with no source above 0 is shown in bold red. The
build writes the table from the pages and `UPDATED.toml` on any wiki that has a `health.md` page, so the
table is never written into `health.md` itself, and a user build leaves it out.
