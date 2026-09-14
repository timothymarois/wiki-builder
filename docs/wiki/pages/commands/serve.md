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
  { label = "Command", value = "wiki serve", note = "or wiki alone", cite = ["usage", "alone"] },
  { label = "Options", value = "--port, --root, --wiki", cite = "usage" },
]

[[infobox]]
group = "Values"
rows = [
  { label = "Address", value = "127.0.0.1", cite = "serve" },
  { label = "Default port", value = "8787", cite = "usage" },
]

[[infobox]]
group = "Exit codes"
rows = [
  { label = "Success", value = "0", note = "once stopped", cite = "exit" },
  { label = "Problems", value = "1", cite = "exit" },
  { label = "Misuse", value = "2", note = "including a port in use", cite = "exit" },
]
+++

`wiki serve` builds the site, serves it on this machine, and opens a browser at it.[^serve] It runs until
it is stopped with ctrl-c.[^serve] Typing `wiki` alone does the same.[^alone] How the server behaves is
described on [Local server](../serving.md).

## Usage

It takes the options every command shares, and a port.[^usage]
```sh
wiki serve [-h] [--root ROOT] [--wiki WIKI] [--port PORT]
wiki serve --port 8791
```

## Options

| Option | Meaning | Default |
|---|---|---|
| `--port PORT` | the port to serve on[^usage] | 8787 |

## Output

It prints what `wiki build` prints, then the address it is serving.[^output] On a wiki of three
pages:[^output]
```text
wiki: goals                              20 words    0 cited    0 missing
wiki: index                               3 words    0 cited    0 missing
wiki: refunds                            29 words    1 cited    1 missing
wiki: 1 source cited, 1 claim marked as having no source
wiki: the collected goals read in 15 words
wiki: 3 pages written to /path/to/notes/docs/wiki/site
wiki: serving http://127.0.0.1:8791/docs/wiki/site/  (ctrl-c to stop)
```

## Exit codes

| Code | Condition | Message |
|---|---|---|
| `0` | it is stopped with ctrl-c[^exit] | none after the address it was serving |
| `1` | a problem stops the build | the problem |
| `2` | the port is already in use | `wiki: cannot serve on port 8787: Address already in use; choose another with --port` |
| `2` | there is no wiki where it was pointed | `wiki: no wiki at nowhere` |

[^serve]: `src/builder/cli.py` — `run()` builds, then calls `serve()`; `src/builder/serve.py` — `serve()`
    binds `127.0.0.1`, opens a browser, and returns 0 on `KeyboardInterrupt`.
[^alone]: `src/builder/cli.py` — `run()` treats no command as `"serve"`, on `PORT` when no port was given.
[^usage]: `src/builder/cli.py` — `main()` gives `serve` the shared options and `--port`, defaulting to
    `PORT`, 8787.
[^output]: `src/builder/serve.py` — `serve()` prints the address it serves, after `run()` in
    `src/builder/cli.py` prints the build.
[^exit]: `src/builder/cli.py` — `main()` returns 2 with no wiki and 1 for a `WikiError`;
    `src/builder/serve.py` — `serve()` returns 2 when the port is taken.
