# wiki-builder

**A wiki a person can read, built from markdown a person wrote, where every statement is traced to the
code it came from.**

It renders pages into a Wikipedia-shaped static site — sidebar, infobox, numbered contents, cited
references — and then refuses the things that make documentation rot. That second half is the point.
Rendering markdown is easy; keeping a document true for a year is not.

## Why it exists

Documentation dies the same way every time. It grows faster than anyone reads it, nobody can tell which
sentences were checked, and by the time it is wrong it still looks authoritative. wiki-builder exists for
the case where **somebody is reading the wiki instead of reading the source** — so a sentence they cannot
trace is a sentence they have to take on faith.

So it refuses:

| | |
|---|---|
| A sentence that states something and cites nothing | `{missing}` is a fine answer; silence is not |
| A reference that cites a project document instead of code | A page of prose is another claim, not an answer |
| A heading that asks a question or rates itself | "Where it goes" — the reader wanted "Home" |
| A page longer than anyone will read | Budgets you set, that nag until you have measured them |
| A page edited since its date was recorded | So a date on a page means something |
| A picture whose subject has changed | Re-render it, or bless it with a reason |
| A page nobody can reach | Every page is in the sidebar, and a draft says it is one |

Each of those was added after the failure it prevents actually happened.

## Install

Nothing to install. [uv](https://docs.astral.sh/uv/) runs it from a pinned version:

```sh
uvx --from git+https://github.com/timothymarois/wiki-builder@v0.1.0 wiki --help
```

In a project, that goes in one wrapper the repository commits:

```sh
#!/bin/sh
# scripts/dev-wiki.sh
set -eu
WIKI_VERSION=v0.1.0        # the pin. Bump this to update.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec uvx --from "git+https://github.com/timothymarois/wiki-builder@$WIKI_VERSION" \
     wiki "$@" --root "$ROOT"
```

That is the whole integration, for any project on any stack. No virtual environment to activate, no
`requirements.txt`, nothing installed globally. The version is in the file, so it shows up in a diff.

## Use

```sh
wiki build       render docs/wiki/pages into docs/wiki/site
wiki check       every reason the wiki is not fit to read
wiki serve       build, serve, and open a browser at it
wiki sync        write the skill into the project, and record the release
wiki bless       a picture whose subject moved, with why it is still true
wiki publish     build with clean addresses, for a host
wiki player      build the reader-facing view, with everything internal removed
```

A project looks like this:

```
docs/wiki/
  wiki.toml          the site's name, the reading budgets, the sidebar
  pages/**.md        the pages. A page's path is its address and its place in the sidebar
  images/            pictures, and PICTURES.toml recording what each one shows
  UPDATED.toml       when each page last changed. Written by the tool
  site/              the rendered site. Generated; do not commit it
```

`docs/wiki/site/index.html` opens straight off disk — no server — because links end in `index.html`.
`wiki publish` builds the same site with clean addresses for a host that can serve them.

wiki-builder keeps its own wiki in `docs/wiki/`, written with the tool and held to its checks. From a
checkout, `uv run wiki serve` builds it and opens it.

## The skill

Half of wiki-builder is not code. `wiki sync` writes a skill into your repository — `.agents/skills/` or
`.claude/skills/` — that tells an agent how to write a page: the intent contract, how to name things,
what may never appear, and a worked example with the same content written badly beside it.

**It belongs in your repository rather than inside the package** because agents read it from there, and a
change to how pages must be written belongs in a diff somebody reviews.

`wiki sync --skill-dir tools/skills` puts it in a folder of your choosing instead, relative to the
project. `wiki sync --no-skill` records the release without writing the skill at all. Wherever it goes, a
copy already there is brought up to date with the release.

## Updating

```sh
1.  WIKI_VERSION=v0.1.0 → v0.2.0     one line, in the diff
2.  ./scripts/dev-wiki.sh sync        re-writes the skill, records the release
3.  ./scripts/dev-wiki.sh check       fails, naming every page the new rules break
```

**A release that adds a check is a breaking release.** New rules find old pages — that is what they are
for — so `check` names every page a release will fail, rather than stopping at the first. Nothing updates
itself: a documentation build that goes red on a morning you changed nothing is how people stop trusting
the build.

## Continuous integration

wiki-builder is also a GitHub Action. A project checks its wiki on every push and pull request with one
step, and the job fails on every reason the wiki is not fit to read: an uncited sentence or infobox row, a
question for a heading, a page over its budget, a stale date, a picture whose subject changed, or a wiki
synced against a different release.

```yaml
# .github/workflows/wiki.yml
name: wiki
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: timothymarois/wiki-builder@TAG
        with:
          wiki: docs/wiki      # the default; set it only if the wiki lives elsewhere
```

`TAG` is a wiki-builder release, the same one `scripts/dev-wiki.sh` pins, so the check in CI is the
check that ran locally. The action installs the tool from its own copy at that release. Its inputs are
`root` (the project, default `.`), `wiki` (default `docs/wiki`) and `python-version` (default `3.12`).

wiki-builder runs two workflows of its own: `tests`, the tool's tests on Python 3.11 and 3.12, and
`wiki`, the same action on its own `docs/wiki`.

## Publishing

`wiki publish` builds the site for a web host. wiki-builder deploys its own wiki to
`https://wiki-builder.marois.dev` with GitHub Pages: `.github/workflows/pages.yml` checks the wiki,
publishes it and deploys it on every push to `main`. The wiki's Installation page, and its two Deployment
guides for GitHub and Cloudflare, walk a project through the same setup.

## Requirements

Python 3.11 or newer, and `uv`. One install per machine, not per project.
