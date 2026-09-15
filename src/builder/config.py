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
# The same line split around its value, so the value alone is replaced and a comment after it is kept.
VERSION_VALUE = re.compile(r"""^(\s*version\s*=\s*)(?:"(?:[^"\\]|\\.)*"|'[^']*')(\s*(?:#.*)?)$""")


class WikiError(Exception):
    """Something the person running this must fix, phrased for them rather than for a stack trace."""


def load_config(wiki_dir):
    """The settings file as TOML, or raise saying it is missing or unreadable."""
    path = wiki_dir / CONFIG
    if not path.is_file():
        raise WikiError(f"there is no {CONFIG} in {wiki_dir}")
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise WikiError(f"{CONFIG} is unreadable: {error}") from error


def read_coverage(wiki_dir):
    """The patterns naming the source files `wiki coverage` counts, as [include, exclude], or None.

    A project keeps its source wherever it likes, so the tool counts only the files the project names.
    """
    table = load_config(wiki_dir).get("coverage")
    if table is None:
        return None
    patterns = []
    for key, required in (("include", True), ("exclude", False)):
        value = table.get(key, None if required else []) if isinstance(table, dict) else None
        if (not isinstance(value, list) or not all(isinstance(item, str) and item for item in value)
                or (required and not value)):
            raise WikiError(f"{CONFIG}: coverage.{key} must list patterns of files relative to the project, "
                            f'such as {key} = ["src/**/*.py"]')
        patterns.append(value)
    return patterns


def read_config(wiki_dir):
    """Return (site, budget, sections) for a project, or raise saying what is missing."""
    loaded = load_config(wiki_dir)

    site = loaded.get("site", {})
    if not site.get("name"):
        raise WikiError(f"{CONFIG} has no site.name")
    url = site.get("url")
    if url is not None and not (isinstance(url, str) and url.startswith(("https://", "http://"))):
        raise WikiError(f"{CONFIG}: site.url must be a full address starting with https:// or http://, "
                        "such as https://docs.example.org")
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
    try:
        # Read as written, so a file with Windows line endings is written back with them.
        with path.open(encoding="utf-8", newline="") as stream:
            text = stream.read()
        before = tomllib.loads(text)
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise WikiError(f"{CONFIG} is unreadable: {error}") from error
    ending = "\r\n" if "\r\n" in text else "\n"
    # Only inside [tool]: a version line in any other table is another setting. Each line keeps the ending
    # it was written with, and a line added takes the file's.
    setting = 'version = "%s"' % version
    rows = text.splitlines(keepends=True)
    lines = [row.rstrip("\r\n") for row in rows]
    ends = [row[len(line):] for row, line in zip(rows, lines)]
    table, header, written = None, None, False
    for index, row in enumerate(lines):
        heading = TABLE_HEADER.match(row)
        if heading:
            table = heading.group(1)
            if table == "tool" and not row.lstrip().startswith("[[") and header is None:
                header = index
        elif table == "tool" and VERSION_SETTING.match(row):
            value = VERSION_VALUE.match(row)
            lines[index] = (value.group(1) + '"%s"' % version + value.group(2)) if value else setting
            written = True
            break
    if not written and header is not None:
        ends[header] = ends[header] or ending
        lines.insert(header + 1, setting)
        ends.insert(header + 1, ends[header])
    elif not written:
        while lines and not lines[-1].strip():
            lines.pop()
            ends.pop()
        if ends:
            ends[-1] = ends[-1] or ending
        block = ["", "# Written by `wiki sync`. Which release of the tool these pages",
                 "# were written against; `wiki check` says so when they differ.", "[tool]", setting]
        lines += block
        ends += [ending] * len(block)
    text = "".join(line + end for line, end in zip(lines, ends))
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
    path.write_text(text, encoding="utf-8", newline="")
