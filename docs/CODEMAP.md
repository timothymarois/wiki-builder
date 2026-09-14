# Codemap

*Where each kind of thing lives. Inventory, not explanation — the reasoning is in* [the brief](./wiki/pages/brief.md)
*and the rules are in* [../AGENTS.md](../AGENTS.md).

Counts are of lines, and are meant to show shape and growth at a glance.

## Project (root — 6 tracked files)

- `pyproject.toml` — the package: distribution `wiki-builder`, command `wiki`, `mistune` pinned exactly,
  Python 3.11 or newer for `tomllib`.
- `action.yml` — the GitHub Action a project uses to check its wiki in CI: installs wiki-builder from the
  action's own copy, then runs `wiki check`.
- `README.md` — what it is, how a project installs it, and how a project updates.
- `AGENTS.md` / `CLAUDE.md` — the rules. Byte-identical, changed in the same commit.
- `.gitignore` — generated output, environments, caches.

## Continuous integration (`.github/workflows/` — 3 workflows)

The first two run on every push to `main` and every pull request; `pages.yml` runs on pushes to `main`.
The kind of CI other projects include is `action.yml` at the root.

- `tests.yml` — the tool's tests on Python 3.11 and 3.12, installed rather than run from the tree.
- `wiki.yml` — wiki-builder's own `docs/wiki`, checked through `action.yml`.
- `pages.yml` — checks the wiki through `action.yml`, publishes it, and deploys it to GitHub Pages at
  `wiki-builder.marois.dev`.

## Documentation (`docs/`)

- `CODEMAP.md` — this file.
- `wiki/` — the tool's own wiki, written with it and held to its own checks. `uv run wiki serve` reads it.
  `wiki/pages/brief.md` is the brief — what the tool is, who it is for, and what it refuses — kept there
  so people read it on the wiki and agents read the same file.

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

## Skills (`.agents/skills/` — 3, linked from `.claude/skills/`)

What an agent working here must load. The repository owns each one, and none of them references a skill
it does not own.

| Skill | For |
|---|---|
| `using-python` | Any Python: boundaries, naming, errors, resources, testing mechanics, traps |
| `testing-code` | Any change in behaviour: which boundary holds the risk, and proving a test has teeth |
| `writing-wiki-pages` | A link to `src/skill/` — the copy that ships, so there is only one of it |

## The skill (`src/skill/` — not a builder feature)

Prose the builder carries to whoever installs it, which is why it sits beside the builder rather than
inside it.

| File | Holds |
|---|---|
| `SKILL.md` | How to write a page: the intent contract, naming, what may never appear, the voice |
| `references/page-standard.md` | The worked example — a page done well, the same content done badly, and the difference |
| `references/reference-standard.md` | The same for reference pages — a command and an endpoint, each done well and badly |
| `references/naming-and-grammar.md` | Names a writer chooses and names the software owns, and the grammar pages are held to |
| `references/reference-pages.md` | How a page documents a command, endpoint, function, settings file or event |

`wiki sync` writes every one of them into the consuming project, where its agents read them. A built wheel carries
them inside the package; a checkout leaves them where they were written, and `build.skill_dir()` finds
them either way.

## Tests (`tests/` — 132 cases)

`tests/test_build.py` (1410 lines). Each case builds a small wiki in a temporary directory, breaks exactly
one rule, and asserts the tool names it. Run them with:

```sh
uv run --with mistune==3.3.4 python -m unittest discover -s tests -t tests
```

Two classes carry properties rather than cases: `ServingTests`, that a cited file is shown rather than
downloaded and that nothing is cached; and `PackageTests`, that neither the code nor the skill names
anything about any project.

## What a project looks like

The shape the tool expects to find, and the shape of wiki-builder's own `docs/wiki/`.

```
docs/wiki/
  wiki.toml          the site's name, the reading budgets, the sidebar
  pages/**.md        a page's path is its address and its place in the sidebar
  images/            pictures, and PICTURES.toml recording what each shows
  UPDATED.toml       when each page last changed. Written by the tool
  site/              the rendered site. Generated; never committed
```
