# Codemap

*Where each kind of thing lives. Inventory, not explanation — the reasoning is in* [BRIEF.md](./BRIEF.md)
*and the rules are in* [../AGENTS.md](../AGENTS.md).

Counts are of lines, and are meant to show shape and growth at a glance.

## Project (root — 7 tracked files)

- `pyproject.toml` — the package: distribution `wiki-builder`, command `wiki`, `mistune` pinned exactly,
  Python 3.11 or newer for `tomllib`.
- `README.md` — what it is, how a project installs it, and how a project updates.
- `CHANGELOG.md` — every release, and for one that adds a check, which pages it will fail.
- `AGENTS.md` / `CLAUDE.md` — the rules. Byte-identical, changed in the same commit.
- `.gitignore` — generated output, environments, caches.

## The builder (`src/builder/` — the package)

| File | Holds |
|---|---|
| `build.py` | The generator and every check. Reads pages, writes a site, returns the reasons a wiki is not fit to read |
| `cli.py` | What `wiki` does when typed: build, check, serve, sync, bless, publish, player |
| `config.py` | `wiki.toml` — a project's site name, reading budgets and sidebar — and the release it was written against |
| `serve.py` | A local server rooted at the project, so a citation opens the file it names as readable text |
| `assets/wiki.css` | The look. Lifted from a prototype its owner approved; light and dark |
| `assets/wiki.js` | Search over an inlined index, the theme switch, the mobile menu, the lightbox, copy |
| `assets/template.html` | The page, as named holes |

## The skill (`src/skill/` — not a builder feature)

Prose the builder carries to whoever installs it, which is why it sits beside the builder rather than
inside it.

| File | Holds |
|---|---|
| `SKILL.md` | How to write a page: the intent contract, naming, what may never appear, the voice |
| `references/the-standard.md` | The worked example — a page done well, the same content done badly, and the difference |

`wiki sync` writes both into the consuming project, where its agents read them. A built wheel carries
them inside the package; a checkout leaves them where they were written, and `build.skill_dir()` finds
them either way.

## Tests (`tests/` — 84 cases)

`tests/test_build.py` (     903 lines). Each case builds a small wiki in a temporary directory, breaks exactly
one rule, and asserts the tool names it. Run them with:

```sh
uv run --with mistune==3.3.4 python -m unittest discover -s tests -t tests
```

Two classes carry properties rather than cases: `ServingTests`, that a cited file is shown rather than
downloaded and that nothing is cached; and `PackageTests`, that neither the code nor the skill names
anything about any project.

## What a project looks like

Not in this repository — this is the shape the tool expects to find.

```
docs/wiki/
  wiki.toml          the site's name, the reading budgets, the sidebar
  pages/**.md        a page's path is its address and its place in the sidebar
  images/            pictures, and PICTURES.toml recording what each shows
  UPDATED.toml       when each page last changed. Written by the tool
  site/              the rendered site. Generated; never committed
```
