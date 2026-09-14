# Brief — wiki-builder

*What this is and why it exists. One screen, stable, and free of private detail.*

## What it is

A tool that renders markdown into a wiki a person can read, and then refuses the things that make
documentation rot. It is installed by a project, not copied into one, and it knows nothing about whatever
it documents.

Two halves, and the second is the reason it exists:

- **A generator.** Pages with TOML front matter become a static site — sidebar nested from the page
  paths, infobox, numbered contents, cited references, search, pictures, a theme that follows the reader.
  Addresses work served and opened off disk alike.
- **A set of refusals.** A paragraph that states something and cites nothing. A reference citing a
  document rather than code. A heading that asks a question instead of naming its section. A page longer
  than anyone will read. A page edited since its date was recorded. A picture whose subject has changed.
  A page nobody approved.

## Why it exists

Documentation dies the same way every time: it grows faster than anyone reads it, nobody can tell which
sentences were checked, and by the time it is wrong it still looks authoritative. The corpus it was
extracted from had grown to 75,000 words its owner had stopped reading.

This tool is for the case where **somebody reads the wiki instead of reading the source.** That makes an
untraceable sentence worse than a missing one: the reader has no way to catch it, and it looks exactly
like a sentence somebody verified. So every statement is cited to the code it came from, or carries the
mark that says it is not — and *"no source"* is an acceptable answer where silence is not.

Every rule in it was added after the failure it prevents actually happened. The check that refuses a
question as a heading found nine on the day it was written, by an agent that had written the rule
forbidding them.

## Users

- **A person who owns a system they no longer write the code for**, and needs to see how it behaves
  without reading it.
- **An agent writing or revising those pages**, which is why the skill ships with the tool rather than
  being left to each project to invent.

## Scope

- **Covers:** rendering; the checks; the skill and its worked example; a local server that shows cited
  source files as readable text; a published build with clean addresses; a reader-facing build with
  everything internal removed; carrying rule changes into a project on update.
- **Refuses:** knowing anything about the project it documents — no project name, no domain word, no
  assumption about how that project describes its own assets, enforced by a test over both the code and
  the skill. Generating pages from the thing they describe: a description derived from an implementation
  agrees with it whatever it does, and catching the disagreement is the whole point. Silently updating
  itself. Scaffolding, opinions about hosting, and anything a second project has not yet asked for.

## External systems

- `uv` (`https://docs.astral.sh/uv/`) — how a project runs a pinned version without installing anything.
  One install per machine, never per project.
- `mistune` — the markdown parser, pinned exactly. The rendered pages are held to rules this tool
  enforces, and a parser changing its output underneath a project would turn every page red at once for
  no reason anyone could see.
- Python 3.11 or newer, for `tomllib` in the standard library.
