"""The one file a project owns: docs/wiki/wiki.toml.

It carries what the site is called, how long a page may be, and which pages start a branch of the
sidebar. Budgets live here rather than in this tool because a reading budget is a property of who reads
it -- a game's wiki and an interface reference plausibly want different limits, and a number nobody has
measured against a real reader should be easy for that reader to change.
"""

import tomllib

CONFIG = "wiki.toml"

# What a project gets when it says nothing. Every one of these is a guess until somebody reads the pages
# and says otherwise, which is what `calibrated` records.
DEFAULT_BUDGET = {"page": 500, "intent": 120, "goals": 3500, "calibrated": False}


class WikiError(Exception):
    """Something the person running this must fix, phrased for them rather than for a stack trace."""


def read_config(wiki_dir):
    """Return (site, budget, sections) for a project, or raise saying what is missing."""
    path = wiki_dir / CONFIG
    if not path.is_file():
        raise WikiError(f"there is no {CONFIG} in {wiki_dir}")
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise WikiError(f"{CONFIG} is unreadable: {error}") from error

    site = loaded.get("site", {})
    if not site.get("name"):
        raise WikiError(f"{CONFIG} has no site.name")
    if not loaded.get("section"):
        raise WikiError(f"{CONFIG} lists no sections, so nothing would be reachable")

    budget = dict(DEFAULT_BUDGET, **loaded.get("budget", {}))
    for name in ("page", "intent", "goals"):
        if not isinstance(budget[name], int) or budget[name] <= 0:
            raise WikiError(f"{CONFIG}: budget.{name} must be a positive number of words")
    site = dict(site, tool_version=loaded.get("tool", {}).get("version", ""))
    return site, budget, loaded["section"]


def record_version(wiki_dir, version):
    """Write which release of the tool a project is on, without disturbing anything else in the file.

    A line-level edit rather than a rewrite: the file is the project's, hand-written and commented, and a
    tool that reformats it every time it touches it is a tool people stop running.
    """
    path = wiki_dir / CONFIG
    text = path.read_text(encoding="utf-8")
    line = 'version = "%s"' % version
    if "[tool]" in text:
        out, seen = [], False
        for row in text.splitlines():
            if row.strip() == "[tool]":
                seen = True
            elif seen and row.strip().startswith("version"):
                row = line
                seen = False
            out.append(row)
        text = "\n".join(out) + "\n"
    else:
        text = text.rstrip("\n") + "\n\n# Written by `wiki sync`. Which release of the tool these pages\n" \
               "# were written against; `wiki check` says so when they differ.\n[tool]\n" + line + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
