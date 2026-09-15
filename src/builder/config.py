"""The one file a project owns: docs/wiki/wiki.toml.

It carries what the site is called, how long a page may be, and which pages start a branch of the
sidebar. Budgets live here rather than in this tool because a reading budget is a property of who reads
it -- a guide for customers and a reference for engineers plausibly want different limits, and a
number nobody has measured against a real reader should be easy for that reader to change.
"""

import re
import tomllib

CONFIG = "wiki.toml"

# What a project gets when it says nothing. Every one of these is a guess until somebody reads the pages
# and says otherwise, which is what `calibrated` records.
DEFAULT_BUDGET = {"page": 500, "intent": 120, "goals": 3500, "calibrated": False}

# A table's header, [name] or [[name]], with any comment after it; and the release's line inside [tool].
TABLE_HEADER = re.compile(r"^\s*\[\[?\s*([^\[\]]+?)\s*\]\]?\s*(?:#.*)?$")
VERSION_SETTING = re.compile(r"^\s*version\s*=")


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
    if not path.is_file():
        raise WikiError(f"there is no {CONFIG} in {wiki_dir}; write one with a [site] name and at least one "
                        "[[section]], then run `wiki sync` again")
    text = path.read_text(encoding="utf-8")
    try:
        before = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise WikiError(f"{CONFIG} is unreadable: {error}") from error
    # Only inside [tool]: a version line in any other table is another setting.
    setting = 'version = "%s"' % version
    lines = text.splitlines()
    table, header, written = None, None, False
    for index, row in enumerate(lines):
        heading = TABLE_HEADER.match(row)
        if heading:
            table = heading.group(1)
            if table == "tool" and not row.lstrip().startswith("[[") and header is None:
                header = index
        elif table == "tool" and VERSION_SETTING.match(row):
            lines[index] = setting
            written = True
            break
    if not written and header is not None:
        lines.insert(header + 1, setting)
    elif not written:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", "# Written by `wiki sync`. Which release of the tool these pages",
                  "# were written against; `wiki check` says so when they differ.", "[tool]", setting]
    text = "\n".join(lines) + "\n"
    # Read back before saving: a line edit can be fooled, by a header inside a multi-line string or a
    # [[tool]] list, and the file must then be left as the project wrote it.
    tool = before.get("tool", {})
    try:
        unchanged = isinstance(tool, dict) and tomllib.loads(text) == {**before,
                                                                         "tool": {**tool, "version": version}}
    except tomllib.TOMLDecodeError:
        unchanged = False
    if not unchanged:
        raise WikiError(f'{CONFIG} could not take the release without changing another setting; set version = '
                        f'"{version}" in its [tool] table by hand, then run `wiki sync` again')
    path.write_text(text, encoding="utf-8", newline="\n")
