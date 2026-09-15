+++
title = "Local server"
subtitle = "a local server for the built site and the files its references name"
status = "approved"
intent = """
The local server exists so that following a citation lands on the code it names, readable in the browser,
rather than on a download or a dead link. What a person sees should always be what was just built.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki serve", note = "or wiki with no command", cite = ["serve", "default"] },
  { label = "Port option", value = "--port", cite = "port" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Address", value = "127.0.0.1", cite = "loopback" },
  { label = "Default port", value = "8787", cite = "serve" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Scope", value = "the whole project", cite = "root" },
  { label = "Hidden files", value = "never served", cite = "hidden" },
  { label = "Host names", value = "127.0.0.1, localhost", cite = "host" },
  { label = "Reach", value = "this machine only", cite = "loopback" },
  { label = "Caching", value = "none", cite = "cache" },
]
+++

`wiki serve` builds the site, serves it at 127.0.0.1 on port 8787, and opens a browser at it.[^serve] It is
also what `wiki` does when it is given no command at all.[^default] How the site itself is made is
described on [Site](site.md).

## Root

**The server shows the whole project, not only the site.**[^root] A page can link to any file in the
project, and a browser cannot follow a link above the folder it is served from.[^paths]

That means anything that can reach the server can read every file in the project.[^root] For that reason, it
answers only on this machine.[^loopback] **A hidden file is never served**: an address with any part
starting with a full stop, such as `.env` or `.git/config`, is answered with page not found, and so is a
file that a link in the project leads into a hidden folder or out of the project.[^hidden] It answers only a
request addressed to 127.0.0.1 or localhost, so a web page that gives its own domain that address cannot
read the project through it.[^host]

## Sources

Code, settings and markdown files open **as text in the browser** instead of downloading, across 38 common
file types.[^text] Anything else, such as the site's own pages and pictures, is served as it normally
would be.[^text] Every answer tells the browser not to guess another type, so a text file is never read as
a page.[^sniff]

## Freshness

The server never rebuilds the site, so a page edited while it runs appears after `wiki build` and a
reload.[^rebuild] **Nothing the server sends may be cached**, so a rebuilt page appears on the next
reload.[^cache] The
addresses of the stylesheet and the script also change whenever their contents do, so even a tab holding
an old copy picks up the new one.[^stamp]

## Errors

A request answered with a success status is not logged; redirects and failures are.[^log] If the port is already in use, the server says
so, names `--port` as the way to pick another, and exits with 2.[^port]

[^serve]: `src/builder/serve.py` — `serve()` binds `127.0.0.1` and opens the site's address with
    `webbrowser.open()`; `src/builder/cli.py` — `run()` builds first, and `main()` defaults the port to
    `PORT`, 8787.
[^default]: `src/builder/cli.py` — `run()` treats no command as `"serve"`.
[^root]: `src/builder/serve.py` — `serve()` roots the handler at the project and points the browser at
    the site beneath it.
[^paths]: `src/builder/build.py` — `rewrite_references()` turns a link to a file outside the site into a
    path from the page to that file.
[^loopback]: `src/builder/serve.py` — `serve()` listens on `127.0.0.1` only.
[^text]: `src/builder/serve.py` — `shown_as_text()` answers every suffix in `AS_TEXT` as `text/plain`, and
    leaves every other type to the stock handler.
[^hidden]: `src/builder/serve.py` — `Handler.send_head()` answers 404 when any part of the decoded path
    starts with `.`, or when the file it resolves to is outside the project or has such a part inside it.
[^host]: `src/builder/serve.py` — `Handler.send_head()` answers 403 when the request's `Host` names
    anything but `LOCAL_NAMES`.
[^sniff]: `src/builder/serve.py` — `Handler.end_headers()` sends `X-Content-Type-Options: nosniff`.
[^rebuild]: `src/builder/cli.py` — `run()` builds once before it calls `serve()`; `src/builder/serve.py` —
    `serve()` only serves.
[^cache]: `src/builder/serve.py` — `Handler.end_headers()` sends `Cache-Control: no-store, must-revalidate`,
    `Pragma: no-cache` and `Expires: 0`.
[^stamp]: `src/builder/build.py` — `write_site()` adds a digest of each asset to its address.
[^log]: `src/builder/serve.py` — `Handler.log_message()` drops any status starting with 2, and logs every
    other.
[^port]: `src/builder/serve.py` — `serve()` catches the `OSError` a taken port raises and returns 2;
    `src/builder/cli.py` — `main()` defines `--port`.
