# Wiki Builder

**A wiki a person can read, built from markdown, where every statement is traced to the code it came
from.**

It renders pages into a Wikipedia-style static site (sidebar, infobox, contents, citations and search) and
checks them: an uncited sentence, a question for a heading, a page too long to read, a stale picture or an
unreachable page fails the check. The full documentation is the wiki itself, built with the tool:
**[wiki-builder.marois.dev](https://wiki-builder.marois.dev)**.

## Install

Nothing to install per project. [uv](https://docs.astral.sh/uv/) runs a pinned release, from one wrapper
the project commits:

```sh
#!/bin/sh
# scripts/dev-wiki.sh
set -eu
WIKI_VERSION=v0.7.0        # the pin. Bump this to update.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec uvx --from "git+https://github.com/timothymarois/wiki-builder@$WIKI_VERSION" \
     wiki "$@" --root "$ROOT"
```

Pages live in `docs/wiki/pages`, and `docs/wiki/wiki.toml` names the site and its sidebar.
[Installation](https://wiki-builder.marois.dev/installation/) walks through a first wiki.

## Commands

```text
wiki build     render the pages into docs/wiki/site
wiki check     every reason the wiki is not fit to read
wiki coverage  list the source files no page cites
wiki families  list child pages that share no declared layout
wiki serve     build the site, serve it, and open it in a browser
wiki sync      write the agent skill into the project, and record the release
wiki publish   build the site with clean addresses, for a host
wiki user      build the reader-facing view, with everything internal removed
wiki bless     record that a changed picture is still true
wiki audit     record that pages were checked against the code today
```

## Updating

1. Bump `WIKI_VERSION` in the wrapper.
2. Run `./scripts/dev-wiki.sh sync` to update the skill and record the release.
3. Run `./scripts/dev-wiki.sh check`. A release that adds a check names every page the new rule finds.

## Continuous integration

One step checks the wiki on every push and pull request:

```yaml
# .github/workflows/wiki.yml
name: wiki
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: timothymarois/wiki-builder@v0.7.0
```

## More

- [Brief](https://wiki-builder.marois.dev/brief/): purpose, reasoning, users, scope and outside systems
- [Skill](https://wiki-builder.marois.dev/skill/): the instructions an agent follows to write a page
- [GitHub Pages](https://wiki-builder.marois.dev/deployment-github/) and
  [Cloudflare](https://wiki-builder.marois.dev/deployment-cloudflare/): publishing a wiki

Requires Python 3.11 or newer, and uv.
