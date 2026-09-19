+++
title = "Authentication"
subtitle = "Cloudflare Access or a password prompt in front of a published wiki"
status = "approved"
intent = """
This guide exists so that a project can deploy its wiki on Cloudflare behind a sign-in in the browser, so
that only the readers the project chooses can read it. A reader who has not signed in should see none of
the wiki.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Services", value = "Cloudflare Access, Pages Functions", cite = ["pin", "middleware"] },
  { label = "Middleware file", value = "functions/_middleware.js", cite = "middleware" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Sign-in code lifetime", value = "10 minutes", cite = "pin" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Coverage", value = "every file on the address", note = "markdown copies and llms.txt included", cite = ["hostname", "middleware"] },
  { label = "Password storage", value = "an encrypted Pages secret", cite = "secrets" },
]
+++

A wiki published on Cloudflare Pages can ask for a sign-in before it shows any page, in one of two ways:
**Cloudflare Access**, which emails each allowed reader a sign-in code, or a **Pages Function** that asks
the browser for a shared user name and password.[^pin][^middleware] Cloudflare recommends Access for a
production sign-in, and a password prompt is safe only over HTTPS, because it sends the password
unencrypted.[^basic] Publishing the wiki is described on [Cloudflare](../deployment-cloudflare.md).

`wiki publish` writes a markdown copy beside each page and an `llms.txt` listing them, and each holds the
wiki's text, so a sign-in guards those files as well as the pages.[^copies]

## Cloudflare Access

**Access lets in only the email addresses its policy allows**, and each reader signs in with a code sent to
that address, with no identity provider to connect.[^pin][^policy] The code expires ten minutes after the
reader asks for it.[^pin] A policy's Allow action admits the readers its rules match: named addresses
under Emails, or a whole domain under Emails ending in.[^policy] Access protects a whole address, so the
markdown copies and `llms.txt` sit behind it with the pages.[^hostname][^copies]

Each address the wiki is served from is protected on its own.[^preview][^pagesdev]

| Address | Setting |
|---|---|
| Preview deployments | the project's Settings, then Enable access policy[^preview] |
| `PROJECT.pages.dev` | edit the policy that Enable access policy creates, delete the `*` from its Subdomain field and save, then enable the access policy again[^pagesdev] |
| Custom domain | under Zero Trust, Access controls, then Applications: Create new application, Self-hosted and private, Add public hostname, and the domain[^custom] |

**A custom domain without its own Access policy shows a sign-in that does not work.**[^custom] The Zero
Trust Free plan asks for a payment method when the account is set up, and does not charge it.[^free]

## Password prompt

A Pages Function at `functions/_middleware.js` runs in front of every request, static files included, and
passes an accepted request on to the page.[^middleware] The `functions` folder sits at the root of the
repository Cloudflare builds, not inside `_site`.[^functions] The user name and password are Pages secrets,
added with Encrypt selected under the project's Settings, then Variables and Secrets, before the
deployment that reads them.[^secrets]

The middleware below adapts Cloudflare's Basic Authentication example to Pages: it reads `WIKI_USER` and
`WIKI_PASSWORD` from those secrets, compares both in constant time, and answers a missing or wrong password
with the `401` that makes the browser ask again.[^basic][^secrets]

```js
// functions/_middleware.js
const encoder = new TextEncoder();

// Compares in constant time, so the time taken reveals nothing about the password.
function timingSafeEqual(a, b) {
  const aBytes = encoder.encode(a);
  const bBytes = encoder.encode(b);
  if (aBytes.byteLength !== bBytes.byteLength) {
    return !crypto.subtle.timingSafeEqual(aBytes, aBytes);
  }
  return crypto.subtle.timingSafeEqual(aBytes, bBytes);
}

function signIn() {
  return new Response("Sign in to read the wiki.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="wiki", charset="UTF-8"' },
  });
}

export async function onRequest(context) {
  const { WIKI_USER, WIKI_PASSWORD } = context.env;
  if (!WIKI_USER || !WIKI_PASSWORD) {
    return new Response("WIKI_USER and WIKI_PASSWORD are not set.", { status: 500 });
  }
  const [scheme, encoded] = (context.request.headers.get("Authorization") || "").split(" ");
  if (scheme !== "Basic" || !encoded) {
    return signIn();
  }
  let credentials;
  try {
    credentials = atob(encoded);
  } catch {
    return signIn();
  }
  const colon = credentials.indexOf(":");
  const user = credentials.substring(0, colon);
  const password = credentials.substring(colon + 1);
  if (colon < 0 || !timingSafeEqual(WIKI_USER, user) || !timingSafeEqual(WIKI_PASSWORD, password)) {
    return signIn();
  }
  return context.next();
}
```

## On a Worker

On a **Worker with static assets**, **Cloudflare serves a matching asset before the Worker script
runs**, so a sign-in in front of the pages needs `assets.run_worker_first` in the Worker's
configuration.[^first] A `functions/` folder is not read there; `wrangler pages functions build` compiles
one into a single Worker script.[^compile]

```jsonc
{
  "name": "a-wiki",
  "main": "./worker/index.js",
  "assets": { "directory": "./_site/", "binding": "ASSETS", "run_worker_first": true }
}
```

Cloudflare marks neither as replacing the other, so a project already on Pages has nothing to
change.[^neither]

## External links

- [One-time PIN login](https://developers.cloudflare.com/cloudflare-one/identity/one-time-pin/)
- [Access policies](https://developers.cloudflare.com/cloudflare-one/policies/access/)
- [Known issues](https://developers.cloudflare.com/pages/platform/known-issues/)
- [Middleware](https://developers.cloudflare.com/pages/functions/middleware/)
- [HTTP Basic Authentication](https://developers.cloudflare.com/workers/examples/basic-auth/)
- [Worker script routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/)
- [Migrating from Pages to Workers](https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/)

[^pin]: Cloudflare Docs — [One-time PIN login](https://developers.cloudflare.com/cloudflare-one/identity/one-time-pin/):
    a reader enters an email address and, when an Access policy allows it, receives a PIN that expires
    10 minutes after the request; no identity provider is needed.
[^policy]: Cloudflare Docs — [Access policies](https://developers.cloudflare.com/cloudflare-one/policies/access/):
    the Allow action lets in the users a policy's rules match, with the Emails selector for named
    addresses and Emails ending in for a domain.
[^hostname]: Cloudflare Docs — [Publish a self-hosted application to the Internet](https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/self-hosted-public-app/):
    an Access application is added for a public hostname on a domain active on Cloudflare.
[^preview]: Cloudflare Docs — [Preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/):
    Enable access policy protects the preview deployments and not the `pages.dev` domain or a custom
    domain.
[^pagesdev]: Cloudflare Docs — [Known issues](https://developers.cloudflare.com/pages/platform/known-issues/):
    the `pages.dev` domain is protected by deleting the `*` from the Subdomain field of the policy Enable
    access policy creates, saving, and enabling the access policy again.
[^custom]: Cloudflare Docs — [Known issues](https://developers.cloudflare.com/pages/platform/known-issues/):
    a custom domain needs a Self-hosted and private application under Zero Trust, Access controls,
    Applications, and without its policy the Access sign-in renders but does not work.
[^free]: Cloudflare Docs — [Get started](https://developers.cloudflare.com/cloudflare-one/setup/): the
    Zero Trust Free plan still asks for a payment method, and does not charge it.
[^middleware]: Cloudflare Docs — [Middleware](https://developers.cloudflare.com/pages/functions/middleware/):
    `functions/_middleware.js` runs on the entire application, including in front of static files, and
    `context.next()` passes the request on.
[^functions]: Cloudflare Docs — [Functions - Get started](https://developers.cloudflare.com/pages/functions/get-started/):
    the `/functions` directory is at the root of the Pages project, not in the static root.
[^secrets]: Cloudflare Docs — [Bindings](https://developers.cloudflare.com/pages/functions/bindings/): a
    secret is added under Settings, Variables and Secrets with Encrypt selected, is read from
    `context.env`, and is set before the deployment that uses it.
[^basic]: Cloudflare Docs — [HTTP Basic Authentication](https://developers.cloudflare.com/workers/examples/basic-auth/):
    Basic Authentication sends credentials unencrypted and needs HTTPS, Cloudflare Access is recommended
    for production, credentials are compared with `crypto.subtle.timingSafeEqual`, and a `401` carrying
    `WWW-Authenticate` prompts the browser for credentials.
[^first]: Cloudflare Docs — [Worker script routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/):
    "If you have both static assets and a Worker script configured, Cloudflare will first attempt to serve
    static assets if one matches the incoming request", and `assets.run_worker_first` runs the Worker
    before each request instead.
[^compile]: Cloudflare Docs — [Migrating from Pages to Workers](https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/):
    "Workers, on the other hand, will default to serving static assets ahead of your Worker script, unless
    you have configured `assets.run_worker_first`", and a `functions/` folder "must first compile these
    functions into a single Worker script with the `wrangler pages functions build` command".
[^neither]: Cloudflare Docs — [Middleware](https://developers.cloudflare.com/pages/functions/middleware/)
    and [Migrating from Pages to Workers](https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/):
    neither marks Pages as deprecated or in maintenance, and neither tells a new project to use Workers.
[^copies]: `src/builder/build.py` — `write_site()` writes each page's `index.md` with `markdown_copy()` and
    `llms.txt` with `agent_index()` in every build but a user build; `src/builder/cli.py` — `run()` builds
    `wiki publish` for the internal audience.
