+++
title = "Deployment (GitHub)"
subtitle = "publishing a wiki on GitHub"
status = "approved"
intent = """
This guide exists so that a project on GitHub can publish its wiki as a website for free, read by people
who never open the repository, and only in a state that passed its checks. A project should get there with
one workflow and a DNS record.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki publish", cite = "publish" },
  { label = "Host", value = "GitHub Pages", cite = "pages" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Domain", value = "wiki-builder.marois.dev", cite = "cname" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Condition", value = "wiki check passes", cite = "order" },
]
+++

`wiki publish` builds the site into a folder, with addresses that end in a folder rather than a
file.[^publish] Every page is a folder holding one `index.html`, and every link names the folder, so no address a reader follows ends in `.html` and no host setting is needed to hide it.[^publish] What the build makes is described on [Site](site.md), and the same guide for another
free host on [Deployment (Cloudflare)](deployment-cloudflare.md).

## Workflow

A project adds one workflow that checks the wiki, publishes it, and hands the result to GitHub
Pages.[^pages] The action installs `wiki` and leaves it installed, so a later step in the same job can run
it.[^action] If the check fails, the job stops and nothing is published.[^order]

```yaml
# .github/workflows/pages.yml
name: pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: timothymarois/wiki-builder@TAG
      - run: wiki publish _site
      - run: echo "DOMAIN" > _site/CNAME
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: github-pages
    steps:
      - uses: actions/deploy-pages@v4
```

## Settings

**GitHub Pages is switched on before the workflow first runs**: in the repository's settings, under
Pages and then Build and deployment, the source is GitHub Actions.[^source] Until it is, the build job
passes and the deploy job fails with a 404 saying to enable GitHub Pages.[^enable] The workflow writes the
domain into a `CNAME` file at the root of the site.[^cname]

| Setting | Value |
|---|---|
| Pages source, under Build and deployment | GitHub Actions[^source] |
| Custom domain | the domain in `CNAME` |
| DNS record | a `CNAME` from the domain to `OWNER.github.io`[^dns] |
| HTTPS | enforced, once GitHub has issued the certificate[^https] |

## Example

wiki-builder deploys its own wiki to wiki-builder.marois.dev the same way, on every push to
`main`.[^pages]

## External links

- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Managing a custom domain for your GitHub Pages site](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [Securing your GitHub Pages site with HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https)
- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [actions/deploy-pages](https://github.com/actions/deploy-pages)

[^publish]: `src/builder/cli.py` — `run()` builds with `links="clean"` for `publish`, into a folder
    `guard_output()` allows; `build()` then empties `LINK_SUFFIX`, so a link names the folder and not its
    `index.html`.
[^source]: GitHub Docs — [Configuring a publishing source for your GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site):
    under Settings, Pages, "Build and deployment", the source is set to GitHub Actions; and
    [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages):
    custom workflows must first be enabled for the repository.
[^enable]: GitHub — [actions/deploy-pages](https://github.com/actions/deploy-pages/blob/v4/src/internal/deployment.js):
    when creating the deployment returns 404, the error adds "Ensure GitHub Pages has been enabled".
[^dns]: GitHub Docs — [Managing a custom domain for your GitHub Pages site](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site):
    a subdomain needs a `CNAME` record pointing to `<user>.github.io` or `<organization>.github.io`,
    without the repository name.
[^https]: GitHub Docs — [Securing your GitHub Pages site with HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https):
    **Enforce HTTPS** is in the repository's Pages settings, and the certificate is provisioned after the
    DNS check that starts when the custom domain is set.
[^pages]: `.github/workflows/pages.yml` — the `build` job checks and publishes the wiki, and the `deploy`
    job runs `actions/deploy-pages`.
[^action]: `action.yml` — installs wiki-builder with `pip` into the Python `actions/setup-python` puts on
    the path.
[^order]: `.github/workflows/pages.yml` — `deploy` needs `build`, whose first step after checkout is the
    check.
[^cname]: `.github/workflows/pages.yml` — writes `wiki-builder.marois.dev` into `_site/CNAME` before the
    upload.
