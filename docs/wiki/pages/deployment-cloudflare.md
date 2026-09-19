+++
title = "Cloudflare"
subtitle = "the build command and settings that deploy the wiki to Cloudflare Pages"
status = "approved"
intent = """
This guide exists so that a project can publish its wiki on Cloudflare as a website for free, read by
people who never open the repository, and only in a state that passed its checks. Cloudflare should build
it from the repository on every push, with no workflow file to keep.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Host", value = "Cloudflare Pages", cite = "git" },
  { label = "Build command", value = "./scripts/deploy-wiki.sh _site", cite = "git" },
  { label = "Commands", value = "wiki check, wiki publish", cite = ["exit", "publish"] },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Output directory", value = "_site", cite = "publish" },
  { label = "Price", value = "free", note = "up to 500 builds a month", cite = "limits" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Condition", value = "wiki check passes", cite = "exit" },
  { label = "Custom domain", value = "added under the project's custom domains", cite = "domains" },
]
+++

Cloudflare Pages builds a project's wiki from its repository with one build command, which runs the
project's own deploy script.[^git] That script installs the pinned release, checks the wiki and runs
`wiki publish`, as [Installation](installation.md) describes. If the check fails, the script stops and
nothing is published.[^exit] What `wiki publish` makes is described on [wiki publish](commands/publish.md),
and the same guide for GitHub on [GitHub Pages](deployment-github.md). A sign-in in front of the
published wiki is described on [Authentication](deployment-cloudflare/authentication.md).

## Build

The build command names the script and nothing else.[^git]

```sh
./scripts/deploy-wiki.sh _site
```

The script the project commits reads the release pin, installs that release, checks the wiki and
publishes it.{missing}

```sh
#!/bin/sh
# scripts/deploy-wiki.sh -- check the wiki and publish it, for a host that builds from the repository.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-_site}"
WIKI_VERSION="$(cat "$ROOT/scripts/wiki-version")"
pip install --quiet "git+https://github.com/timothymarois/wiki-builder@$WIKI_VERSION"
wiki check --root "$ROOT"
wiki publish "$OUT" --root "$ROOT"
```

It installs with `pip` rather than `uvx`, which the build image need not carry.[^image]
**The release is named in the repository, not here**: the script reads `scripts/wiki-version`, so bumping
it is a line in a diff rather than a value typed into the dashboard, where nothing records that it
changed.{missing} The script installs from a git address, which needs `git`, and Cloudflare's list of build
image tools names `pip` but not `git`.[^image] `wiki check` exits with 1 when it finds any problem, so the
script stops there.[^exit] `wiki publish` then builds into `_site`, the folder Cloudflare
serves.[^publish][^output] A wiki at the root of the repository rather than in `docs/wiki` has the script
pass `--wiki .`, which the tool takes as it stands.[^wikipath]

## Settings

The project is created under Workers & Pages, with Create application, Pages and Connect to Git, and its
build settings are entered then.[^git]

| Setting | Value |
|---|---|
| Framework preset | none[^preset] |
| Build command | `./scripts/deploy-wiki.sh _site`[^git] |
| Build output directory | `_site`[^publish] |
| Python version | the build image's default, newer than wiki-builder's 3.11 floor[^image][^floor] |
| Custom domain | the subdomain, added under the project's custom domains[^domains] |

When the domain's zone is already on Cloudflare, adding the custom domain creates its DNS record.[^domains]
Cloudflare Pages is free on Cloudflare's Free plan, which allows 500 builds a month and up to 20,000 files
in a site.[^limits]

## External links

- [Git integration guide](https://developers.cloudflare.com/pages/get-started/git-integration/)
- [Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)
- [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)
- [Serving Pages](https://developers.cloudflare.com/pages/configuration/serving-pages/)
- [Limits](https://developers.cloudflare.com/pages/platform/limits/)

[^publish]: `src/builder/cli.py` — `run()` builds with `links="clean"` for `publish`, into the folder it is
    given; `build()` then empties `LINK_SUFFIX`, so a link names the folder and not its `index.html`.
[^git]: Cloudflare Docs — [Git integration guide](https://developers.cloudflare.com/pages/get-started/git-integration/):
    a project is created from Workers & Pages with Create application, Pages and Connect to Git, where
    its build command and build output directory are set.
[^output]: Cloudflare Docs — [Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/):
    the build output directory is where the build command writes the built version of the site.
[^preset]: Cloudflare Docs — [Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/):
    a project not using a preset sets its own build command.
[^image]: Cloudflare Docs — [Build image](https://developers.cloudflare.com/pages/configuration/build-image/):
    the current image's default Python is 3.13.3, and `PYTHON_VERSION` selects another; its tools list
    `pip` and do not list `git`.
[^floor]: `pyproject.toml` — `requires-python = ">=3.11"`.
[^wikipath]: `src/builder/build.py` — `wiki_of()` uses a given `--wiki` as it stands, and joins
    `docs/wiki` to the project only when none is given.
[^domains]: Cloudflare Docs — [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/):
    when the site is already a Cloudflare zone, its `CNAME` record is added automatically once the DNS
    record is confirmed.
[^exit]: `src/builder/cli.py` — `run()` returns 1 when `check()` finds a problem, and `main()` returns
    that as the exit code.
[^limits]: Cloudflare Docs — [Limits](https://developers.cloudflare.com/pages/platform/limits/): the Free
    plan allows 500 builds a month, and a site on it can hold up to 20,000 files.
