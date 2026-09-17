+++
title = "Brief"
subtitle = "purpose, reasoning, users, scope and outside systems"
status = "approved"
goals = false
intent = """
The brief exists so that a reader arriving at wiki-builder, person or agent, learns in one screen what it
is, who it is for and what it refuses. It stays short and stable, and names nothing private.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Name", value = "wiki-builder" },
  { label = "Author", value = "Timothy Marois" },
  { label = "Website", value = "marois.dev", link = "https://marois.dev" },
  { label = "Source", value = "github.com/timothymarois/wiki-builder", link = "https://github.com/timothymarois/wiki-builder" },
]

[[infobox]]
group = "Requirements"
rows = [
  { label = "Python", value = "3.11 or newer" },
  { label = "Parser", value = "mistune, pinned exactly" },
  { label = "Runner", value = "uv or pip" },
]
+++

## Purpose

wiki-builder renders markdown into a wiki a person can read, and then refuses the things that make
documentation rot. A project installs it rather than copying it in, and it knows nothing about what it
documents.

It has two halves, and the second is why it exists:

- **A generator.** Pages with TOML front matter become a static site with a sidebar, infobox, contents,
  citations, search and pictures, that works served or from disk.
- **A set of refusals.** A sentence or an infobox row that states something and cites nothing. A reference
  linking to a markdown document. A heading that asks a question or rates itself. A name or sentence that
  points instead of naming. A page too long to read. A page edited since its date was recorded. A picture whose subject
  has changed. An unreachable page.

## Reasoning

Documentation dies the same way every time: it grows faster than it is read, readers cannot tell which
sentences were checked, and by the time it is wrong it still looks authoritative. The wiki wiki-builder was
extracted from had grown to 75,000 words that were no longer read.

wiki-builder is for the case where **the wiki is read instead of the source.** There, an untraceable
sentence is worse than a missing one, because it looks exactly like a verified one. So every sentence is
cited to the code it came from, or marked as uncited.

Every rule was added after the failure it prevents happened. On the day the check against
question headings was written, it found nine, all written by the agent that had written the rule against
them.

## Users

- **A person who owns a system but no longer writes its code**, and needs to see how it behaves without
  reading it.
- **An agent writing or revising those pages**, which is why the skill ships with the tool rather than
  being left to each project to invent.

## Scope

- **Covers:** rendering; the checks; the skill; a local server that shows the site and the project's
  files; a published build with clean addresses; a user build with everything internal removed;
  carrying rule changes into a project; a GitHub Action for a project's CI; guides to installing and
  deploying a wiki.
- **Refuses:** knowing one fact about the project it documents, which a test over the code and the skill
  enforces: no project name, no domain word, no assumption about its assets. Generating pages from the
  code they describe, since such a page agrees with the code whatever it does. Updating itself silently.
  Scaffolding, and every feature a second project has not yet asked for.

## External systems

- `uv` (`https://docs.astral.sh/uv/`) runs a pinned version without installing the tool: one install per
  machine, never per project.
- `mistune` is the markdown parser, pinned exactly so that a new version cannot turn every page red at
  once.
- Python 3.11 or newer, for `tomllib` in the standard library.
- GitHub Actions, for continuous integration.
