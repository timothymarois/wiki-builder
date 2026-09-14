+++
title = "wiki serve"
subtitle = "build the site and read it in a browser"
status = "approved"
intent = """
wiki serve exists so that a person can read the wiki as it stands by typing one command. It should always
show what was just built, and only to this machine.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Command", value = "wiki serve", note = "or wiki alone" },
  { label = "Options", value = "--port, --root, --wiki" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Address", value = "127.0.0.1" },
  { label = "Default port", value = "8787" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", note = "once stopped" },
  { label = "Problems", value = "1" },
  { label = "Misuse", value = "2", note = "including a port in use" },
]
+++

`wiki serve` builds the site, serves it on this machine, and opens a browser at it. It runs until it is
stopped with ctrl-c.[^serve] Typing `wiki` alone does the same.[^alone] How the server behaves is described
on [Local server](../serving.md).

## Usage

It takes the options every command shares, and a port.[^usage]
```sh
wiki serve [--root ROOT] [--wiki WIKI] [--port PORT]
```

## Options

| Option | Meaning | Default |
|---|---|---|
| `--port PORT` | the port to serve on[^usage] | 8787 |

## Output

It prints what `wiki build` prints, then the address it is serving.[^output]

## Exit codes

It exits with 0 once stopped, 1 when a page stops the build, and 2 when there is no wiki or the port is
already in use.[^exit]

[^serve]: `src/builder/cli.py` — `run()` builds, then calls `serve()`; `src/builder/serve.py` — `serve()`
    binds `127.0.0.1`, opens a browser, and returns 0 on `KeyboardInterrupt`.
[^alone]: `src/builder/cli.py` — `run()` treats no command as `"serve"`, on `PORT` when no port was given.
[^usage]: `src/builder/cli.py` — `main()` gives `serve` the shared options and `--port`, defaulting to
    `PORT`, 8787.
[^output]: `src/builder/serve.py` — `serve()` prints the address it serves.
[^exit]: `src/builder/cli.py` — `main()` returns 2 with no wiki and 1 for a `WikiError`;
    `src/builder/serve.py` — `serve()` returns 2 when the port is taken.
