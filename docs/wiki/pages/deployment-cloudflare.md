+++
title = "Deployment (Cloudflare)"
subtitle = "publishing a wiki on Cloudflare"
status = "approved"
intent = """
This guide exists so that a project can publish its wiki on Cloudflare as a website for free, read by
people who never open the repository, and only in a state that passed its checks. Cloudflare should build
it from the repository on every push, with no workflow file to keep.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Commands", value = "wiki check, wiki publish", cite = ["exit", "publish"] },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Output directory", value = "_site", cite = "publish" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Condition", value = "wiki check passes", cite = "exit" },
]
+++

Cloudflare Pages builds a project's wiki from its repository with one build command, which installs
wiki-builder, checks the wiki and runs `wiki publish`.[^git] If the check fails, the command stops and
nothing is published.[^exit] What `wiki publish` makes is described on [wiki publish](commands/publish.md),
and the same guide for GitHub on [Deployment (GitHub)](deployment-github.md). A sign-in in front of the
published wiki is described on [Authentication (Cloudflare)](deployment-cloudflare/authentication.md).

## Build

The build command is one line.[^git] It installs from a git address, which needs `git`, and Cloudflare's
list of build image tools names `pip` but not `git`.[^image]

```sh
pip install "git+https://github.com/timothymarois/wiki-builder@TAG" && wiki check && wiki publish _site
```

`wiki check` exits with 1 when it finds any problem, so the command stops there.[^exit] `wiki publish` then
builds into `_site`, the folder Cloudflare serves.[^publish][^output]

## Settings

The project is created under Workers & Pages, with Create application, Pages and Connect to Git, and its
build settings are entered then.[^git]

| Setting | Value |
|---|---|
| Framework preset | none{missing} |
| Build command | the command above[^exit] |
| Build output directory | `_site`[^publish] |
| Python version | the build image's default, newer than wiki-builder's 3.11 floor[^image][^floor] |
| Custom domain | the subdomain, added under the project's custom domains[^domains] |

When the domain's zone is already on Cloudflare, adding the custom domain creates its DNS record.[^domains]

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
[^image]: Cloudflare Docs — [Build image](https://developers.cloudflare.com/pages/configuration/build-image/):
    the current image's default Python is 3.13.3, and `PYTHON_VERSION` selects another; its tools list
    `pip` and do not list `git`.
[^floor]: `pyproject.toml` — `requires-python = ">=3.11"`.
[^domains]: Cloudflare Docs — [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/):
    when the site is already a Cloudflare zone, its `CNAME` record is added automatically once the DNS
    record is confirmed.
[^exit]: `src/builder/cli.py` — `run()` returns 1 when `check()` finds a problem, and `main()` returns
    that as the exit code.
