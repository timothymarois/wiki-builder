+++
title = "Local server"
subtitle = "reading a wiki with its sources beside it"
status = "approved"
categories = ["Commands"]
intent = """
The local server exists so that following a citation lands on the code it names, readable in the browser,
rather than on a download or a dead link. What a person sees should always be what was just built.
"""

[[infobox]]
group = "Server"
rows = [
  { label = "Command", value = "wiki serve", note = "or wiki with no command" },
  { label = "Address", value = "127.0.0.1:8787" },
  { label = "Serves", value = "the whole project" },
]
+++

`wiki serve` builds the site, serves it, and opens a browser at it.[^serve] It is also what `wiki` does
when it is given no command at all.[^default] How the site itself is made is described on
[Site](site.md).

## Root

**The server shows the whole project, not only the site.**[^root] References point at code, which sits
outside the site, and a browser cannot follow a link above the folder it is served from.[^root]

That means anyone who can reach the server can read every file in the project. For that reason, it answers
only on this machine.[^loopback]

## Sources

Code, settings and markdown files open **as text in the browser** instead of downloading, across 38 common
file types.[^text] Anything else, such as the site's own pages and pictures, is served as it normally would
be.[^text]

## Freshness

**Nothing the server sends may be cached**, so a rebuilt page appears on the next reload.[^cache] The
addresses of the stylesheet and the script also change whenever their contents do, so even a tab holding
an old copy picks up the new one.[^stamp]

## Errors

Successful requests are not logged; failed ones are.[^log] If the port is already in use, the server says
so, names the option that picks another, and exits with 2.[^port]

[^serve]: `src/builder/serve.py` — `serve()` binds `127.0.0.1` and opens
    the site's address with `webbrowser.open()`; `src/builder/cli.py` —
    `main()` builds first and defaults the port to `PORT`, 8787.
[^default]: `src/builder/cli.py` — `main()` treats no command as `"serve"`.
[^root]: `src/builder/serve.py` — `serve()` roots the handler at the
    project and points the browser at the site beneath it.
[^loopback]: `src/builder/serve.py` — `serve()` listens on `127.0.0.1`
    only.
[^text]: `src/builder/serve.py` — `shown_as_text()` answers every suffix in
    `AS_TEXT` as `text/plain`, and leaves every other type to the stock handler.
[^cache]: `src/builder/serve.py` — `Handler.end_headers()` sends
    `Cache-Control: no-store`.
[^stamp]: `src/builder/build.py` — `write_site()` adds a digest of each
    asset to its address.
[^log]: `src/builder/serve.py` — `Handler.log_message()` drops any status
    starting with 2.
[^port]: `src/builder/serve.py` — `serve()` catches the `OSError` a taken port raises and returns 2.
