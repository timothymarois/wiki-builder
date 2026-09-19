"""Render a directory of markdown pages into a browsable static wiki.

This tool knows nothing about whatever it documents. It is handed pages, a configuration file and a
picture ledger, and it writes a site: one directory per page, each holding an index.html, so a page can
be opened off disk as readily as served.

It reads nothing else. In particular it never reads the thing being documented: a page derived from an
implementation agrees with that implementation by construction, so it could never catch it behaving
differently from the way it is supposed to, and catching that is the only reason the wiki exists. Pages
are written by people who read the code.

The rendered site is not meant to be committed -- it is built before it is served, so it cannot go
stale. What `check` refuses is a page that no longer renders, a page that states something and cites
nothing, a heading that asks a question instead of naming its section, a page that has outgrown its
reading budget, and a picture whose subject has changed since the picture was made.
"""

import argparse
import datetime
import hashlib
import html as html_module
import json
import os
import posixpath
import re
import shutil
import sys
import tempfile
import tomllib
import urllib.parse
from importlib import resources
from pathlib import Path

import mistune
from mistune.util import unikey

from . import __version__
from .config import WikiError, read_config, read_coverage, CONFIG

# Front matter is TOML between these fences, so it is read by the standard library and costs no parser.
FENCE = "+++"

# Who a build is for: everyone working on the project, or the users of whatever it documents.
AUDIENCES = ("internal", "user")

# Where the tool's own files live, so it runs from anywhere rather than only inside a repository laid
# out the way the first one was.
ASSETS = resources.files(__package__) / "assets"

# Diagrams are drawn by Mermaid, the diagram language GitHub draws from a ```mermaid block. Its browser build
# ships inside the package, pinned by its name, so a wiki draws them served, published, or opened straight
# off disk with no network. Mermaid is MIT licensed; its licence travels with it.
MERMAID = "mermaid-12.0.0.min.js"
MERMAID_LICENSE = "mermaid-12.0.0.LICENSE"
MERMAID_BLOCK = re.compile(r'<pre><code class="language-mermaid">(.*?)</code></pre>', re.S)
# A code block exactly as markdown renders it: a bare <pre>, through its own closing tag.
BARE_PRE = re.compile(r"(<pre>.*?</pre>)", re.S)


def skill_dir():
    """Where the skill is, whether this is an installed copy or a source checkout.

    The skill lives beside the builder in the source tree rather than inside it, because it is not a
    feature of the builder -- it is prose the builder carries to whoever installs it. A built wheel puts
    it inside the package; an editable install leaves it where it was written.
    """
    packaged = Path(str(resources.files(__package__))) / "skill"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parents[1] / "skill"


SKILL = skill_dir()

# The collected-intent page. Generated, never written, because it is the surface a change is approved
# against and a maintained copy would drift from the intents it claims to collect.
GOALS_ID = "goals"

LEDGER = "PICTURES.toml"

# PDFs a page links live in this folder beside the pictures, and a build carries only the ones a page links.
# The limit is one fixed figure for every wiki, not a setting.
FILES = "files"
MEGABYTE = 1024 * 1024
PDF_LIMIT = 20 * MEGABYTE

# When each page last changed, and what it looked like then. Committed, because the rendered site is not:
# a date taken from the clock on every build would say "today" forever and tell a reader nothing. The
# date moves only when the page's own content moves, which is also what decides whether it is rewritten.
DATES = "UPDATED.toml"
MONTHS = ("January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")

# A link the renderer must not touch: it already points where it means to.
SETTLED_LINK = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|#|//)")
# A link that leaves the wiki. It opens in a new tab so the reader keeps their place, carries nofollow so a
# published wiki lends no standing to what it points at, and is marked so the reader knows before following.
OUTSIDE_LINK = re.compile(r"^(?:https?:)?//", re.I)
OUTSIDE = ' class="ext" target="_blank" rel="nofollow noopener noreferrer"'
# A link to a page the wiki does not have, drawn red the way an encyclopedia marks a page nobody has written.
NEW_PAGE = ' class="new" title="This page does not exist"'

HEADING = re.compile(r"<(h2|h3)>(.*?)</\1>", re.S)
TAG = re.compile(r"<[^>]+>")
ATTRIBUTE = re.compile(r'(href|src)="([^"]*)"')
LONE_FIGURE = re.compile(r"<p>(<figure.*?</figure>)</p>", re.S)
# A footnote's definition: its first line and every indented or blank line after it, the reference in group 1.
FOOTNOTE = re.compile(r"^\[\^[^\]]+\]:(.*(?:\n(?:[ \t]+.*|))*)", re.M)
# Where a reference-style link's address is defined. It names an address, not a fact, so it is blanked
# before a page is read as statements -- as a footnote definition is, and for the same reason. Without
# this, exempting "[Name][ref]" where it is used would still leave its definition asking for a citation
# no writer can give it.
LINK_DEFINITION = re.compile(r"^[ \t]*\[[^\]^][^\]]*\]:[ \t]*\S+.*$", re.M)

# Everything the user build must not carry. Each is emitted by this file, in this exact shape, so
# stripping them is removing what we put there rather than parsing arbitrary HTML.
# An <aside>, not a <div>: the user build strips this block with a non-greedy match, which would stop
# at the first closing tag of the same kind. Markdown can put a <div> inside a citation -- a table
# wrapper, or raw HTML someone pasted -- and the strip would then truncate and leak the rest of the
# block into a user build. Nothing this renderer emits ever nests an <aside>.
INTERNAL_BLOCK = re.compile(r'<aside class="cites"[^>]*>.*?</aside>', re.S)
INTERNAL_MARKER = re.compile(r'<sup class="ref[^"]*"[^>]*>.*?</sup>', re.S)

# A missing citation. Every statement on a page is either traced to the code or marked here, in the place
# a reader already looks for a source, because every statement, fact, requirement and behaviour needs a
# citation or this mark. Two things put the mark there -- the
# thing is not built yet, or nobody has found where it happens -- and for a reader the consequence is the
# same: do not take this on faith. Written {missing} in the prose, or missing = true on an infobox row.
# Never shown to a user.
MISSING = re.compile(r"\{missing\}")
# Rendered code, inline or a block, kept whole when a page is split around it.
CODE_HTML = re.compile(r"(<pre\b.*?</pre>|<code\b.*?</code>)", re.S)
MISSING_CITATION = ('<sup class="ref nocite" data-audience="internal" '
                    'title="No source cited: either this is not built yet, or where it happens has not been '
                    'found">[?]</sup>')


# --------------------------------------------------------------------------------------------------
# reading


def read_front_matter(path):
    """Return (metadata, markdown body) for one page, or raise if the fences are wrong."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith(FENCE + "\n"):
        raise WikiError(f"{path.name} does not open with a {FENCE} front-matter fence")
    rest = text[len(FENCE) + 1:]
    end = rest.find("\n" + FENCE + "\n")
    if end == -1:
        raise WikiError(f"{path.name} never closes its {FENCE} front-matter fence")
    try:
        meta = tomllib.loads(rest[:end])
    except tomllib.TOMLDecodeError as error:
        raise WikiError(f"{path.name} has unreadable front matter: {error}") from error
    return meta, rest[end + len(FENCE) + 2:]


def counted_words(body):
    """The words a reader reads on a page.

    A reference is followed and a code block copied, so neither is read the way prose is; and a table's
    pipes and dashed line are how it is drawn, not what it says, so only the words in its cells count.
    """
    text = FENCED.sub("", strip_footnote_definitions(body))
    lines = [line for line in text.splitlines() if not TABLE_SEPARATOR.match(line)]
    return len("\n".join(lines).replace("|", " ").split())


def read_pages(pages_dir, intent_budget):
    """Every page in the directory, by id, sorted so two runs agree."""
    if not pages_dir.is_dir():
        raise WikiError(f"there are no pages: {pages_dir} does not exist")
    pages = {}
    for path in sorted(pages_dir.rglob("*.md")):
        meta, body = read_front_matter(path)
        # The id keeps the path, so pages/a/b.md is "a/b" and is addressed as /a/b/.
        page_id = path.relative_to(pages_dir).with_suffix("").as_posix()
        if page_id.rsplit("/", 1)[-1] == "source":
            raise WikiError("a page may not be called source.md: every page's source view lives there")
        # The subtitle was called kicker before. Read as nothing, every page that still says kicker
        # would lose its subtitle and no build would say so.
        if "kicker" in meta:
            raise WikiError(f"{path.name} gives its subtitle as kicker, which is now called subtitle; "
                            "rename kicker to subtitle")
        # An audience the build does not know is refused rather than read quietly as internal, which would
        # keep the page out of the user build and say nothing about it.
        if meta.get("audience", "internal") not in AUDIENCES:
            raise WikiError(f"{path.name} gives its audience as {meta['audience']!r}; an audience is "
                            "\"internal\" or \"user\"")
        if not isinstance(meta.get("image", ""), str):
            raise WikiError(f"{path.name} gives its image as {meta['image']!r}; name one picture recorded in "
                            f"{LEDGER}, such as image = \"page-anatomy.svg\"")
        for required in ("title", "intent"):
            if not str(meta.get(required, "")).strip():
                raise WikiError(f"{path.name} has no {required}; every page must say what it is for")
        intent_words = len(meta["intent"].split())
        if intent_words > intent_budget:
            raise WikiError(f"{path.name}'s intent runs to {intent_words} words, over the {intent_budget} "
                            "an intent may use; say what the system is for, not how it works")
        pages[page_id] = {
            "id": page_id,
            "path": path,
            "meta": meta,
            "body": body,
            "raw": path.read_text(encoding="utf-8"),
            "title": meta["title"],
            "intent": " ".join(meta["intent"].split()),
            "subtitle": meta.get("subtitle", ""),
            "hatnote": meta.get("hatnote", ""),
            "audience": meta.get("audience", "internal"),
            # Draft until approved. A page states what part of the system is for, and that needs approval
            # -- an agent may draft one, and drafting is not approving.
            "status": meta.get("status", "draft"),
            "categories": list(meta.get("categories", [])),
            # Neither a reference nor a code block is read the way prose is: one is followed, the other
            # copied or run. Code blocks are not counted.
            "words": counted_words(body),
        }
    if not pages:
        raise WikiError(f"{pages_dir} holds no pages; a wiki that renders nothing did not run")
    return pages


def strip_footnote_definitions(body):
    """Prose only. A citation is provenance, and counting it against a page would punish citing."""
    return FOOTNOTE.sub("", body)


def read_dates(wiki):
    """What each page hashed to when it last changed, and the day that was."""
    path = wiki / DATES
    if not path.is_file():
        return {}
    fix = "restore it from version control, since `wiki build` and `wiki audit` write it"
    try:
        dates = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise WikiError(f"{DATES} is unreadable: {error}; {fix}") from error
    for page_id in sorted(dates):
        if not isinstance(dates[page_id], dict):
            raise WikiError(f"{DATES} is unreadable: {page_id} is not a table; {fix}")
    return dates


def write_dates(wiki, dates):
    lines = [
        "# When each page last changed, what it hashed to then, and when it was last audited.",
        "#",
        "# Written by `wiki build` and `wiki audit`, never by hand. A page is re-rendered, and its date",
        "# moves, only when its own content has changed -- so the date on a page means something, and a",
        "# build that changed nothing writes nothing. An audit keeps its day through later edits.",
        "",
    ]
    for page_id in sorted(dates):
        lines.append("[%s]" % toml_key(page_id))
        lines.append("updated = %s" % toml_string(dates[page_id]["updated"]))
        lines.append("digest = %s" % toml_string(dates[page_id]["digest"]))
        if dates[page_id].get("audited"):
            lines.append("audited = %s" % toml_string(dates[page_id]["audited"]))
        lines.append("")
    (wiki / DATES).write_text("\n".join(lines), encoding="utf-8", newline="\n")


def spoken_date(iso):
    """1763-03-01 becomes 1 March 1763. A reader should not have to parse a date."""
    year, month, day = (int(part) for part in iso.split("-"))
    return "%d %s %d" % (day, MONTHS[month - 1], year)


def read_ledger(images_dir):
    """What each picture shows, and what its subject hashed to when it was made."""
    path = images_dir / LEDGER
    if not path.is_file():
        return {}
    fix = "correct it by hand so each picture is a table"
    try:
        ledger = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise WikiError(f"{LEDGER} is unreadable: {error}; {fix}") from error
    for name in sorted(ledger):
        if not isinstance(ledger[name], dict):
            raise WikiError(f"{LEDGER} is unreadable: {name} is not a table; {fix}")
    # A build copies each picture by the name its table carries, so a name that climbed out of the folder
    # would copy any file in the project into the site.
    for name in sorted(ledger):
        if name in ("", ".", "..") or "/" in name or "\\" in name:
            raise WikiError(f"{LEDGER} has a table for {name}, which is not a file name; name each table for "
                            "a picture's file name alone, such as page-anatomy.svg")
    return ledger


def write_ledger(images_dir, ledger):
    """Rewrite the ledger. Only the shapes used here -- strings and lists of strings -- are emitted."""
    lines = [
        "# What each picture shows, and what its subject hashed to when the picture was made.",
        "#",
        "# The gate fails when a depicted asset has moved and its picture has not been re-made, because a",
        "# wiki read instead of the source cannot afford a picture of something that no longer",
        "# exists. Clear it by re-rendering, or by `wiki bless <picture> \"<reason>\"`",
        "# when the change did not alter what the picture shows.",
        "",
    ]
    for name in sorted(ledger):
        entry = ledger[name]
        lines.append("[%s]" % toml_key(name))
        for field in ("made", "digest"):
            if entry.get(field):
                lines.append("%s = %s" % (field, toml_string(entry[field])))
        depicts = entry.get("depicts", [])
        lines.append("depicts = [%s]" % ", ".join(toml_string(item) for item in depicts))
        if entry.get("blessed"):
            lines.append("blessed = %s" % toml_string(entry["blessed"]))
        lines.append("")
    (images_dir / LEDGER).write_text("\n".join(lines), encoding="utf-8", newline="\n")


def script_json(value):
    """A value as JSON that is safe inside a script element.

    A browser ends a script at the first `</script>` whatever JSON surrounds it, so a title carrying one
    would run the rest as a script of its own. JSON may spell any character as an escape, and these three
    are the ones HTML reads.
    """
    return (json.dumps(value, sort_keys=True, separators=(",", ":"))
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def toml_string(value):
    return json.dumps(str(value), ensure_ascii=False)


def toml_key(value):
    return json.dumps(str(value), ensure_ascii=False)


# --------------------------------------------------------------------------------------------------
# addresses
#
# One directory per page, each holding an index.html, so an address is "plants/" and never
# "plants.html". Every reference is relative: a leading slash resolves to the filesystem root and
# breaks the moment the site is served from anywhere but the root of a host.


def wiki_of(root, wiki=None):
    """Where a project keeps its wiki. `docs/wiki` unless it says otherwise."""
    return Path(wiki) if wiki else root / "docs/wiki"


def page_directory(page_id):
    return "" if page_id == "index" else page_id + "/"


def category_directory(slug):
    return "category/" + slug + "/"


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


# What a link to a page ends in.
#
# "index.html" by default, because that link works in both places a wiki gets read: served over a port,
# and opened straight off disk by double-clicking a file. A bare "plants/" works only when something is
# serving it -- a browser handed a directory over file:// lists its contents instead of showing the page.
#
# Empty for publishing, where "plants/" is the address and nothing ends in .html. That is the only place
# the difference is worth having, and it is a flag rather than the default.
#
# One module-level value rather than an argument threaded through six functions: every link in a build is
# the same kind, build() sets it and puts it back, and there is never more than one build at a time.
LINK_SUFFIX = "index.html"


def relative_directory(from_directory, to_directory):
    """A link from one page's directory to another's.

    Percent-encoded, because the address is made of file names and is written into an href: a quote in a
    name would end the attribute, and a colon would read as a scheme such as javascript:.
    """
    rel = urllib.parse.quote(posixpath.relpath("/" + to_directory, "/" + (from_directory or ".")))
    return ("./" if rel == "." else rel + "/") + LINK_SUFFIX


def relative_file(from_directory, to_file):
    """A link from one page's directory to a file in the site, percent-encoded for the same reason."""
    return urllib.parse.quote(posixpath.relpath("/" + to_file, "/" + (from_directory or ".")))


# --------------------------------------------------------------------------------------------------
# markdown


CITATION = '<sup class="ref">[<a href="#cite-%d">%d</a>]</sup>'


def footnote_reference(renderer, key, index):
    """Wikipedia's own shape: a bracketed superscript at the claim, linked to the entry at the foot.

    The number is remembered against its footnote, so an infobox row citing the same footnote carries the
    same number, whatever order the prose happened to cite things in.
    """
    renderer.cited.setdefault(key, index)
    return CITATION % (index, index)


# An address written bare, rather than as `[title](address)` or between angle brackets, which are the two
# forms markdown links on its own. A bare one renders as text a reader cannot follow -- one wiki published
# 2,009 of them, 82% of its references. Only a scheme starts one: linking `docs.example.com` on sight
# would mark up prose that was never an address. `&amp;` is a character of the address rather than the end
# of it, because a query string carries ampersands and the page's HTML has already escaped them.
BARE_ADDRESS = re.compile(r"""https?://(?:&amp;|[^\s<>()\[\]"'&])+""")
# What an address must not be wrapped inside: a link it already has, and code, which shows text as written.
ALREADY_MARKED = re.compile(r"<a\b[^>]*>.*?</a>|<(code|pre)\b[^>]*>.*?</\1>", re.S)


def autolink_addresses(markup):
    """Make every bare address on a page clickable, leaving one already linked or shown as code alone.

    Done to the page's HTML rather than to its markdown, so what the writer typed is what the source view
    and the markdown copy still show. Trailing punctuation is handed back: an address ending a sentence
    keeps its full stop outside the link.
    """
    def wrap(found):
        address = found.group(0)
        trimmed = address.rstrip(".,;:!?")
        return '<a href="%s">%s</a>%s' % (trimmed, trimmed, address[len(trimmed):])

    parts, last = [], 0
    for marked in ALREADY_MARKED.finditer(markup):
        parts += [BARE_ADDRESS.sub(wrap, markup[last:marked.start()]), marked.group(0)]
        last = marked.end()
    parts.append(BARE_ADDRESS.sub(wrap, markup[last:]))
    return "".join(parts)


def footnote_item(renderer, text, key, index):
    return '<li id="cite-%d">%s</li>\n' % (index, text.rstrip())


def footnote_block(renderer, text):
    return ('<aside class="cites" id="cite" data-audience="internal">\n<h2>References</h2>\n'
            '<ol class="refs">\n%s</ol>\n</aside>\n' % text)


class WikiRenderer(mistune.HTMLRenderer):
    """A picture is a figure with its caption, not a bare image dropped into a paragraph.

    This is a subclass rather than a registered function because a renderer resolves its own methods
    before anything registered on it: registering "image" is silently ignored, and the pictures come out
    as plain <img> with no caption and nothing reports a problem.
    """

    def image(self, text, url, title=None):
        caption = title or text
        return ('<figure class="fig"><img src="%s" alt="%s">%s</figure>'
                % (html_module.escape(url, quote=True), html_module.escape(text, quote=True),
                   "<figcaption>%s</figcaption>" % html_module.escape(caption) if caption else ""))


def make_markdown():
    markdown = mistune.create_markdown(
        renderer=WikiRenderer(escape=True), plugins=["footnotes", "table", "strikethrough"])
    # These three the plugin adds; the renderer defines no method of its own for them, so they take.
    markdown.renderer.register("footnote_ref", footnote_reference)
    markdown.renderer.register("footnote_item", footnote_item)
    markdown.renderer.register("footnotes", footnote_block)
    markdown.renderer.cited = {}
    return markdown


def strip_tags(markup):
    return html_module.unescape(TAG.sub("", markup)).strip()


def for_user(body):
    """Remove everything this file marked internal, leaving no dangling marker behind.

    The per-heading source links need no removal here: they are added later, by number_headings, and only
    when the page has references -- which this function has just taken away.
    """
    body = INTERNAL_BLOCK.sub("", body)
    return INTERNAL_MARKER.sub("", body)


def number_headings(body):
    """Number every heading and return the contents entries."""
    entries = []
    counters = [0, 0]

    def replace(match):
        level, inner = match.group(1), match.group(2)
        if level == "h2":
            counters[0] += 1
            counters[1] = 0
            number = str(counters[0])
        else:
            counters[1] += 1
            number = "%d.%d" % (counters[0], counters[1])
        slug = "s" + number.replace(".", "-")
        entries.append((level, number, strip_tags(inner), slug))
        return '<%s id="%s"><span>%s</span></%s>' % (level, slug, inner, level)

    return HEADING.sub(replace, body), entries


def render_contents(entries):
    """The numbered contents box, shown once a page has enough sections to need one."""
    if len(entries) <= 2:
        return ""
    groups = []
    for entry in entries:
        if entry[0] == "h2" or not groups:
            groups.append((entry, []))
        else:
            groups[-1][1].append(entry)

    def item(entry, children):
        _, number, text, slug = entry
        markup = ('<li><a href="#%s"><span class="tn">%s</span>%s</a>'
                  % (slug, number, html_module.escape(text)))
        if children:
            markup += "<ol>%s</ol>" % "".join(item(child, []) for child in children)
        return markup + "</li>"

    return ('<div class="toc"><div class="th">Contents</div><ol>%s</ol></div>'
            % "".join(item(entry, children) for entry, children in groups))


def is_pdf(address):
    """Whether a link's address names a PDF, by its file name, leaving out any query or fragment after it."""
    return urllib.parse.unquote(address.partition("#")[0].partition("?")[0]).lower().endswith(".pdf")


def filed_name(source_path, address, files_dir):
    """The file name a link gives a PDF directly in the wiki's files folder, or None when it leads anywhere else.

    Only a plain file name directly in the folder counts: a link through a folder inside it, or out of it and
    back, would publish a file from wherever the path led. The author wrote the link relative to their own
    file, so it is resolved from there, and both sides are resolved for the reason `linked_page()` gives.
    """
    address = urllib.parse.unquote(address)
    name = posixpath.basename(address)
    if name in ("", ".", "..") or "\\" in name:
        return None
    if (source_path.parent / posixpath.dirname(address)).resolve() != files_dir.resolve():
        return None
    return name


def filed_pdf(source_path, address, files_dir):
    """The name of the PDF in the files folder a link leads to, or None when the folder holds no such file.

    A symbolic link is copied as the file it points at, so one leading out of the folder stops the build
    rather than publish whatever it reaches.
    """
    name = filed_name(source_path, address, files_dir)
    if name is None or not (files_dir / name).is_file():
        return None
    if not (files_dir / name).resolve().is_relative_to(files_dir.resolve()):
        raise WikiError(f"{source_path.name} links to {name}, which links to a file outside the files folder; put "
                        "the PDF itself in the wiki's files folder")
    return name


def file_size(size):
    """A file's size as a reader reads it: whole kilobytes under a megabyte, megabytes to one place above it.

    Rounded up, so a size never reads smaller than the file, and counted in 1,024s, as the limit on a PDF is,
    so a PDF the check refuses never reads as inside the limit. A file that rounds up to 1,024 kilobytes is a
    megabyte, and an empty file is no kilobyte at all.
    """
    kilobytes = -(-size // 1024)
    if kilobytes < 1024:
        return "%d KB" % kilobytes
    return "%d.%d MB" % divmod(-(-size * 10 // MEGABYTE), 10)


# A PDF link as rewrite_references() leaves it, carrying its size until the size is written after the link.
PDF_ANCHOR = re.compile(r'(<a href="[^"]*" class="pdf") data-size="([^"]*)"([^>]*>.*?</a>)', re.S)


def rewrite_references(body, directory, site_root, root, images, page_ids, pages_dir, source_path, shown,
                       files_dir, linked, found):
    """Point every link and picture where it will actually resolve from this page's directory.

    A page is written beside its fellows, so its author links the way the repository reads: a sibling
    page as name.md, anything else by its path. Both are translated here -- the sibling to a clean
    address, the path to wherever it sits relative to this page -- so one link works while reading the
    markdown and again in the browser. Each picture the body shows is added to `shown`, the pictures the
    site carries, and each PDF in the files folder it links to `linked`, the PDFs the site carries. A PDF
    link is marked with its class and size, for the viewer and for the size written after it. Every PDF
    link, published or not, is added to `found` as (page file, address), for `pdf_problems()` to judge.
    """
    here = site_root / directory if directory else site_root

    def replace(match):
        attribute, target = match.group(1), match.group(2)
        if SETTLED_LINK.match(target):
            if attribute == "href" and OUTSIDE_LINK.match(target):
                return match.group(0) + OUTSIDE
            return match.group(0)
        address, _, fragment = target.partition("#")
        if attribute == "src":
            name = posixpath.basename(urllib.parse.unquote(address))
            if name not in images:
                raise WikiError(f"{directory or 'the main page'} shows {name}, which has no entry in {LEDGER}")
            shown.add(name)
            resolved = relative_file(directory, "images/" + name)
        else:
            # A PDF in the files folder is published beside the pages. One anywhere else keeps the path below,
            # which leads nowhere once published, and `wiki check` refuses it through pdf_problems(). The address
            # is read back from the rendered page, where & is written &amp;, and a query is no part of the file.
            written = html_module.unescape(address)
            path, question, query = written.partition("?")
            if is_pdf(path):
                found.append((source_path, written + (("#" + html_module.unescape(fragment)) if fragment else "")))
                name = filed_pdf(source_path, path, files_dir)
                if name is not None:
                    linked.add(name)
                    return '%s="%s%s%s" class="pdf" data-size="%s"' % (
                        attribute, relative_file(directory, FILES + "/" + name),
                        html_module.escape(question + query, quote=True), ("#" + fragment) if fragment else "",
                        file_size((files_dir / name).stat().st_size))
            # Inside the pages tree it is a sibling page and becomes a clean address; anywhere else it is a
            # path in the repository and becomes a path from this page to it.
            target_id = linked_page(source_path, address, pages_dir)
            if target_id in page_ids:
                resolved = relative_directory(directory, page_directory(target_id))
            elif target_id is not None:
                # A page the wiki does not have: pointed where it would be, and drawn red, so nobody takes
                # it for a page that exists. `wiki check` refuses it through dead_link_problems().
                return '%s="%s%s"%s' % (attribute, relative_directory(directory, page_directory(target_id)),
                                        ("#" + fragment) if fragment else "", NEW_PAGE)
            else:
                resolved = os.path.relpath((source_path.parent / address).resolve(),
                                           here.resolve()).replace(os.sep, "/")
        return '%s="%s%s"' % (attribute, resolved, ("#" + fragment) if fragment else "")

    return ATTRIBUTE.sub(replace, body)


def linked_page(source_path, address, pages_dir):
    """The page a link to a markdown file names, or None when the link leads outside the pages.

    The author wrote the link relative to their own file, so it is resolved from there. Both sides are
    resolved, or neither: resolve() follows symlinks, and on macOS a path under /var comes back under
    /private/var, so a resolved path compared against an unresolved folder takes a page for a file, and
    the link is emitted as an absolute path that works on exactly one machine.
    """
    # The markdown parser percent-encodes an address, so it is decoded to name the file on disk.
    address = urllib.parse.unquote(address)
    if not address.endswith(".md"):
        return None
    try:
        return (source_path.parent / address).resolve().relative_to(pages_dir.resolve()).with_suffix("").as_posix()
    except ValueError:
        return None


def render_source(raw, copy_link=""):
    """The page's own markdown, and a button that copies it. The button adds no text of its own inside
    the block, so what is copied is exactly the file.

    Above it, a link to the page's markdown copy, opened as the file itself: the one place a person looking
    for the markdown already goes, in place of a separate markdown tab."""
    link = ('<p class="hat">The page as a markdown file: <a href="%s">%s</a></p>'
            % (copy_link, posixpath.basename(copy_link))) if copy_link else ""
    return link + ('<div class="srcbox"><button class="copy" type="button">Copy</button>'
                   '<pre class="src">%s</pre></div>' % html_module.escape(raw))


# --------------------------------------------------------------------------------------------------
# page parts


def row_cites(row):
    """The footnotes an infobox row cites, as its author wrote them.

    Compared through `unikey`, the markdown parser's own normalisation, and nothing else: a key normalised
    any other way matches in the check and misses in the render, and the row silently shows no number.
    """
    cite = row.get("cite", [])
    return [str(key) for key in ([cite] if isinstance(cite, str) else cite)]


def render_infobox(page, audience, directory, images, cited=None):
    """The facts a reader would actually check, in their language, as the page's author chose them."""
    groups = page["meta"].get("infobox", [])  # a generated page has no front matter and no infobox
    picture = page["meta"].get("image")
    if not groups and not picture:
        return ""
    parts = ['<aside class="ib">', '<div class="cap">%s</div>' % html_module.escape(page["title"])]
    if picture:
        if picture not in images:
            raise WikiError(f"{page['id']}.md shows {picture}, which has no entry in {LEDGER}")
        caption = page["meta"].get("image_caption", "")
        parts.append('<div class="pic"><img src="%s" alt="%s">%s</div>'
                     % (relative_file(directory, "images/" + picture),
                        html_module.escape(caption, quote=True),
                        '<div class="cc">%s</div>' % html_module.escape(caption) if caption else ""))
    shown = 0
    missing = False
    for group in groups:
        if not visible_to(audience, group.get("audience", page["audience"])):
            continue
        shown += 1
        parts.append('<div class="grp">%s</div>' % html_module.escape(group.get("group", "")))
        for row in group.get("rows", []):
            value = html_module.escape(str(row.get("value", "")))
            link = row.get("link")
            if link:
                # A value may link outside the wiki, such as to an author's site. A page is linked from
                # the text instead, where its address is rewritten to resolve from wherever it is read.
                if not OUTSIDE_LINK.match(str(link)):
                    raise WikiError(f"{page['id']}.md links the infobox row {row.get('label', '')!r} to "
                                    f"{link}, which is not an address outside the wiki; link a page from "
                                    "the text instead")
                value = '<a href="%s"%s>%s</a>' % (html_module.escape(str(link), quote=True), OUTSIDE, value)
            # A row may name the requirement that promises it. That identifier is traceability for
            # the next review of the page against the code, and it is never rendered: a row that carries
            # one shows no badge beside it.
            if row.get("missing") and audience != "user":
                missing = True
                value += " " + MISSING_CITATION
            elif audience != "user":
                # A row cites the way a sentence does: with the number its footnote has in the prose.
                value += "".join(CITATION % (cited[unikey(key)], cited[unikey(key)])
                                 for key in row_cites(row) if unikey(key) in (cited or {}))
            note = row.get("note")
            parts.append('<div class="r"><b>%s</b><span>%s%s</span></div>'
                         % (html_module.escape(str(row.get("label", ""))), value,
                            "<i>%s</i>" % html_module.escape(str(note)) if note else ""))
    if shown and missing:
        parts.append('<div class="legend">A row marked %s has no source to cite: either it is not built '
                     "yet, or where it happens has not been found.</div>" % MISSING_CITATION)
    parts.append("</aside>")
    return "\n".join(parts)


def visible_to(audience, marked):
    """Whether something marked for one audience belongs in a build for another.

    One predicate rather than the same De Morgan pair written out at every call site: the internal and
    user split is what keeps a requirement identifier or an internal page out of a user build, and a
    rule restated five times is a rule that will be changed in four places.
    """
    return audience != "user" or marked == "user"


def descendants_of(page_id, page_ids):
    """A page and everything beneath it, depth first."""
    yield page_id
    for child in children_of(page_id, page_ids):
        yield from descendants_of(child, page_ids)


def children_of(page_id, page_ids):
    """The pages that live directly beneath this one. A page's place in the tree is its own address."""
    return sorted(other for other in page_ids
                  if other != page_id and other.rsplit("/", 1)[0] == page_id)


# The mark at the right of a section's header, turned by the stylesheet when the section is shut. It is
# drawn rather than written so it takes the header's own colour in either theme.
CHEVRON = ('<svg class="chev" width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">'
           '<path d="M1 3.5 5 7.5 9 3.5" fill="none" stroke="currentColor" stroke-width="1.6" '
           'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def render_nav(sections, pages, categories, current, directory, audience):
    """The sidebar. Its shape comes from the pages, not from labels written beside them.

    A section names the pages that start a branch; everything beneath one nests under it automatically,
    because a page that lives at a/b/c is a child of the page at a/b. Nothing has to be listed twice, and
    a new page appears in the right place by being put in the right directory.
    """
    # Every page is in the sidebar, draft or not. A draft still says so above everything else on it, and
    # search, the categories and the goals still offer only what has been approved.
    visible = {page_id for page_id in pages
               if visible_to(audience, pages[page_id]["audience"])}

    def branch(page_id):
        # Children are gathered from every page, not only the visible ones: a page hidden from this
        # audience must not take its visible children down with it. They rise to where it stood.
        below = "".join(branch(child) for child in children_of(page_id, set(pages)))
        if page_id not in visible:
            return below
        # The branch the reader is in is marked, so a child page shows which page it sits under.
        above = (current or "").startswith(page_id + "/")
        link = ('<li><a class="%s" href="%s">%s</a>'
                % ("on" if page_id == current else "up" if above else "",
                   relative_directory(directory, page_directory(page_id)),
                   html_module.escape(pages[page_id]["title"])))
        holds = ' class="here"' if page_id == current or above else ""
        return link + ("<ul%s>%s</ul>" % (holds, below) if below else "") + "</li>"

    markup = []
    for section in sections:
        items = []
        for page_id in section.get("pages", []):
            if page_id not in pages:
                raise WikiError(f"the navigation lists a page {page_id!r} that does not exist")
            items.append(branch(page_id))
        for name in section.get("categories", []):
            slug = slugify(name)
            if slug not in categories:
                raise WikiError(f"the navigation lists a category {name!r} that no page belongs to")
            items.append('<li><a class="%s" href="%s">%s</a></li>'
                         % ("on" if slug == current else "",
                            relative_directory(directory, category_directory(slug)),
                            html_module.escape("Category: " + name)))
        items = [item for item in items if item]
        if not items:
            continue
        title = section.get("title", "")
        # The header is a button across the whole rail, and the pages under it sit in one box the
        # stylesheet can slide shut. The key is the title slugged, never the section's position: a
        # section added above another would otherwise inherit what a reader had shut.
        markup.append('<h5 data-sec="%s"><button type="button"><span>%s</span>%s</button></h5>'
                      '<div class="fold"><ul>%s</ul></div>'
                      % (slugify(title), html_module.escape(title), CHEVRON, "".join(items)))
    return "".join(markup)


def current_section(sections, current):
    """The key of the section the page being drawn sits in, so the sidebar can show it open.

    A reader who follows a link straight to a page should see where it sits, whatever they shut on an
    earlier visit -- so this is the one section the stored state does not close, and reaching it never
    changes what is stored.
    """
    for section in sections:
        for page_id in section.get("pages", []):
            if current == page_id or (current or "").startswith(page_id + "/"):
                return slugify(section.get("title", ""))
        for name in section.get("categories", []):
            if current == slugify(name):
                return slugify(section.get("title", ""))
    return ""


def ancestors_of(page_id, pages, audience):
    """The pages above this one that a build for this audience has, from the top down."""
    parts = page_id.split("/")
    above = ["/".join(parts[:depth]) for depth in range(1, len(parts))]
    return [ancestor for ancestor in above
            if ancestor in pages and visible_to(audience, pages[ancestor]["audience"])]


def render_crumbs(page_id, pages, directory, audience):
    """The pages above this one, each a link, so a reader on a child page sees where it sits and can climb.

    A page this build does not have is left out, as the sidebar leaves it out; with nothing left above the
    page there is no trail at all, and a top page never has one.
    """
    links = ['<a href="%s">%s</a>' % (relative_directory(directory, page_directory(ancestor)),
                                      html_module.escape(pages[ancestor]["title"]))
             for ancestor in ancestors_of(page_id, pages, audience)]
    if not links:
        return ""
    return ('      <nav class="crumbs" aria-label="Breadcrumb">%s › <span aria-current="page">%s</span></nav>\n'
            % (" › ".join(links), html_module.escape(pages[page_id]["title"])))


def render_categories(page, directory, categories):
    names = [name for name in page["categories"] if slugify(name) in categories]
    if not names:
        return ""
    return ('<div class="cats"><b>Categories:</b> %s</div>'
            % " · ".join('<a href="%s">%s</a>'
                         % (relative_directory(directory, category_directory(slugify(name))),
                            html_module.escape(name))
                         for name in sorted(names)))


# --------------------------------------------------------------------------------------------------
# the site


def collect_categories(pages, audience):
    """Every category a page claims, with the pages in it. A category nobody is in is not a category."""
    categories = {}
    for page_id in sorted(pages):
        page = pages[page_id]
        if not visible_to(audience, page["audience"]):
            continue
        # A category is a way into the wiki, so it lists only what is in the wiki.
        if page["status"] != "approved":
            continue
        for name in page["categories"]:
            categories.setdefault(slugify(name), {"name": name, "pages": []})["pages"].append(page_id)
    return categories


def goals_page(pages, sections, audience):
    """Every intent, in the order the sidebar puts them: the whole point of the thing, in one sitting."""
    ordered = goals_order(pages, sections, audience)
    body = []
    for page_id in ordered:
        page = pages[page_id]
        body.append("<h2>%s</h2>" % html_module.escape(page["title"]))
        body.append("<p>%s</p>" % html_module.escape(page["intent"]))
    return "\n".join(body), sum(len(pages[page_id]["intent"].split()) for page_id in ordered)


# The page the build lists every page on, when a wiki has one, and the marker for a family's member table.
HEALTH_ID = "health"
HEALTH_COLUMNS = ("Page", "Status", "Words", "Cited", "Missing", "Updated", "Audited")
FAMILY_TABLE = "{family-table}"
FAMILY_TABLE_LINE = re.compile(r"^[ \t]*\{family-table\}[ \t]*$", re.M)


# A table over a named set of pages, which a family's member table cannot serve: a family is a page and
# its children, and a wiki whose index differs from its tree has pages to list that are nobody's children.
# Listing a page in a section pulls its whole subtree into that one fold, so a project wanting a foldable
# section for each part has to keep those parts out of the page that indexes them.
INDEX_TABLE = "{index-table}"
INDEX_TABLE_LINE = re.compile(r"^[ \t]*\{index-table\}[ \t]*$", re.M)
# The front matter a column may show. A page's title is already the link in the first cell.
COLUMN_FIELDS = ("subtitle", "status")


def glob_pattern(pattern):
    """One page pattern as an expression that matches an address.

    Written out rather than taken from `fnmatch`, whose `*` crosses a `/` -- with it, `area/*` would match
    every page at any depth beneath area, and a table meant to list the parts of an area would list the
    whole of it. `pathlib`'s own matching would do, but it arrived after the Python this package supports.
    """
    out, at = [], 0
    while at < len(pattern):
        if pattern.startswith("**", at):
            out.append(".*")
            at += 2
        elif pattern[at] == "*":
            out.append("[^/]*")
            at += 1
        elif pattern[at] == "?":
            out.append("[^/]")
            at += 1
        else:
            out.append(re.escape(pattern[at]))
            at += 1
    return re.compile("".join(out) + r"\Z")


def index_pages(patterns, page_ids):
    """The pages an index table lists: every page matching any of its patterns, in address order.

    A pattern names addresses under `pages`, which is what a writer sees: `area/*` is the pages directly
    under area, and `area/**` is everything beneath it however deep.
    """
    found = set()
    for pattern in patterns:
        cleaned = pattern[len("pages/"):] if pattern.startswith("pages/") else pattern
        cleaned = cleaned[:-len(".md")] if cleaned.endswith(".md") else cleaned
        matches = glob_pattern(cleaned)
        found |= {page_id for page_id in page_ids if matches.match(page_id)}
    return sorted(found)


def pages_beneath(page_id, page_ids):
    """How many pages sit under this one, however deep. The number a hand-kept index gets wrong first."""
    return sum(1 for other in page_ids if other.startswith(page_id + "/"))


def index_columns(index):
    """The columns a page's index table declares, or None when it declares none this file can write."""
    columns = index.get("columns")
    if not isinstance(columns, list) or not columns:
        return None
    return [column for column in columns if isinstance(column, dict)] or None


def index_table_rows(page_id, pages, emitted, audience):
    """A page's index table: its headings, a row for each page it lists, and the totals row if asked for.

    Every value is read rather than written, so a page added anywhere beneath a listed page changes the
    count without anyone editing the table. None when the page declares no index this file can write,
    which `wiki check` reports.
    """
    index = pages[page_id]["meta"].get("index")
    if not isinstance(index, dict):
        return None
    patterns = index.get("pages")
    patterns = [patterns] if isinstance(patterns, str) else patterns
    columns = index_columns(index)
    if not isinstance(patterns, list) or not patterns or columns is None:
        return None
    written = [other for other in emitted if other != page_id]
    headings = [str(column.get("heading", "")) for column in columns]
    rows = []
    for listed in index_pages([str(pattern) for pattern in patterns], written):
        stated = {}
        for group in pages[listed]["meta"].get("infobox", []):
            if visible_to(audience, group.get("audience", pages[listed]["audience"])):
                for row in group.get("rows", []):
                    stated.setdefault(str(row.get("label", "")), str(row.get("value", "")))
        cells = []
        for column in columns:
            if column.get("count"):
                cells.append(str(pages_beneath(listed, written)))
            elif column.get("field"):
                cells.append(str(pages[listed]["meta"].get(str(column["field"]), "")).strip())
            else:
                cells.append(stated.get(str(column.get("label", "")), ""))
        rows.append((listed, cells))
    totals = None
    if index.get("total"):
        # Only a counted column has a total: summing anything a page happened to write in a cell would
        # be inventing a number nobody stated.
        totals = [str(sum(int(cells[at]) for _, cells in rows)) if column.get("count") else ""
                  for at, column in enumerate(columns)]
    return headings, rows, totals


def markdown_cell(text):
    """Text that sits in one markdown table cell without ending the cell, the row, or opening a code span."""
    return " ".join(str(text).splitlines()).replace("|", "\\|").replace("`", "\\`")


def health_rows(pages, emitted, dates, citations):
    """Every written page but the health page, A to Z by title, with the cells it shows for each.

    A page that cites nothing cannot be audited, so it shows no citation counts and no audit date. Only
    recorded dates are shown, never days since one, so two builds of one wiki write the same page.
    """
    rows = []
    for page_id in emitted:
        if page_id == HEALTH_ID:
            continue
        page = pages[page_id]
        cites = page["meta"].get("goals", True)
        cited, missing = citations.get(page_id, (0, 0))
        audited = dates.get(page_id, {}).get("audited", "")
        order = (str(page["title"]).lower(), page_id)
        cells = ["approved" if page["status"] == "approved" else "draft", str(page["words"]),
                 str(cited) if cites else "", str(missing) if cites else "",
                 spoken_date(dates[page_id]["updated"]),
                 (spoken_date(audited) if audited else "never") if cites else ""]
        rows.append((order, page_id, cells))
    return [(page_id, cells) for _, page_id, cells in sorted(rows)]


def health_summary(pages, rows):
    """The line above the health table: how many pages, drafts, pages never audited and unsourced claims."""
    def counted(count, word):
        return "%d %s%s" % (count, word, "" if count == 1 else "s")

    drafts = sum(1 for page_id, _ in rows if pages[page_id]["status"] != "approved")
    never = sum(1 for _, cells in rows if cells[5] == "never")
    missing = sum(int(cells[3]) for _, cells in rows if cells[3])
    return "%s, %s waiting on approval, %d never audited, %s with no source" % (
        counted(len(rows), "page"), counted(drafts, "draft"), never, counted(missing, "claim"))


def health_html(pages, rows, directory):
    """The health page's summary and table, as the page shows them."""
    head = "".join("<th>%s</th>" % name for name in HEALTH_COLUMNS)
    body = "".join('<tr><td><a href="%s">%s</a></td>%s</tr>'
                   % (relative_directory(directory, page_directory(page_id)),
                      html_module.escape(pages[page_id]["title"]),
                      "".join(('<td class="missing">%s</td>' if index == 3 and cell not in ("", "0") else "<td>%s</td>")
                              % html_module.escape(cell) for index, cell in enumerate(cells)))
                   for page_id, cells in rows)
    return ('<p>%s</p>\n<div class="wt"><table class="w health"><thead><tr>%s</tr></thead><tbody>%s</tbody>'
            "</table></div>\n" % (html_module.escape(health_summary(pages, rows)), head, body))


def health_markdown(pages, rows, directory):
    """The health page's summary and table, as its markdown copy carries them."""
    lines = ["", health_summary(pages, rows), "", "| %s |" % " | ".join(HEALTH_COLUMNS),
             "|%s" % ("---|" * len(HEALTH_COLUMNS))]
    lines += ["| [%s](%s) | %s |" % (markdown_cell(pages[page_id]["title"]), copy_address(directory, page_id),
                                     " | ".join(markdown_cell(cell) for cell in cells))
              for page_id, cells in rows]
    return "\n".join(lines) + "\n"


def family_table_rows(page_id, pages, emitted, audience):
    """A declared family's member table: the labels it compares, and each member this build writes with its
    value for each label, empty where the member states none. A value in an infobox group the build leaves
    out is not shown. None when the family declares no table, which `wiki check` reports.
    """
    family = pages[page_id]["meta"].get("family")
    labels = family.get("table") if isinstance(family, dict) else None
    if not isinstance(labels, list) or not labels:
        return None
    written = set(emitted)
    rows = []
    for child in children_of(page_id, set(pages)):
        if child not in written:
            continue
        values = {}
        for group in pages[child]["meta"].get("infobox", []):
            if visible_to(audience, group.get("audience", pages[child]["audience"])):
                for row in group.get("rows", []):
                    values.setdefault(str(row.get("label", "")), str(row.get("value", "")))
        rows.append((child, [values.get(str(label), "") for label in labels]))
    return [str(label) for label in labels], rows


def family_table_html(pages, table, directory):
    """A family's member table as the parent page shows it: each member linked, then its values."""
    labels, rows = table
    head = "<th></th>" + "".join("<th>%s</th>" % html_module.escape(label) for label in labels)
    body = "".join('<tr><td><a href="%s">%s</a></td>%s</tr>'
                   % (relative_directory(directory, page_directory(child)),
                      html_module.escape(pages[child]["title"]),
                      "".join("<td>%s</td>" % html_module.escape(value) for value in values))
                   for child, values in rows)
    return ('<div class="wt"><table class="w family"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (head, body))


def family_table_markdown(pages, table, directory):
    """A family's member table as the parent's markdown copy carries it."""
    labels, rows = table
    lines = ["|  | %s |" % " | ".join(markdown_cell(label) for label in labels),
             "|%s" % ("---|" * (len(labels) + 1))]
    lines += ["| [%s](%s) | %s |" % (markdown_cell(pages[child]["title"]), copy_address(directory, child),
                                     " | ".join(markdown_cell(value) for value in values))
              for child, values in rows]
    return "\n".join(lines)


def index_table_html(pages, table, directory):
    """A page's index table as it shows it: each listed page linked, then its values, then the totals."""
    headings, rows, totals = table
    head = "<th></th>" + "".join("<th>%s</th>" % html_module.escape(heading) for heading in headings)
    body = "".join('<tr><td><a href="%s">%s</a></td>%s</tr>'
                   % (relative_directory(directory, page_directory(listed)),
                      html_module.escape(pages[listed]["title"]),
                      "".join("<td>%s</td>" % html_module.escape(value) for value in values))
                   for listed, values in rows)
    if totals:
        body += ("<tr class=\"total\"><td>Total</td>%s</tr>"
                 % "".join("<td>%s</td>" % html_module.escape(value) for value in totals))
    return ('<div class="wt"><table class="w index"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (head, body))


def index_table_markdown(pages, table, directory):
    """A page's index table as its markdown copy carries it."""
    headings, rows, totals = table
    lines = ["|  | %s |" % " | ".join(markdown_cell(heading) for heading in headings),
             "|%s" % ("---|" * (len(headings) + 1))]
    lines += ["| [%s](%s) | %s |" % (markdown_cell(pages[listed]["title"]), copy_address(directory, listed),
                                     " | ".join(markdown_cell(value) for value in values))
              for listed, values in rows]
    if totals:
        lines.append("| Total | %s |" % " | ".join(markdown_cell(value) for value in totals))
    return "\n".join(lines)


def goals_order(pages, sections, audience):
    """The pages whose intents the goals page collects, in sidebar order. Shared by the rendered goals page
    and its markdown copy, so the two can never list different goals."""
    ordered = []
    seen = set()
    for section in sections:
        for top in section.get("pages", []):
            for page_id in descendants_of(top, set(pages)):
                if page_id not in pages or page_id in seen or page_id == GOALS_ID:
                    continue
                if not visible_to(audience, pages[page_id]["audience"]):
                    continue
                if pages[page_id]["status"] != "approved":
                    continue
                # A page about the wiki itself states no goal of the system, and would only dilute the one
                # page whose whole job is to read as the system's goals in one sitting.
                if not pages[page_id]["meta"].get("goals", True):
                    continue
                ordered.append(page_id)
                seen.add(page_id)
    return ordered


# One row, two views. A page with no written source -- a generated category -- shows the Article tab
# alone rather than a Source tab leading to nothing.
ARTICLE_ONLY = '      <ul><li><a class="sel">Article</a></li></ul>'


def on_article():
    """The tab row of an article: itself, and its source beside it."""
    return ('      <ul><li><a class="sel">Article</a></li>'
            '<li><a href="source/%s">Source</a></li></ul>' % LINK_SUFFIX)


def on_source():
    """And of a source view. Both go through LINK_SUFFIX: written by hand they were dead off disk, which
    is exactly the failure the suffix exists to prevent."""
    return ('      <ul><li><a href="../%s">Article</a></li>'
            '<li><a class="sel">Source</a></li></ul>' % LINK_SUFFIX)


# Words a reader gets through in a minute, for the reading time in a page's footer. Not a new figure: a page
# of 500 words, the default budget, is meant to answer in about two minutes.
READING_PACE = 250


def reading_minutes(words):
    """About how many minutes a page takes to read: whole minutes, rounded up, and never none."""
    return max(1, -(-words // READING_PACE))


def page_stats(words, cited=None, missing=None):
    """The counts a page's footer carries, written out: its words, its reading time and its citations, all
    counted by the build."""
    minutes = reading_minutes(words)
    stats = ["%d word%s" % (words, "" if words == 1 else "s"),
             "about %d minute%s to read" % (minutes, "" if minutes == 1 else "s")]
    if cited is not None:
        stats += ["%d source%s cited" % (cited, "" if cited == 1 else "s"),
                  "%d claim%s with no source" % (missing, "" if missing == 1 else "s")]
    return stats


# Which release built the site, at the foot of the sidebar and outside the part that scrolls, so a reader
# looking at a page can tell what made it without finding the repository first. The address is the tool's
# own, not the project's: the version beside it is the tool's version, and a link to the project's
# repository is the mark beside the site's name.
RAIL_FOOT = '<div class="railfoot"><a href="%s">Wiki v%s</a></div>'
WIKI_REPOSITORY = "https://github.com/timothymarois/wiki-builder"

# The GitHub mark beside the site's name, drawn inline so the site needs no network and no picture file for it.
GITHUB_LINK = ('<a class="github" href="%s" target="_blank" rel="noopener noreferrer" aria-label="GitHub" '
               'title="GitHub"><svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true">'
               '<path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
               '0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53'
               '.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 '
               '0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36'
               '.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75'
               '-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 '
               '8c0-4.42-3.58-8-8-8z"/></svg></a>')


def render_page(title, subtitle, hatnote, body_html, infobox, categories_bar, nav, index, site,
                directory, template, tabs=ARTICLE_ONLY, updated="", stamp_css="", stamp_js="",
                draft=False, llm_links="", diagram_script="", stats=(), audited=None, crumbs="",
                nav_here=""):
    body_html, entries = number_headings(body_html)
    filled = {
        "tabs": tabs,
        "crumbs": crumbs,
        "tab_title": html_module.escape("%s — %s" % (title, site["name"])),
        "css": relative_file(directory, "assets/wiki.css") + stamp_css,
        "js": relative_file(directory, "assets/wiki.js") + stamp_js,
        "home": relative_directory(directory, ""),
        "site_name": html_module.escape(site["name"]),
        # localStorage belongs to an address, not to a wiki: two wikis published under one domain, and
        # every page opened off disk, would otherwise share one set of shut sections.
        "nav_key": "wiki-nav-shut:" + slugify(site["name"]),
        "tagline_line": ("<span>%s</span>" % html_module.escape(site["tagline"])) if site.get("tagline") else "",
        "github": (GITHUB_LINK % html_module.escape(site["github"], quote=True)) if site.get("github") else "",
        "nav": nav,
        "nav_here": nav_here,
        "rail_foot": RAIL_FOOT % (WIKI_REPOSITORY, __version__),
        "title": html_module.escape(title),
        "subtitle": html_module.escape(subtitle),
        "hatnote": (('      <p class="hat draft"><b>Draft</b> — not approved yet.</p>\n' if draft else "")
                    + ('      <p class="hat">%s</p>' % html_module.escape(hatnote) if hatnote else "")),
        "infobox": infobox,
        "contents": render_contents(entries),
        "body": body_html,
        "categories": categories_bar,
        # The day a page was last audited follows the day it was updated, and says never when it has not
        # been; None leaves it out, as a user build and a generated page do.
        "footer": ('      <div class="foot">%s</div>' % "".join(
            "<span>%s</span>" % html_module.escape(part)
            for part in (["Last updated " + spoken_date(updated)] if updated else [])
            + (["Last audited " + (spoken_date(audited) if audited else "never")]
               if updated and audited is not None else [])
            + list(stats))
                   ) if updated or stats else "",
        "index": index,
        "llm_links": llm_links,
        "diagram_script": diagram_script,
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: filled.get(m.group(1), ""), template)


# --------------------------------------------------------------------------------------------------
# markdown for agents
#
# An agent reads markdown far better than a rendered page, and a static host answers one address with one
# file whoever asks, so each page is published twice: rendered, and as a markdown copy beside it, with
# llms.txt at the root listing every copy. The shape is the llms.txt proposal's.

AGENT_INDEX = "llms.txt"
AGENT_COPY = "index.md"
# A markdown link or picture as written: everything up to the address, the address, the closing bracket.
MARKDOWN_LINK = re.compile(r"(!?\[[^\]]*\]\()([^)\s]+)(\))")


def outside_code(text, change):
    """Apply a change to markdown everywhere but its code, which is shown as written."""
    def inline(segment):
        parts = re.split("(%s)" % INLINE_CODE.pattern, segment)
        return "".join(part if index % 2 else change(part) for index, part in enumerate(parts))

    out, last = [], 0
    for block in FENCED.finditer(text):
        out.append(inline(text[last:block.start()]))
        out.append(block.group(0))
        last = block.end()
    out.append(inline(text[last:]))
    return "".join(out)


def copy_address(from_directory, page_id):
    """A link from one page's folder to another page's markdown copy."""
    return urllib.parse.quote(posixpath.relpath("/" + page_directory(page_id) + AGENT_COPY,
                                                "/" + (from_directory or ".")))


def markdown_copy(page, directory, page_ids, pages_dir, ledger, files_dir, linked, extra=""):
    """A page as an agent reads it: title, subtitle and intent, then the body and references as written.

    Only addresses move. The author linked a sibling page as name.md from the pages folder, and the copy
    sits in the page's own folder in the site, so a link to a page points at that page's copy, a picture at
    the site's copy of the picture, and a PDF in the files folder at the site's copy of the PDF, which is
    added to `linked` so the site carries it. Code is left alone: a sample shows a link as written.
    """
    def readdress(match):
        opening, target, closing = match.groups()
        if SETTLED_LINK.match(target):
            return match.group(0)
        address, _, fragment = target.partition("#")
        if opening.startswith("!"):
            name = posixpath.basename(address)
            return opening + relative_file(directory, "images/" + name) + closing if name in ledger \
                else match.group(0)
        path, question, query = address.partition("?")
        if is_pdf(path):
            name = filed_pdf(page["path"], path, files_dir)
            if name is None:
                return match.group(0)
            linked.add(name)
            return (opening + relative_file(directory, FILES + "/" + name) + question + query
                    + ("#" + fragment if fragment else "") + closing)
        target_id = linked_page(page["path"], address, pages_dir)
        if target_id in page_ids:
            return opening + copy_address(directory, target_id) + ("#" + fragment if fragment else "") + closing
        return match.group(0)

    head = ["# " + page["title"], ""]
    if page["subtitle"]:
        head += ["_%s_" % page["subtitle"], ""]
    if page["status"] != "approved":
        head += ["**Status.** Draft, not approved yet.", ""]
    head += ["**Intent.** " + " ".join(page["intent"].split()), ""]
    body = outside_code(page["body"].strip("\n"), lambda text: MARKDOWN_LINK.sub(readdress, text))
    return "\n".join(head) + "\n" + body + "\n" + extra


def goals_markdown(pages, ordered, directory):
    """The intents the goals page collects, as its markdown copy carries them."""
    return "".join("\n## [%s](%s)\n\n%s\n" % (pages[page_id]["title"], copy_address(directory, page_id),
                                              " ".join(pages[page_id]["intent"].split()))
                   for page_id in ordered)


SITEMAP = "sitemap.xml"


def sitemap_xml(url, entries):
    """sitemap.xml: every address the host serves under site.url, and the day each page last changed.

    A search engine reads every address from this one file. The days come from the recorded dates, never
    the clock, so two builds of one wiki write the same bytes; a category page has no date of its own.
    """
    base = url.rstrip("/") + "/"
    rows = []
    for directory, day in sorted(entries):
        address = html_module.escape(base + urllib.parse.quote(directory) + LINK_SUFFIX)
        rows.append("  <url><loc>%s</loc>%s</url>\n" % (address, "<lastmod>%s</lastmod>" % day if day else ""))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(rows) + "</urlset>\n")


def agent_order(sections, pages, emitted):
    """Every page the build writes, each once, grouped by section in sidebar order."""
    shown, seen, order = set(emitted), set(), []
    for section in sections:
        ids = []
        for top in section.get("pages", []):
            for page_id in descendants_of(top, set(pages)):
                if page_id in shown and page_id not in seen:
                    seen.add(page_id)
                    ids.append(page_id)
        order.append((section.get("title", ""), ids))
    return order


def agent_index(site, order, pages):
    """llms.txt: the site's name, then every page's markdown copy, by section in sidebar order."""
    lines = ["# " + site["name"], ""]
    if site.get("tagline"):
        lines += ["> " + site["tagline"], ""]
    for title, ids in order:
        if ids:
            lines += ["## " + title, ""] + ["- [%s](%s)%s" % (
                pages[page_id]["title"], copy_address("", page_id),
                ": " + pages[page_id]["subtitle"] if pages[page_id]["subtitle"] else "") for page_id in ids] + [""]
    return "\n".join(lines)


def build(root, out, audience, link_root=None, today=None, record=True, links="file", wiki_dir=None,
          sitemap=False, pdf_links=None):
    """Write the whole site, and return the per-page word counts.

    `links` is "file" -- links that work served and off disk alike -- or "clean" for publishing. A list given
    as `pdf_links` receives every link to a PDF the build writes, as (page file, address).

    `out` is where the bytes go; `link_root` is where the site will be read from, which is not always the
    same place -- a check renders into a temporary directory to inspect what the real one would contain,
    and a link to a file outside the site has to be counted from where the site actually sits.
    """
    global LINK_SUFFIX
    was = LINK_SUFFIX
    LINK_SUFFIX = "" if links == "clean" else "index.html"
    try:
        return write_site(root, out, audience, link_root, today, record, wiki_of(root, wiki_dir), sitemap,
                          [] if pdf_links is None else pdf_links)
    finally:
        LINK_SUFFIX = was


def write_site(root, out, audience, link_root, today, record, wiki, sitemap=False, pdf_links=None):
    """Everything a build does, once the kind of link it emits has been settled."""
    site, budget, sections = read_config(wiki)
    pages = read_pages(wiki / "pages", budget["intent"])
    template = (ASSETS / "template.html").read_text(encoding="utf-8")
    # The stylesheet and the script are addressed with a short digest of their own contents, so changing
    # either changes its address. Without this a browser goes on using the copy it already holds and the
    # change simply does not appear -- which reads as the change being broken rather than unfetched, and
    # no header can evict what a tab has already cached.
    stamps = {name: "?v=" + hashlib.sha256((ASSETS / name).read_bytes()).hexdigest()[:8]
              for name in ("wiki.css", "wiki.js")}
    images_dir = wiki / "images"
    ledger = read_ledger(images_dir)
    shown = set()
    files_dir = wiki / FILES
    # A folder that is itself a link resolves, with every file in it, to wherever it points, so the test that keeps
    # a PDF inside the folder would pass anything there.
    if files_dir.is_symlink():
        raise WikiError(f"the wiki's {FILES} folder is a symbolic link, so a build would publish whatever it points "
                        f"at; make {FILES} a folder of its own inside the wiki, and put the PDFs in it")
    pdfs = set()
    site_root = (link_root or out)
    today = today or datetime.date.today().isoformat()
    dates = read_dates(wiki)

    if GOALS_ID not in pages:
        raise WikiError(f"there is no {GOALS_ID}.md; the collected goals need a page to be collected onto")
    goals_html, goals_words = goals_page(pages, sections, audience)
    pages[GOALS_ID]["words"] += goals_words

    # Reachable means listed in the navigation, or beneath something that is.
    listed = {page_id for section in sections for page_id in section.get("pages", [])}
    in_nav = {reachable
              for top in listed
              for reachable in descendants_of(top, set(pages))}
    for page_id in sorted(pages):
        if page_id not in in_nav:
            raise WikiError(f"{page_id}.md is in no navigation section and beneath no page that is, "
                            "so no reader could reach it")
    # A category needs no navigation entry: every page carrying one links to it from its own foot, which
    # is the only direction anyone travels. Listing one in wiki.toml still works, and still has to name a
    # category some page belongs to.
    categories = collect_categories(pages, audience)

    markdown = make_markdown()
    emitted = [page_id for page_id in sorted(pages)
               if visible_to(audience, pages[page_id]["audience"])]

    index_entries = []
    linked = [page_id for page_id in emitted if pages[page_id]["status"] == "approved"]
    for page_id in linked:
        # A child page's title names only what sets it apart within its parent, so a result says where the
        # page sits.
        index_entries.append({"u": page_directory(page_id), "t": pages[page_id]["title"],
                              "s": pages[page_id]["subtitle"],
                              "p": " › ".join(pages[ancestor]["title"]
                                              for ancestor in ancestors_of(page_id, pages, audience))})
    for slug in sorted(categories):
        index_entries.append({"u": category_directory(slug),
                              "t": "Category: " + categories[slug]["name"], "s": "a category page", "p": ""})

    def index_for(directory):
        """The search index as this page must address it: every other page relative to this one.

        The entries are collected site-relative, which is the only sane way to collect them and the wrong
        thing to put in a page: a browser resolves "b/" against the directory it is already in, so one
        shared index sends every result clicked on /a/ to /a/b/, and every one of them is a miss.
        """
        return script_json([{"u": relative_directory(directory, entry["u"]), "t": entry["t"],
                             "s": entry["s"], "p": entry["p"]} for entry in index_entries])

    changed = []
    for page_id in sorted(pages):
        digest = page_digest(pages, page_id, sections)
        if dates.get(page_id, {}).get("digest") != digest:
            changed.append(page_id)
            # Updated, not replaced: the day the page was last audited stays true after an edit.
            dates.setdefault(page_id, {}).update(updated=today, digest=digest)
    for gone in sorted(set(dates) - set(pages)):
        del dates[gone]
        changed.append(gone)
    if changed and record:
        write_dates(wiki, dates)

    counts = {}
    written = []

    def emit(directory, markup, name="index.html"):
        destination = out / directory / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        # A page whose bytes have not moved is left alone, so what a build touched is what a build
        # actually changed.
        if not destination.is_file() or destination.read_text(encoding="utf-8") != markup:
            destination.write_text(markup, encoding="utf-8", newline="\n")
        written.append(destination)

    # The stylesheet goes in before any page: it is how a later build knows this folder for its own, so a
    # build that stops partway leaves a folder the next build still accepts.
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("wiki.css", "wiki.js"):
        written.append(copy_if_changed(ASSETS / name, assets / name))

    # Counted from the pages as written, once, for every footer.
    citations = citation_counts(root, wiki)
    diagrams_used = False
    for page_id in emitted:
        page = pages[page_id]
        directory = page_directory(page_id)
        # Tables the build writes from other pages: a family's member table where its parent marks it, and the
        # health table on the health page, which a user build leaves out.
        family_table = (family_table_rows(page_id, pages, emitted, audience)
                        if FAMILY_TABLE in page["body"] else None)
        index_table = (index_table_rows(page_id, pages, emitted, audience)
                       if INDEX_TABLE in page["body"] else None)
        health = (health_rows(pages, emitted, dates, citations)
                  if page_id == HEALTH_ID and audience != "user" else None)
        markdown.renderer.cited = {}
        body = markdown(page["body"])
        if page_id == GOALS_ID:
            body += goals_html
            page["raw"] += ("\n<!-- Every intent below this page's own text is collected from the other\n"
                            "     pages when the wiki is built, and is not written here. -->\n")
        body = LONE_FIGURE.sub(r"\1", body)
        # Every address the page shows, in its prose and in its references alike, is a link a reader can
        # follow. Before the rewrites below, so a diagram's source and a code sample are still inside the
        # <pre> that keeps them out of it.
        body = autolink_addresses(body)
        # A mermaid block is a diagram, not a sample: Mermaid draws what it finds in a pre.mermaid, and only
        # a page carrying one loads the script.
        body, diagrams = MERMAID_BLOCK.subn(r'<pre class="mermaid">\1</pre>', body)
        diagrams_used = diagrams_used or bool(diagrams)
        # Mermaid is several megabytes, so a page only names it: the page's own script fetches it once a
        # diagram nears the screen, and nothing else on the page waits for it.
        diagram_script = ('<script>const WIKI_MERMAID=%s;</script>'
                          % script_json(relative_file(directory, "assets/" + MERMAID)) if diagrams else "")
        # A page's own table takes the wiki's table style, and scrolls inside its wrapper on a narrow
        # screen rather than widening the page.
        body = body.replace("<table>", '<div class="wt"><table class="w">').replace("</table>",
                                                                                    "</table></div>")
        # A code block gets the source view's box and copy button, which the page's script already works.
        # Only a bare <pre> is markdown's; the source view's own is built elsewhere, with a class.
        # Each bare block is wrapped with its own closing tag. Closing after every </pre> once put a stray
        # </div> after a diagram, which ended the article there and dropped the rest of the page out of it.
        body = BARE_PRE.sub(r'<div class="srcbox"><button class="copy" type="button">Copy</button>\1</div>',
                            body)
        # Outside code only: a sample that shows the mark shows it as written.
        body = "".join(part if CODE_HTML.fullmatch(part) else MISSING.sub(MISSING_CITATION, part)
                       for part in CODE_HTML.split(body))
        # References are taken out first, so a picture shown only in one never reaches a user build.
        if audience == "user":
            body = for_user(body)
        body = rewrite_references(body, directory, site_root, root, ledger, set(pages),
                                  wiki / "pages", page["path"], shown, files_dir, pdfs,
                                  [] if pdf_links is None else pdf_links)
        # A PDF's size follows its link, so a reader knows what a click will fetch.
        body = PDF_ANCHOR.sub(r'\1\3 <span class="pdfsize">(PDF, \2)</span>', body)
        if page["meta"].get("image"):
            shown.add(page["meta"]["image"])
        # Written in after the references are pointed, because their links already resolve from this page.
        if family_table:
            body = body.replace("<p>%s</p>" % FAMILY_TABLE, family_table_html(pages, family_table, directory))
        if index_table:
            body = body.replace("<p>%s</p>" % INDEX_TABLE, index_table_html(pages, index_table, directory))
        if health is not None:
            body += health_html(pages, health, directory)
        # The source view names paths and internal identifiers by its nature, so it is internal only.
        with_source = audience != "user"
        # The markdown copy is the page as written, references and marks included, so it goes where the
        # source view goes and nowhere else.
        llm_links = ""
        if with_source:
            extra = (goals_markdown(pages, goals_order(pages, sections, audience), directory) if page_id == GOALS_ID
                     else health_markdown(pages, health, directory) if health is not None else "")
            copy = markdown_copy(page, directory, set(emitted), wiki / "pages", ledger, files_dir, pdfs, extra)
            if family_table:
                copy = outside_code(copy, lambda text: FAMILY_TABLE_LINE.sub(
                    lambda _: family_table_markdown(pages, family_table, directory), text))
            if index_table:
                copy = outside_code(copy, lambda text: INDEX_TABLE_LINE.sub(
                    lambda _: index_table_markdown(pages, index_table, directory), text))
            emit(directory, copy, AGENT_COPY)
            llm_links = ('<link rel="alternate" type="text/markdown" href="%s">\n<link rel="describedby" '
                         'href="%s">' % (AGENT_COPY, posixpath.relpath("/" + AGENT_INDEX,
                                                                        "/" + (directory or "."))))
        emit(directory, render_page(
            page["title"], page["subtitle"], page["hatnote"], body,
            render_infobox(page, audience, directory, ledger, markdown.renderer.cited),
            render_categories(page, directory, categories),
            render_nav(sections, pages, categories, page_id, directory, audience),
            index_for(directory), site, directory, template,
            on_article() if with_source else ARTICLE_ONLY, dates[page_id]["updated"],
            stamps["wiki.css"], stamps["wiki.js"], page["status"] != "approved", llm_links, diagram_script,
            # A reader-facing build carries no references and no marks, so it counts neither; nor does a page
            # excused from citations, which has nothing to count.
            page_stats(page["words"], *(citations.get(page_id, (0, 0))
                                        if with_source and page["meta"].get("goals", True)
                                        else (None, None))),
            # An audit checks a page's citations against the code. A user build withholds them, and a page
            # excused from citations has none, so neither carries an audit.
            audited=(dates[page_id].get("audited", "") if with_source and page["meta"].get("goals", True)
                     else None),
            crumbs=render_crumbs(page_id, pages, directory, audience),
            nav_here=current_section(sections, page_id)))
        if with_source:
            source_directory = directory + "source/"
            emit(source_directory, render_page(
                page["title"], "markdown source of this page", "",
                render_source(page["raw"], "../" + AGENT_COPY), "", "",
                render_nav(sections, pages, categories, page_id, source_directory, audience),
                index_for(source_directory), site, source_directory, template, on_source(),
                dates[page_id]["updated"], stamps["wiki.css"], stamps["wiki.js"],
                nav_here=current_section(sections, page_id)))
        counts[page_id] = page["words"]

    for slug in sorted(categories):
        directory = category_directory(slug)
        listed = categories[slug]
        rows = "".join(
            '<a href="%s"><b>%s</b><span>%s</span></a>'
            % (relative_directory(directory, page_directory(page_id)),
               html_module.escape(pages[page_id]["title"]),
               html_module.escape(pages[page_id]["subtitle"]))
            for page_id in listed["pages"])
        body = "<p>%d page%s in this category.</p><div class=\"gal\">%s</div>" % (
            len(listed["pages"]), "" if len(listed["pages"]) == 1 else "s", rows)
        emit(directory, render_page(
            "Category: " + listed["name"], "a category page", "", body, "", "",
            render_nav(sections, pages, categories, slug, directory, audience),
            index_for(directory), site, directory, template, ARTICLE_ONLY, "",
            stamps["wiki.css"], stamps["wiki.js"], nav_here=current_section(sections, slug)))

    if audience != "user":
        order = agent_order(sections, pages, emitted)
        emit("", agent_index(site, order, pages), AGENT_INDEX)

    # Only a build meant for a host lists its addresses, and only once the wiki says where it is hosted.
    if sitemap and site.get("url"):
        entries = [(page_directory(page_id), dates[page_id]["updated"]) for page_id in linked]
        entries += [(category_directory(slug), "") for slug in sorted(categories)]
        emit("", sitemap_xml(site["url"], entries), SITEMAP)

    # Only a wiki that draws a diagram carries the script, and its licence beside it.
    if diagrams_used:
        for name in (MERMAID, MERMAID_LICENSE):
            written.append(copy_if_changed(ASSETS / name, assets / name))
    # Every recorded picture must exist, but only those a written page shows are copied: a picture on an
    # internal page stays out of a user build.
    for name in sorted(ledger):
        if not (images_dir / name).is_file():
            raise WikiError(f"{LEDGER} lists {name}, which is not in {images_dir}")
        # A symbolic link is copied as the file it points at, so one leading out of the folder would publish it.
        if not (images_dir / name).resolve().is_relative_to(images_dir.resolve()):
            raise WikiError(f"{LEDGER} lists {name}, which links to a file outside the images folder; put the "
                            f"picture itself in {images_dir}")
    if shown:
        (out / "images").mkdir(parents=True, exist_ok=True)
        for name in sorted(shown):
            written.append(copy_if_changed(images_dir / name, out / "images" / name))
    # Only the PDFs a written page links are copied, each one already found to be a file of the folder's own.
    if pdfs:
        (out / FILES).mkdir(parents=True, exist_ok=True)
        for name in sorted(pdfs):
            written.append(copy_if_changed(files_dir / name, out / FILES / name))

    # Whatever the site no longer makes goes, so a page that was deleted leaves nothing behind.
    clear_stale(out, written)
    return counts, goals_words, budget, sorted(
        page_id for page_id in pages if pages[page_id]["status"] != "approved")


# The files a build wrote, listed inside the site, one path to a line.
BUILD_RECORD = ".wiki-build"


def clear_stale(out, written):
    """Delete each file an earlier build wrote and this one did not, then record what this one wrote.

    A site folder can hold files a person put there for its host, such as a CNAME naming the domain, and
    those are not the build's to delete. A site written before builds kept a record has none, so there the
    build takes only the kinds of file it makes.
    """
    record = out / BUILD_RECORD
    made = sorted({path.relative_to(out).as_posix() for path in written})
    if record.is_file():
        earlier = record.read_text(encoding="utf-8").splitlines()
    else:
        earlier = [path.relative_to(out).as_posix() for path in sorted(out.rglob("*"))
                   if path.is_file() and (path.name in ("index.html", AGENT_COPY, AGENT_INDEX)
                                          or path.relative_to(out).parts[0] in ("assets", "images", FILES))]
    inside = out.resolve()
    for name in sorted(set(earlier) - set(made) - {""}, reverse=True):
        path = out / name
        # The record is text in a folder anyone can edit, so a name leading out of the site is not removed.
        if not path.is_file() or not path.resolve().is_relative_to(inside):
            continue
        path.unlink()
        parent = path.parent
        # A linked folder is left in place: it is a link someone made, not a folder a build emptied.
        while parent.resolve() != inside and not parent.is_symlink() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    listed = "".join(name + "\n" for name in made)
    # Left alone when it lists the same files, so a build that changed nothing touches nothing.
    if not record.is_file() or record.read_text(encoding="utf-8") != listed:
        record.write_text(listed, encoding="utf-8", newline="\n")


def copy_if_changed(source, destination):
    """Copy only when the bytes differ, so an unchanged file keeps its timestamp."""
    if not destination.is_file() or destination.read_bytes() != source.read_bytes():
        shutil.copyfile(source, destination)
    return destination


# --------------------------------------------------------------------------------------------------
# checking


def tree_digest(directory):
    """Every file under a directory, by relative path. Two builds of one wiki must agree exactly: a
    timestamp, an absolute path or an unsorted walk that crept in would show here and nowhere else."""
    digests = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            digests[str(path.relative_to(directory))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def subject_digest(root, depicts):
    """What the things a picture shows hash to now.

    A `depicts` entry is a path in the project -- a file, or a directory taken whole. Nothing about its
    contents is assumed: the digest is over the bytes, so any project can say what a picture shows
    without first adopting a convention for describing its own assets.
    """
    digest = hashlib.sha256()
    for name in sorted(depicts):
        subject = root / name
        if not subject.exists():
            raise WikiError(f"a picture says it shows {name}, which is not in this project")
        files = sorted(subject.rglob("*")) if subject.is_dir() else [subject]
        seen = False
        for path in files:
            if not path.is_file():
                continue
            seen = True
            digest.update(str(path.relative_to(root)).encode("utf-8"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        if not seen:
            raise WikiError(f"a picture says it shows {name}, which holds no files")
    return "sha256:" + digest.hexdigest()


def picture_problems(root, wiki=None):
    """Every picture whose subject has moved since the picture was made."""
    images_dir = wiki_of(root, wiki) / "images"
    ledger = read_ledger(images_dir)
    problems = []
    for name in sorted(ledger):
        entry = ledger[name]
        depicts = entry.get("depicts", [])
        if not depicts:
            continue
        current = subject_digest(root, depicts)
        if entry.get("digest") and entry["digest"] != current:
            problems.append(
                f"{name} shows {', '.join(sorted(depicts))}, which has changed since the picture was made; "
                f"re-render it, or `wiki bless {name} \"<why the picture is still true>\"`")
    return problems


# A link to a document, inside a footnote's reference. The address has to end in `.md` -- at its end, or
# where a fragment or a query starts -- and not merely hold those characters somewhere: matched loosely,
# the rule refused `https://www.mdpi.com/...` for the `.md` inside its host, so a wiki citing a paper
# published there had no way to link it. The PDF rule below has always anchored this way.
DOCUMENT_LINK = re.compile(r"\]\(([^)\s]*\.md(?=[#?)]|$)[^)]*)\)")
# A link to a PDF the wiki keeps, inside a footnote's reference: a document too, however it is published. An
# outside service's own PDF, linked by its full address, is that service's documentation.
PDF_DOCUMENT_LINK = re.compile(r"\]\((?![a-z][a-z0-9+.-]*:|//)([^)\s]*\.pdf(?:#[^)\s]*)?)\)", re.I)


def citation_problems(root, wiki=None):
    """Every reference that cites a document instead of the code.

    A reference exists to answer "where does this actually happen", and a page of prose is not an answer:
    it is another claim, written by someone else, that can be wrong in the same way. Following a citation
    should land in the thing that runs.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for note in FOOTNOTE.finditer(text):
            links = list(DOCUMENT_LINK.finditer(note.group(1))) + list(PDF_DOCUMENT_LINK.finditer(note.group(1)))
            for link in sorted(links, key=lambda found: found.start()):
                problems.append(
                    f"{path.relative_to(pages_dir)} cites {link.group(1)}, which is a document; "
                    "a reference names the code that does the thing, or an outside service's own documentation")
    return problems


HEADING_LINE = re.compile(r"^#{2,6}\s+(.+?)\s*$", re.M)
# A fenced code sample. It is the thing itself, shown rather than described, so neither its blank lines
# nor its lines that start with # are prose -- and a reference page is mostly samples.
FENCED = re.compile(r"^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", re.M | re.S)
# A heading that opens with one of these is a question, and a question is the writer thinking aloud about
# what to put in the section. Name the thing instead.
QUESTION_WORD = re.compile(r"^(how|what|where|why|when|which|who|whether)\b", re.I)
# Editorialising: a heading that rates its own contents rather than naming them.
EDITORIAL = re.compile(r"\b(matters?|important|interesting|note|overview|misc|details?)\b", re.I)
# A name that opens with one of these points at the page it sits on instead of naming anything: "This site"
# reads as nothing in a contents box, a search result, or a page quoted somewhere else. Name it: Domain.
DEMONSTRATIVE = re.compile(r"^(this|that|these|those|our|here)\b", re.I)
# Prose that points at the project instead of naming it. A published page is read by people who did not
# arrive from the project, and to them "this repository" is no repository at all.
POINTING = re.compile(r"\b(?:this|these|our)\s+(?:repository|repositories|repo|project|site|website|wiki|"
                      r"tool|package|codebase)\b", re.I)


# What says where a statement came from: a citation, or the mark that says there is none.
CLAIM = re.compile(r"\[\^[^\]]+\]|\{missing\}")
# Any heading line. Removed before a page is read as statements, so prose written directly beneath one is
# read like any other.
HEADING_ANY = re.compile(r"^#{1,6}[ \t].*$", re.M)
# The start of a list item inside a block, so each item is read on its own.
LIST_ITEM = re.compile(r"\n(?=[ \t]*(?:[-*+]|\d+\.)[ \t])")
# The line under a table's header: pipes, dashes, colons and spaces only.
TABLE_SEPARATOR = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*$")
# The end of a sentence: a full stop, question or exclamation mark, any closing quote, bracket or emphasis,
# and the citations or mark that belong to the sentence -- then a space and what starts the next one: a
# capital, a digit, code, emphasis or an opening bracket. A version number or an abbreviation has no space
# and capital after its full stop, so neither ends one.
BOUNDARY = re.compile(r"([.!?][\"”’')\]*_]*(?:\[\^[^\]]+\]|\s*\{missing\})*)\s+(?=[A-Z0-9`*_\[\"“(])")
# Inline code. Its punctuation is part of a name, never the end of a sentence.
INLINE_CODE = re.compile(r"`[^`\n]*`")
# One block of prose: a run of lines with no blank line inside it.
BLOCK = re.compile(r"^(?![ \t]*$).+(?:\n(?![ \t]*$).*)*", re.M)
# A link to another page. The page it points at carries the citations.
PAGE_LINK = re.compile(r"\]\([^)\s]*\.md(?:#[^)\s]*)?\)")
# A statement that is nothing but links, as under External links: it names somewhere to read and states
# nothing that could be cited. A reference-style link counts, because "[Name][ref]" points where
# "[Name](url)" points, and several may sit on one line. Only punctuation may stand between them: a word
# between two links, "and" included, makes the line prose, and prose is a claim.
LINK = r"\[[^\]]+\](?:\([^)\s]+\)|\[[^\]]*\])"
LINK_ONLY = re.compile(r"^\s*(?:(?:[-*+]|\d+\.)\s+)?%s(?:\s*[;,·/|]\s*%s)*\s*[.;]?\s*$" % (LINK, LINK))
# A statement that is only a bold label -- "**Inference.**", "- **Note.**" -- which names what follows
# instead of stating it, so there is nothing to cite. BOUNDARY ends a sentence at the full stop inside the
# bold, cutting the label off the sentence it introduces; that sentence still answers for its own
# citation. Held to four words and no verb, because a claim set in bold is still a claim.
BOLD_LABEL = re.compile(r"^\s*(?:(?:[-*+]|\d+\.)\s+)?(\*\*|__)\s*(?P<label>[^*_]+?)\s*\1\s*$")
LABEL_VERB = re.compile(r"\b(is|are|was|were|be|has|have|had|can|could|will|would|must|may|might|shall"
                        r"|does|do|did|says|say|holds|hold|needs|need|takes|take|gets|get|makes|make"
                        r"|goes|go|runs|run|comes|come|gives|give|keeps|keep|leaves|leave)\b", re.I)


def bold_label(statement):
    """Whether a statement is a bold label rather than a claim set in bold."""
    found = BOLD_LABEL.match(statement)
    if not found:
        return False
    label = found.group("label").rstrip(".:;,")
    return bool(label) and len(label.split()) <= 4 and not LABEL_VERB.search(label)
# The pipes that divide one row into cells: every one the writer did not escape. Backticks are not
# honoured, because the renderer does not honour them either -- a cell holding `a|b` is two cells to it,
# and a check that read it as one would pass a table the renderer throws away.
CELL_EDGE = re.compile(r"(?<!\\)\|")
# The body rows of a rendered table, which is what a row in the markdown was meant to become.
RENDERED_BODY = re.compile(r"<tbody>(.*?)</tbody>", re.S)


def statements(block):
    """The statements in one block of prose: each sentence of each list item, or each row of a table.

    A table's rows are read one at a time, and its header is not read at all: a header names the columns
    and states nothing. A table row needs at least one citation in any of its columns -- a table held as a
    whole let one cited row carry every row beside it.
    """
    if block.startswith("|"):
        rows = block.split("\n")
        if len(rows) > 1 and TABLE_SEPARATOR.match(rows[1]):
            rows = rows[2:]
        return [row.strip() for row in rows if row.strip()]
    found = []
    for item in LIST_ITEM.split(block):
        text = " ".join(item.split())
        # Boundaries are found with code's punctuation blanked out, then cut from the text as written. The
        # blanking keeps every character where it was, so the positions agree.
        masked = INLINE_CODE.sub(lambda code: re.sub(r"[.!?]", " ", code.group(0)), text)
        start = 0
        for boundary in BOUNDARY.finditer(masked):
            found.append(text[start:boundary.end(1)])
            start = boundary.end()
        found.append(text[start:])
    return found


def page_statements(path):
    """Every statement on one page, with the line of the file it starts on.

    Footnote definitions, fenced code and headings are blanked rather than removed, so every line keeps its
    number and a statement is reported where a person or an agent will find it.
    """
    text = path.read_text(encoding="utf-8")
    _, body = read_front_matter(path)
    first = text[:len(text) - len(body)].count("\n") + 1

    def blank(match):
        return "\n" * match.group(0).count("\n")

    # The family table marker is where the build writes a table, not a sentence.
    body = INDEX_TABLE_LINE.sub("", FAMILY_TABLE_LINE.sub("", HEADING_ANY.sub("", LINK_DEFINITION.sub(
        "", FENCED.sub(blank, FOOTNOTE.sub(blank, body))))))
    for block in BLOCK.finditer(body):
        start = first + body[:block.start()].count("\n")
        chunk = block.group(0)
        if chunk.lstrip().startswith("!["):
            continue
        for statement in statements(chunk.strip()):
            words = statement.split()[:6]
            found = re.search(r"\s+".join(map(re.escape, words)), chunk) if words else None
            yield (start + chunk[:found.start()].count("\n") if found else start), statement


def quoted(statement, limit=80):
    """A statement as a report quotes it: whole when short, cut at a word with an ellipsis when not."""
    text = " ".join(statement.split())
    if len(text) <= limit:
        return "“%s”" % text
    return "“%s…”" % (text[:limit].rsplit(" ", 1)[0] if " " in text[:limit] else text[:limit])


def table_cells(row):
    """The cells of one markdown table row, counted the way the renderer counts them."""
    parts = CELL_EDGE.split(row.strip())
    # A row written with the outer pipes has an empty field at each end, which is a border and not a cell.
    if parts and not parts[0].strip():
        parts = parts[1:]
    if parts and not parts[-1].strip():
        parts = parts[:-1]
    return parts


def source_tables(path):
    """Each table in a page's markdown: the line its header is on, its header, and its body rows.

    Read from the markdown rather than the built page, because what this is for is the difference between
    the two. Fenced code and footnote definitions are blanked rather than removed, so every line keeps
    its number.
    """
    text = path.read_text(encoding="utf-8")
    _, body = read_front_matter(path)
    first = text[:len(text) - len(body)].count("\n") + 1

    def blank(match):
        return "\n" * match.group(0).count("\n")

    lines = FENCED.sub(blank, FOOTNOTE.sub(blank, body)).split("\n")
    found, index = [], 0
    while index < len(lines) - 1:
        header, after = lines[index], lines[index + 1]
        if "|" in header and header.strip() and TABLE_SEPARATOR.match(after):
            rows, cursor = [], index + 2
            while cursor < len(lines) and lines[cursor].strip() and "|" in lines[cursor]:
                rows.append((first + cursor, lines[cursor]))
                cursor += 1
            found.append((first + index, header, rows))
            index = cursor
            continue
        index += 1
    return found


def table_problems(root, wiki=None):
    """Tables the renderer will not draw as tables, which the other checks cannot see.

    A row that does not divide into the same cells as its header stops the whole block being a table, and
    a row carrying anything after its last pipe falls out of one -- in both cases the markdown is served
    as a paragraph of raw pipes. Nothing else notices: every check that reads a table reads the markdown,
    where the rows are still rows, so a mangled table cites its sources correctly and passes. A reader
    gets the pipes.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    markdown = make_markdown()
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        name = path.relative_to(pages_dir)
        _, body = read_front_matter(path)
        tables = source_tables(path)
        named = len(problems)
        for line, header, rows in tables:
            width = len(table_cells(header))
            for row_line, row in rows:
                if row.strip().startswith("|") and not row.strip().endswith("|"):
                    problems.append(
                        "%s:%d: the table row %s carries text after its last |, so the renderer drops it "
                        "out of the table and serves the table as a paragraph of pipes; move what follows "
                        "the last | into a cell" % (name, row_line, quoted(row)))
                elif len(table_cells(row)) != width:
                    cells = len(table_cells(row))
                    problems.append(
                        "%s:%d: the table row %s has %d cell%s where its header has %d, so the renderer "
                        "refuses the whole table and serves it as a paragraph of pipes; give the row %d "
                        "cell%s, one for each column"
                        % (name, row_line, quoted(row), cells, "" if cells == 1 else "s", width,
                           width, "" if width == 1 else "s"))
        # The backstop: a table that did not render for a reason no row above names. The page's own
        # markdown is rendered here, so the tables the build writes itself are not in what is counted.
        if tables and len(problems) == named:
            drawn = markdown(FOOTNOTE.sub("", body))
            rows_drawn = sum(part.count("<tr>") for part in RENDERED_BODY.findall(drawn))
            rows_written = sum(len(rows) for _, _, rows in tables)
            if rows_drawn < rows_written:
                problems.append(
                    "%s:%d: the table starting here is served as a paragraph of pipes rather than a "
                    "table; give it a header row, a |---| line with one column for each cell, and one "
                    "row for each line" % (name, tables[0][0]))
    return problems


def uncited_problems(root, wiki=None):
    """Sentences that state something and say nothing about where they came from.

    A reader uses this instead of reading the source, so a sentence they cannot trace is one they have to
    take on faith. Every sentence carries a reference, or the mark that says there is none -- and the
    second is a fine answer. What is not a fine answer is silence, because silence looks exactly like a
    cited claim to someone scanning the page. A sentence never borrows its neighbour's citation: one
    citation used to cover a whole paragraph, and a claim beside a cited one read as though it were checked.

    A sentence that links to another page is excused, because that page carries the citations. A table row
    is held to the rule the way a sentence is: a citation or the mark in any one of its cells.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        meta, body = read_front_matter(path)
        # A page about the wiki itself -- the front page, the one that collects the goals, the one
        # explaining how this is kept true -- describes no behaviour, so it has nothing to cite and never
        # will. `goals = false` already marks exactly those pages.
        if not meta.get("goals", True):
            continue
        for line, statement in page_statements(path):
            if not re.search(r"[A-Za-z]", statement):
                continue
            if (CLAIM.search(INLINE_CODE.sub("", statement)) or PAGE_LINK.search(statement)
                    or LINK_ONLY.match(statement) or bold_label(statement)):
                continue
            if statement.startswith("|"):
                problems.append("%s:%d: the table row %s cites nothing; give one of its cells a reference, "
                                "or {missing} if there is none"
                                % (path.relative_to(pages_dir), line, quoted(statement)))
                continue
            problems.append("%s:%d: %s states something and cites nothing; give it a reference, or "
                            "{missing} if there is none"
                            % (path.relative_to(pages_dir), line, quoted(statement)))
    return problems


def missing_marks(root, wiki=None):
    """Every claim marked as having no source, and the line it is on.

    The count on every build says how much of the wiki is taken on faith; this says where. `wiki check`
    prints it without failing, because the mark is an answer and the list is the work that remains.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    marks = []
    for path in sorted(pages_dir.rglob("*.md")):
        name = path.relative_to(pages_dir)
        text = path.read_text(encoding="utf-8")
        meta, _ = read_front_matter(path)
        found = [(line, "%s:%d: %s is marked as having no source" % (name, line, quoted(statement)))
                 for line, statement in page_statements(path)
                 if MISSING.search(INLINE_CODE.sub("", statement))]
        for group in meta.get("infobox", []):
            for row in group.get("rows", []):
                if row.get("missing"):
                    label = str(row.get("label", ""))
                    line = text[:max(text.find('label = "%s"' % label), 0)].count("\n") + 1
                    found.append((line, "%s:%d: the infobox row %r is marked as having no source"
                                  % (name, line, label)))
        marks += [message for _, message in sorted(found)]
    return marks


# A footnote cited in the prose, and one defined at the foot.
CITED = re.compile(r"\[\^([^\]]+)\](?!:)")
DEFINED = re.compile(r"^\[\^([^\]]+)\]:", re.M)


def infobox_problems(root, wiki=None):
    """Infobox rows that state something and cite nothing.

    A row is a claim in the most visible place on the page, so it carries a citation the way a sentence
    does. It names a footnote the page's prose also cites -- which keeps every row repeating something the
    page says, and gives it a number a reader can follow -- or it says there is none with `missing = true`.
    A page about the wiki itself states no behaviour, and is excused as it is from the prose rule.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        meta, body = read_front_matter(path)
        if not meta.get("goals", True):
            continue
        defined = {unikey(key) for key in DEFINED.findall(body)}
        prose = FENCED.sub("", FOOTNOTE.sub("", body))
        cited = {unikey(key) for key in CITED.findall(prose)} & defined
        name = path.relative_to(pages_dir)
        for group in meta.get("infobox", []):
            for row in group.get("rows", []):
                if row.get("missing"):
                    continue
                label = row.get("label", "")
                keys = row_cites(row)
                if not keys:
                    problems.append(f"{name}: the infobox row {label!r} states something and cites nothing; "
                                    "give it cite = \"<footnote>\" naming a reference the page's text cites, "
                                    "or missing = true if there is none")
                for key in keys:
                    if unikey(key) not in cited:
                        problems.append(f"{name}: the infobox row {label!r} cites [^{key}], "
                                        "which no sentence on the page cites; cite it where the page "
                                        "states the same fact")
    return problems


def heading_problems(root, wiki=None):
    """Headings that name nothing.

    A reader scans headings to find the one that holds their answer, so a heading is a label on a drawer:
    Water, Predators, Hunting. "Where they go" is the writer wondering what belongs in the section, and
    "Fast enough to matter" is the writer rating it. Neither tells a reader whether to stop scanning.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        meta, body = read_front_matter(path)
        # A subtitle is held to the same question words: "what a person writes" names nothing a reader
        # choosing between pages can tell apart either.
        subtitle = str(meta.get("subtitle", "")).strip()
        if QUESTION_WORD.match(subtitle):
            problems.append(f"{path.relative_to(pages_dir)}: the subtitle {subtitle!r} asks a question; "
                            "name the things the page covers")
        for heading in HEADING_LINE.finditer(FENCED.sub("", body)):
            title = heading.group(1)
            if QUESTION_WORD.match(title):
                problems.append(f"{path.relative_to(pages_dir)}: the heading {title!r} asks a question; "
                                "name the thing the section is about")
            elif EDITORIAL.search(title):
                problems.append(f"{path.relative_to(pages_dir)}: the heading {title!r} rates its own "
                                "contents; name them instead")
            elif DEMONSTRATIVE.match(title):
                problems.append(f"{path.relative_to(pages_dir)}: the heading {title!r} points at the page "
                                "instead of naming anything; name the thing the section is about")
    return problems


# Every front-matter field a reader reads as words.
WORDED_FIELDS = ("title", "subtitle", "intent", "infobox group", "infobox label", "infobox value",
                 "infobox note")


def wording_places(path, pages_dir, front_matter_fields=WORDED_FIELDS):
    """Each field and sentence of a page, named the way a problem names it, with its code removed.

    Every check that refuses a word reads a page through this, so each names a place the same way, and none
    reads a code sample, which shows text as written. `front_matter_fields` narrows the front matter only:
    **the body is always read**, because a word refused in a subtitle is refused in a sentence too, and a
    caller that passed a short list to mean "just these" read every sentence anyway.
    """
    meta, _ = read_front_matter(path)
    name = path.relative_to(pages_dir)
    found = [("title", meta.get("title", "")), ("subtitle", meta.get("subtitle", "")),
             ("intent", meta.get("intent", ""))]
    for group in meta.get("infobox", []):
        found.append(("infobox group", group.get("group", "")))
        for row in group.get("rows", []):
            found += [("infobox label", row.get("label", "")), ("infobox value", row.get("value", "")),
                      ("infobox note", row.get("note", ""))]
    places = [(f"{name}: the {field}", INLINE_CODE.sub("", str(text)))
              for field, text in found if field in front_matter_fields]
    places += [(f"{name}:{line}: {quoted(statement)}", INLINE_CODE.sub("", statement))
               for line, statement in page_statements(path)]
    return places


# A rule told as something somebody said: a dated quote such as "The owner, 2026-09-14", or "the owner said".
# A reader wants the rule; a page that quotes the request for it dates itself and argues instead of describing.
ATTRIBUTION = re.compile(r"\bthe owner(?:'s ruling)?,?\s+\d{4}-\d{2}-\d{2}|\bthe owner (?:said|says|asked|wrote|ruled)\b",
                         re.I)


def attribution_problems(root, wiki=None):
    """Pages that attribute a rule to a person instead of stating it.

    Where a requirement came from is recorded with the work that implements it, never on the page. Code is
    left alone, because a sample shows text as written.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        # The title and the infobox are left out of the front matter read here; every sentence of the
        # body is read whatever is named, which is what the check wants.
        for place, text in wording_places(path, pages_dir, ("subtitle", "intent")):
            if ATTRIBUTION.search(text):
                problems.append(f"{place} attributes a rule to a person; state the rule itself")
    return problems


# A vague actor: a sentence saying that an unnamed person did, did not, or may do something. It hides the one fact
# a reader needs -- who -- so a page names the reader, the writer, an agent, or the part of the system that acts.
VAGUE_ACTOR = re.compile(r"\b(nobody|somebody|someone|anyone|anybody|everyone|everybody|no[ -]one)\b", re.I)


def vague_actor_problems(root, wiki=None):
    """Titles, labels and sentences that say an unnamed person acts instead of naming who.

    Code is left alone, because a sample shows text as written.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        for place, text in wording_places(path, pages_dir):
            found = VAGUE_ACTOR.search(text)
            if found:
                problems.append(f"{place} says {found.group(0).lower()!r} instead of naming who acts; name the "
                                "reader, the writer, an agent or the part that acts")
    return problems


# Words that carry no fact a reader can check, each with what it does to a sentence and what to write
# instead. Only words with no plain use in a description are listed: "may" grants permission as often as it
# hedges, "just" also means a moment ago, and "some", "new" and "will" state facts, so a word list cannot
# tell their uses apart and they are left to the writer.
EMPTY_WORDS = (
    (re.compile(r"\b(powerful|seamless(?:ly)?|robust|cutting-edge|best-in-class)\b", re.I),
     "which sells instead of describing", "say what it does"),
    (re.compile(r"\b(simply|easily|obviously|of course|clearly)\b", re.I),
     "which makes light of what it describes", "delete the word"),
    (re.compile(r"\b(appears? to|seems? to|typically|usually|generally|probably|likely|in some cases|"
                r"tends? to)\b", re.I),
     "which hedges", "say what happens, or mark the claim {missing}"),
    # "note" is also a noun ("each note that is archived"), so the frame is refused only where it opens a
    # sentence or clause, or follows a word that makes it an instruction.
    (re.compile(r"\b((?:please|also|to|should|must)\s+note that|(?<![\w'’]\s)note that|it is worth noting|"
                r"please be aware|in order to)\b", re.I),
     "which frames the fact instead of stating it", "keep the fact and drop the frame"),
    (re.compile(r"\b(etc\b\.?|and so on\b|and/or\b|various\b)", re.I),
     "which leaves a list open", "give the whole list, or the one thing"),
    (re.compile(r"\b(currently|at the moment|for now)\b", re.I),
     "which dates the sentence", "say what it does, and put a planned change in a note at the end of the page"),
    # "the one" stands in for a thing the sentence never names; "the one-time" is a different word.
    (re.compile(r"\b(the ones?)\b(?!-)", re.I),
     "which points at a thing instead of naming it", "name the thing"),
    (re.compile(r"\b(a number of|reasonable)\b", re.I),
     "which gives no figure", "give the number, or the condition"),
    # "anything" is "the ones" without even the article: the sentence was written to say which thing, and
    # this is the word that leaves it out.
    (re.compile(r"\b(anything)\b", re.I),
     "which stands in for the thing instead of naming it", "name the thing"),
    # A passive past participle with no actor: "where PDFs are kept" never says who keeps them, or where.
    (re.compile(r"\b(kept)\b", re.I),
     "which hides who keeps it", "name who keeps it, or say where it lives"),
)
# One English for every wiki: American, and the word a person would say out loud. Each entry gives the
# word refused and the word to write, because "not American English" tells a writer to look it up and
# "write 'behavior'" tells them what to type.
#
# Every word is written out. A rule on the ending would be a tenth of the size and would take "raise",
# "precise", "promise", "otherwise", "surprise", "advise", "revise" and "exercise" with it -- all correct,
# all already in these pages -- so the list is the point, not an accident of how it was written.
BRITISH = {
    "behaviour": "behavior", "behaviours": "behaviors", "behavioural": "behavioral",
    "colour": "color", "colours": "colors", "coloured": "colored", "colouring": "coloring",
    "favour": "favor", "favours": "favors", "favoured": "favored", "favourite": "favorite",
    "flavour": "flavor", "flavours": "flavors", "honour": "honor", "honours": "honors",
    "humour": "humor", "labour": "labor", "labours": "labors",
    "neighbour": "neighbor", "neighbours": "neighbors", "neighbouring": "neighboring",
    "rumour": "rumor", "rumours": "rumors", "endeavour": "endeavor", "endeavours": "endeavors",
    "labelled": "labeled", "labelling": "labeling", "cancelled": "canceled", "cancelling": "canceling",
    "travelled": "traveled", "travelling": "traveling", "traveller": "traveler",
    "modelled": "modeled", "modelling": "modeling", "signalled": "signaled", "signalling": "signaling",
    "fuelled": "fueled", "fuelling": "fueling", "marvellous": "marvelous",
    "skilful": "skillful", "wilful": "willful", "enrol": "enroll", "enrolment": "enrollment",
    "instalment": "installment", "fulfil": "fulfill", "fulfils": "fulfills", "fulfilment": "fulfillment",
    "licence": "license", "licences": "licenses", "defence": "defense", "defences": "defenses",
    "offence": "offense", "offences": "offenses", "pretence": "pretense", "practise": "practice",
    "practised": "practiced", "practising": "practicing",
    "centre": "center", "centres": "centers", "centred": "centered", "metre": "meter", "metres": "meters",
    "litre": "liter", "litres": "liters", "fibre": "fiber", "fibres": "fibers", "theatre": "theater",
    "judgement": "judgment", "judgements": "judgments", "ageing": "aging",
    "catalogue": "catalog", "catalogues": "catalogs", "programme": "program", "programmes": "programs",
    "grey": "gray", "greyed": "grayed", "storey": "story", "storeys": "stories", "tyre": "tire",
    "cheque": "check", "cheques": "checks", "plough": "plow", "aluminium": "aluminum",
    "aeroplane": "airplane", "manoeuvre": "maneuver", "moustache": "mustache", "draught": "draft",
    "learnt": "learned", "spelt": "spelled", "burnt": "burned", "dreamt": "dreamed", "leapt": "leaped",
    "towards": "toward", "afterwards": "afterward", "forwards": "forward", "backwards": "backward",
    "upwards": "upward", "downwards": "downward", "amidst": "amid",
    "analyse": "analyze", "analyses": "analyzes", "analysed": "analyzed", "analysing": "analyzing",
    "paralyse": "paralyze", "paralysed": "paralyzed", "catalyse": "catalyze",
}
# The -ise verbs. Their endings are spelled out here rather than matched, for the reason above: the stem is
# what differs, and it differs by one letter.
for _stem in ("organis", "recognis", "summaris", "capitalis", "minimis", "maximis", "normalis",
              "serialis", "initialis", "customis", "optimis", "prioritis", "standardis", "emphasis",
              "realis", "utilis", "apologis", "categoris", "specialis", "visualis", "authoris",
              "itemis", "familiaris", "generalis", "memoris", "synchronis", "criticis", "summaris"):
    for _ending in ("e", "es", "ed", "ing", "ation", "ations", "er", "ers"):
        BRITISH[_stem + _ending] = _stem[:-1] + "z" + _ending

# Words a person would not say out loud: old English, and the legal register that reads as ceremony. Each
# gives the plain word that replaces it.
#
# A word with a plain meaning in some field stays out, however archaic it sounds elsewhere: "manifold" is a
# part of an engine and a surface in mathematics, and no list here can know which a project documents.
OLD_ENGLISH = {
    "whilst": "write 'while'", "amongst": "write 'among'", "betwixt": "write 'between'",
    "whence": "write 'where from'", "thence": "write 'from there'", "hitherto": "write 'until now'",
    "heretofore": "write 'until now'", "henceforth": "write 'from now on'", "forthwith": "write 'now'",
    "hereby": "delete the word", "herein": "delete the word", "hereto": "delete the word",
    "thereof": "name what it belongs to", "thereto": "name what it belongs to",
    "thereby": "name what does it", "therein": "name what it is in",
    "whereof": "name what it belongs to", "wherein": "name what it is in",
    "whereupon": "write 'and then'", "wherewith": "name what it is done with",
    "aforementioned": "name the thing", "aforesaid": "name the thing",
    "insofar": "write 'as far as'", "notwithstanding": "write 'even so'", "lest": "write 'in case'",
    "unto": "write 'to'", "ere": "write 'before'", "oft": "write 'often'", "nigh": "write 'near'",
    "albeit": "write 'though'", "sundry": "write 'several'",
    "hath": "write 'has'", "doth": "write 'does'", "thee": "write 'you'", "thou": "write 'you'",
    "thy": "write 'your'", "thine": "write 'yours'", "shall": "write 'will' or 'must'",
    "ought": "write 'should'", "thus": "write 'so'", "hence": "write 'so'", "ergo": "write 'so'",
}
# Not a spelling of anything. It is written all the same, so it is refused by name rather than left to a
# reader to puzzle over.
NOT_A_WORD = {"fellen": "write 'fell' or 'fallen'"}
PLAIN_ENGLISH = re.compile(r"\b(%s)\b" % "|".join(
    sorted(list(BRITISH) + list(OLD_ENGLISH) + list(NOT_A_WORD), key=len, reverse=True)), re.I)


def plain_english_problems(root, wiki=None):
    """Words that are not American English, that no person says out loud, or that are not words at all.

    A wiki read by people who did not write it reads in one English, and each of these is refused with the
    word to write in its place. Code is left alone, because a name is written the way the software spells
    it.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        for place, text in wording_places(path, pages_dir):
            # Every word, not the first: with this many words listed, one refusal a run would have a writer
            # fixing a sentence and running the check again for the next word in it.
            seen = []
            for found in PLAIN_ENGLISH.finditer(text):
                word = found.group(0).lower()
                if word in seen:
                    continue
                seen.append(word)
                if word in BRITISH:
                    problems.append(f"{place} says {word!r}, which is not American English; "
                                    f"write {BRITISH[word]!r}")
                elif word in OLD_ENGLISH:
                    problems.append(f"{place} says {word!r}, which no person says out loud; "
                                    f"{OLD_ENGLISH[word]}")
                else:
                    problems.append(f"{place} says {word!r}, which is not a word; {NOT_A_WORD[word]}")
    return problems


# An infobox value that is nothing but one of these gives a reader nothing to check.
EMPTY_VALUE = re.compile(r"yes|configurable|varies|depends", re.I)


def empty_word_problems(root, wiki=None):
    """Words that carry no fact a reader can check, each refused with what to write instead.

    They are looked for wherever a vague actor is, and an infobox value that is nothing but an empty word is
    refused as well: a reader cannot check "configurable", only the default or the condition.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        for place, text in wording_places(path, pages_dir):
            for pattern, effect, instead in EMPTY_WORDS:
                found = pattern.search(text)
                if found:
                    problems.append(f"{place} says {found.group(0).lower()!r}, {effect}; {instead}")
        meta, _ = read_front_matter(path)
        for group in meta.get("infobox", []):
            for row in group.get("rows", []):
                value = str(row.get("value", "")).strip()
                if EMPTY_VALUE.fullmatch(value):
                    problems.append(f"{path.relative_to(pages_dir)}: the infobox row {row.get('label', '')!r} "
                                    f"gives {value!r} as its value, which a reader cannot check; give the "
                                    "default or the condition, or drop the row")
    return problems


def prose_links(path):
    """Every link a page's prose makes, as (line, target), leaving out pictures and addresses already settled.

    Footnotes and code are blanked rather than removed, so every link keeps its line; inline code keeps its
    width too. Code is left alone because a sample shows a link as written, and a reference is held to the
    citation check instead.
    """
    text = path.read_text(encoding="utf-8")
    _, body = read_front_matter(path)
    first = text[:len(text) - len(body)].count("\n") + 1

    def blank(match):
        return "\n" * match.group(0).count("\n")

    body = FENCED.sub(blank, FOOTNOTE.sub(blank, body))
    body = INLINE_CODE.sub(lambda code: " " * len(code.group(0)), body)
    for link in MARKDOWN_LINK.finditer(body):
        opening, target, _ = link.groups()
        if not opening.startswith("!") and not SETTLED_LINK.match(target):
            yield first + body[:link.start()].count("\n"), target


def dead_link_problems(root, wiki=None):
    """Links to a page the wiki does not have.

    A link that leads nowhere looks exactly like one that leads somewhere until somebody follows it, and a
    reader who does has been told a page exists that does not, so a link to a missing page is drawn red
    and this check refuses it. Code is left alone, because a sample shows a link as written; a link outside the pages, or off the site, is not a page link at all.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    page_ids = {path.relative_to(pages_dir).with_suffix("").as_posix() for path in pages_dir.rglob("*.md")}
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        for line, target in prose_links(path):
            target_id = linked_page(path, target.partition("#")[0], pages_dir)
            if target_id is not None and target_id not in page_ids:
                problems.append(f"{path.relative_to(pages_dir)}:{line}: links to {target}, which is no page in the "
                                "wiki; write that page, or link to one that exists")
    return problems


def link_line(path, spellings, searched):
    """":<line>" for where a page's file writes a link, or "" when no spelling of its address is in the file.

    The build records a link from the rendered page, which keeps no line, so its address is found in the file
    again: after the links already found on that page, so a PDF linked twice is named at each line.
    """
    text = path.read_text(encoding="utf-8")
    for spelling in spellings:
        at = text.find(spelling, searched.get(path, 0))
        at = text.find(spelling) if at == -1 else at
        if at != -1:
            searched[path] = at + len(spelling)
            return ":%d" % (text[:at].count("\n") + 1)
    return ""


def pdf_problems(root, wiki, links):
    """Links to a PDF that would be dead once published, or too large to publish.

    `links` holds every PDF link a build wrote, as `build()` records them in `pdf_links`, so the check judges
    each link as the build wrote it, in whatever form the markdown gave it: with a title, in angle brackets, by
    reference, or with a query. A build carries a PDF only from the wiki's files folder, so a link to one
    anywhere else works while the project is served and leads nowhere on a host. A PDF in that folder past the
    limit is refused as well.
    """
    wiki = wiki_of(root, wiki)
    pages_dir, files_dir = wiki / "pages", wiki / FILES
    problems, searched = [], {}
    for path, written in links:
        shown = urllib.parse.unquote(written)
        place = f"{path.relative_to(pages_dir)}{link_line(path, (written, shown), searched)}: links to {shown}"
        address = written.partition("#")[0].partition("?")[0]
        name = filed_name(path, address, files_dir)
        if name is None:
            name = posixpath.basename(urllib.parse.unquote(address))
            link = posixpath.join(os.path.relpath(files_dir, path.parent).replace(os.sep, "/"), name)
            problems.append(f"{place}, which is outside the wiki's files folder and would be dead once "
                            f"published; put {name} in the files folder and link it as {link}")
        elif not (files_dir / name).is_file():
            problems.append(f"{place}, which does not exist; put {name} in the wiki's files folder, or correct "
                            "the link")
        elif (files_dir / name).stat().st_size > PDF_LIMIT:
            problems.append(f"{place}, which is {file_size((files_dir / name).stat().st_size)}, over the "
                            f"{PDF_LIMIT // MEGABYTE} MB a PDF may be; make it smaller, such as by compressing "
                            "its pictures, or split it into parts")
    return problems


def pointing_problems(root, wiki=None):
    """Names and sentences that point at the project instead of naming it.

    A title, infobox group or label that opens "This" or "Our" names nothing outside the page it sits on,
    and "this repository" in a sentence means nothing to a reader who arrived from a search or a link, so
    "This site", "This repository" and wording of their kind are never written. Code is left alone, because a message the software prints is quoted as it is.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    problems = []
    for path in sorted(pages_dir.rglob("*.md")):
        meta, _ = read_front_matter(path)
        name = path.relative_to(pages_dir)
        names = [("title", meta.get("title", ""))]
        for group in meta.get("infobox", []):
            names.append(("infobox group", group.get("group", "")))
            names += [("infobox label", row.get("label", "")) for row in group.get("rows", [])]
        for kind, text in names:
            if DEMONSTRATIVE.match(text):
                problems.append(f"{name}: the {kind} {text!r} points at the page instead of naming "
                                "anything; name the thing itself")
        for place, text in wording_places(path, pages_dir, ("subtitle", "intent")):
            found = POINTING.search(text)
            if found:
                problems.append(f"{place} points at the project with {found.group(0)!r} instead of naming it; "
                                "use its name")
    return problems


def page_digest(pages, page_id, sections):
    """What a page is, for the purpose of "has it changed": its own markdown, and for the page generated
    from other pages' intents, the titles and intents it collects, in its order. The template and the
    stylesheet are deliberately not part of it -- restyling the site is not the page being updated.

    The goals page is dated as the full wiki shows it, whichever build is run, so a user build does not
    move a date the full wiki then moves back. A draft is not collected, so its intent is not part of it.
    """
    content = pages[page_id]["raw"]
    if page_id == GOALS_ID:
        content += "".join("\n%s\n%s" % (pages[other]["title"], pages[other]["intent"])
                           for other in goals_order(pages, sections, "internal"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def audit(root, page_names, wiki=None, today=None):
    """Record the day each page was checked against the code, and return the line to print for each.

    The day sits beside the page's date rather than in the page, because editing the page would move the
    day it was updated. It is recorded only against the page its date describes: a page edited since has
    not been built, so what readers are about to see is not what was checked. Every page is checked
    before any is recorded, so a refused audit records nothing.
    """
    wiki = wiki_of(root, wiki)
    _, budget, sections = read_config(wiki)
    pages = read_pages(wiki / "pages", budget["intent"])
    dates = read_dates(wiki)
    today = today or datetime.date.today().isoformat()
    names = [name[:-len(".md")] if name.endswith(".md") else name for name in page_names]
    for name in names:
        if name not in pages:
            raise WikiError(f"there is no page {name}.md to audit; name a page by its path under pages, "
                            "such as checks/budgets")
        # A page excused from citations states nothing traced to the code, so there is nothing to audit.
        if not pages[name]["meta"].get("goals", True):
            raise WikiError(f"{name}.md says goals = false, so it cites nothing and has nothing to audit; "
                            "leave it out")
        if dates.get(name, {}).get("digest") != page_digest(pages, name, sections):
            raise WikiError(f"{name}.md has changed since its date was recorded; run `wiki build`, then "
                            "audit it again")
    for name in names:
        dates[name]["audited"] = today
    write_dates(wiki, dates)
    return [f"wiki: {name} audited {spoken_date(today)}" for name in names]


def date_problems(root, wiki=None):
    """Pages whose content has moved since the record was written.

    The record is committed and the rendered site is not, so this is what stops a page being edited,
    committed, and read by someone under a date from before the edit.
    """
    wiki = wiki_of(root, wiki)
    _, budget, sections = read_config(wiki)
    pages = read_pages(wiki / "pages", budget["intent"])
    dates = read_dates(wiki)
    problems = []
    for page_id in sorted(pages):
        if dates.get(page_id, {}).get("digest") != page_digest(pages, page_id, sections):
            problems.append(f"{page_id}.md has changed since its date was recorded; "
                            "run `wiki build`")
    for gone in sorted(set(dates) - set(pages)):
        problems.append(f"{DATES} still records {gone}.md, which no longer exists; "
                        "run `wiki build`")
    return problems


def budget_problems(counts, goals_words, budget):
    problems = []
    for page_id in sorted(counts):
        if page_id == GOALS_ID:
            continue
        if counts[page_id] > budget["page"]:
            problems.append(
                f"{page_id}.md runs to {counts[page_id]} words, over the {budget['page']} a page you "
                "consult may use; cut what does not serve the intent, or split the page if the intent "
                "has grown")
    if goals_words > budget["goals"]:
        problems.append(f"the collected goals run to {goals_words} words, over the "
                        f"{budget['goals']} that can be read in one sitting")
    return problems


def version_problems(site, version):
    """Whether the pages were written against the tool that is about to check them."""
    recorded = site.get("tool_version") or ""
    if not recorded:
        return [f"{CONFIG} does not say which release of the tool these pages were written against; "
                "run `wiki sync`"]
    if recorded != version:
        return [f"these pages were written against wiki-builder {recorded} and this is {version}; "
                "run `wiki sync`, then expect any rule added since to be enforced here"]
    return []


# A second-level heading: the sections the members of a family share.
SECTION_HEADING = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.M)


def pages_by_id(root, wiki=None):
    """The pages folder, and every page's path, front matter and body by its id."""
    pages_dir = wiki_of(root, wiki) / "pages"
    found = {}
    for path in sorted(pages_dir.rglob("*.md")):
        meta, body = read_front_matter(path)
        found[path.relative_to(pages_dir).with_suffix("").as_posix()] = (path, meta, body)
    return pages_dir, found


def section_headings(body):
    """A page's second-level headings in order, as the page shows them, leaving out any in a code sample.

    A closing run of hashes and the backticks around a name are markdown, not words a reader sees.
    """
    return [re.sub(r"[ \t]+#+$", "", match.group(1)).replace("`", "").strip()
            for match in SECTION_HEADING.finditer(FENCED.sub("", body))]


def index_problems(root, wiki=None):
    """Index tables a page declares that the build cannot write, and pages it says to list but cannot find.

    An index is a table over a named set of pages rather than over a page's children, so nothing about
    the tree tells the build whether the writer meant what they typed. A pattern matching no page is the
    way one goes wrong silently -- a table that empties itself after a page moves looks exactly like a
    table over a set that is empty -- so it is refused rather than left to publish blank.
    """
    pages_dir, pages = pages_by_id(root, wiki)
    problems = []
    for page_id in sorted(pages):
        _, meta, body = pages[page_id]
        # Judged as the build writes the page: the table replaces the marker only where the marker is a
        # paragraph of its own, so one inside a list, a quote or an indented block would stay as written.
        written = INDEX_TABLE in INLINE_CODE.sub("", FENCED.sub("", body))
        placed = make_markdown()(body).count("<p>%s</p>" % INDEX_TABLE) if written else 0
        index = meta.get("index")
        if written and not placed:
            problems.append(f"{page_id}.md has {INDEX_TABLE} where the build cannot write the table, such as "
                            "in a list, a quote or an indented block; put it on a line of its own, with a "
                            "blank line before and after")
        elif placed > 1:
            problems.append(f"{page_id}.md has {INDEX_TABLE} {placed} times; keep one, where the table goes")
        if index is None:
            if placed:
                problems.append(f"{page_id}.md has {INDEX_TABLE} but declares no [index]; declare it, with "
                                "pages naming the pages to list and columns naming what each row shows")
            continue
        if not isinstance(index, dict):
            problems.append(f"{page_id}.md: index must be a table, written [index] with pages and columns "
                            "under it")
            continue
        if not placed:
            problems.append(f"{page_id}.md declares [index] but has no {INDEX_TABLE}; put {INDEX_TABLE} on a "
                            "line of its own where the table goes")
        patterns = index.get("pages")
        patterns = [patterns] if isinstance(patterns, str) else patterns
        if (not isinstance(patterns, list) or not patterns
                or not all(isinstance(pattern, str) and pattern for pattern in patterns)):
            problems.append(f"{page_id}.md: index.pages must name the pages to list, as one address or a "
                            'list of them, such as pages = "area/*"')
            continue
        listed = index_pages(patterns, [other for other in pages if other != page_id])
        for pattern in patterns:
            if not index_pages([pattern], [other for other in pages if other != page_id]):
                problems.append(f"{page_id}.md: index.pages names {pattern!r}, which matches no page; name "
                                "pages by their address under pages, where * stops at a / and ** does not")
        columns = index.get("columns")
        if not isinstance(columns, list) or not columns or not all(isinstance(c, dict) for c in columns):
            problems.append(f"{page_id}.md: index.columns must list what each row shows, each one a table, "
                            'such as columns = [{ heading = "Pages", count = true }]')
            continue
        for column in columns:
            named = [key for key in ("field", "label", "count") if column.get(key)]
            heading = str(column.get("heading", ""))
            if not heading:
                problems.append(f"{page_id}.md: an index column states no heading; give every column a "
                                'heading, such as { heading = "Pages", count = true }')
            if len(named) != 1:
                problems.append(f"{page_id}.md: the index column {heading!r} names {len(named)} of field, "
                                "label and count; give each column exactly one of them")
            elif named == ["field"] and str(column["field"]) not in COLUMN_FIELDS:
                problems.append(f"{page_id}.md: the index column {heading!r} shows the front matter "
                                f"{column['field']!r}, which a column may not show; show one of "
                                f"{', '.join(COLUMN_FIELDS)}, or an infobox label with label = ")
        if index.get("total") and not any(column.get("count") for column in columns):
            problems.append(f"{page_id}.md declares index.total but no column counts anything; add a column "
                            "with count = true, or take total out")
    return problems


def family_problems(root, wiki=None):
    """Members of a declared family that stray from its layout, and members their parent does not link.

    A parent opts in with [family] in its front matter: `headings`, the second-level headings its members
    use, in that order, and `labels`, the infobox labels a member may use. A member may leave out any of
    them, so a section that does not apply is simply not written, and a key the family does not declare is
    not checked. Each problem names both fixes: change the member, or change the layout on the parent.
    """
    pages_dir, pages = pages_by_id(root, wiki)
    problems = []
    for parent_id in sorted(pages):
        parent_path, meta, body = pages[parent_id]
        # Judged as the build writes the page: the table replaces the marker only where the marker is a paragraph
        # of its own, so one inside a list, a quote or an indented block would stay on the page as written.
        written = FAMILY_TABLE in INLINE_CODE.sub("", FENCED.sub("", body))
        placed = make_markdown()(body).count("<p>%s</p>" % FAMILY_TABLE) if written else 0
        marked = placed > 0
        if written and not placed:
            problems.append(f"{parent_id}.md has {FAMILY_TABLE} where the build cannot write the table, such as in a "
                            "list, a quote or an indented block; put it on a line of its own, with a blank line "
                            "before and after")
        elif placed > 1:
            problems.append(f"{parent_id}.md has {FAMILY_TABLE} {placed} times; keep one, where the member table goes")
        if "family" not in meta:
            if marked:
                problems.append(f"{parent_id}.md has {FAMILY_TABLE} but declares no [family]; declare the family's "
                                "layout, with table naming the infobox labels its member table compares")
            continue
        if not isinstance(meta["family"], dict):
            problems.append(f"{parent_id}.md: family must be a table, written [family], holding headings and "
                            'labels, such as headings = ["Usage", "Output"]')
            continue
        layout = {key: meta["family"].get(key) for key in ("headings", "labels", "table")}
        # An empty list would refuse every name a member uses, which is never what a writer meant.
        wrong = [key for key, value in layout.items()
                 if value is not None and (not isinstance(value, list) or not value
                                           or not all(isinstance(item, str) and item for item in value))]
        for key in wrong:
            meaning, example, tail = {
                "headings": ("headings every member of the family may use", '["Usage", "Output"]',
                             " to check no headings"),
                "labels": ("labels every member of the family may use", '["Command", "Files written"]',
                           " to check no labels"),
                "table": ("infobox labels the member table compares", '["Options", "Files written"]', ""),
            }[key]
            problems.append(f"{parent_id}.md: family.{key} must list the {meaning}, such as {key} = {example}, or "
                            f"leave family.{key} out{tail}")
        if wrong:
            continue
        prose = INLINE_CODE.sub("", FENCED.sub("", body))
        linked = {linked_page(parent_path, link.group(2).partition("#")[0], pages_dir)
                  for link in MARKDOWN_LINK.finditer(prose) if not link.group(1).startswith("!")}
        headings, labels, table = layout["headings"], layout["labels"], layout["table"]
        for label in table if table is not None and labels is not None else []:
            if label not in labels:
                problems.append(f"{parent_id}.md: family.table lists {label!r}, which family.labels does not; add it "
                                "to family.labels, or take it out of family.table")
        if table is not None and not written:
            problems.append(f"{parent_id}.md declares family.table but has no {FAMILY_TABLE}; put {FAMILY_TABLE} on "
                            "its own line where the member table goes")
        if written and table is None:
            problems.append(f"{parent_id}.md has {FAMILY_TABLE} but declares no family.table; add table = [...] "
                            "under [family], naming the infobox labels the member table compares")
        # The member table the build writes links every member, so the parent needs no link of its own to each.
        if marked and table is not None:
            linked = set(children_of(parent_id, set(pages)))
        for child_id in children_of(parent_id, set(pages)):
            _, child_meta, child_body = pages[child_id]
            if child_id not in linked:
                problems.append(f"{parent_id}.md does not link {child_id}.md, a member of its family; link every "
                                "member from the parent, such as in a table of the members")
            previous = None
            for heading in section_headings(child_body) if headings is not None else []:
                if heading not in headings:
                    problems.append(f"{child_id}.md: the heading {heading!r} is not in the family layout on "
                                    f"{parent_id}.md; rename it to one of {', '.join(headings)}, or add it to "
                                    "family.headings there")
                    continue
                if previous is not None and headings.index(heading) <= headings.index(previous):
                    problems.append(f"{child_id}.md: the heading {previous!r} comes before {heading!r}, but "
                                    f"family.headings on {parent_id}.md lists {heading!r} first; order the "
                                    "headings as it lists them")
                previous = heading
            rows = [row for group in child_meta.get("infobox", []) for row in group.get("rows", [])]
            for row in rows if labels is not None else []:
                label = str(row.get("label", ""))
                if label not in labels:
                    problems.append(f"{child_id}.md: the infobox label {label!r} is not in the family layout on "
                                    f"{parent_id}.md; rename it to one of {', '.join(labels)}, or add it to "
                                    "family.labels there")
    return problems


def families_report(root, wiki=None):
    """What `wiki families` prints: parents whose children share no declared layout, and nested titles that
    repeat their parent's.

    A report, not a check. Whether pages are things of one kind is a person's judgement, so it shows each
    child's headings side by side, which is what a family declaration would compare, and decides nothing.
    """
    _, pages = pages_by_id(root, wiki)
    lines, declared, undeclared = [], 0, 0
    for parent_id in sorted(pages):
        meta = pages[parent_id][1]
        children = children_of(parent_id, set(pages))
        if "family" in meta:
            declared += 1
        elif len(children) >= 2:
            undeclared += 1
            lines.append(f"{parent_id}.md declares no family for its {len(children)} children")
            lines += [f"  {child}.md: {', '.join(section_headings(pages[child][2])) or 'no headings'}"
                      for child in children]
        parent_title = str(meta.get("title", ""))
        parent_words = {word.rstrip("s") for word in re.findall(r"[a-z]+", parent_title.lower()) if len(word) > 3}
        for child in children:
            title = str(pages[child][1].get("title", ""))
            repeated = [word for word in re.findall(r"[a-z]+", title.lower())
                        if len(word) > 3 and word.rstrip("s") in parent_words]
            if repeated:
                lines.append(f"{child}.md is titled {title!r}, which repeats {repeated[0]!r} from its parent's "
                             f"title {parent_title!r}; a nested page's title names only what sets it apart")
    lines.append(f"{declared} famil{'y' if declared == 1 else 'ies'} declared; {undeclared} parent"
                 f"{'' if undeclared == 1 else 's'} with two or more children declaring none")
    return lines


# What every producer already writes at the head of its sentence: the file the problem is on, then the
# line when it has one. Nothing here is invented -- a sentence that names no file carries none in its
# record, rather than having one guessed for it.
PROBLEM_PLACE = re.compile(r"^(?P<file>\S+\.\w+)(?::(?P<line>\d+))?:?\s")


def problem_record(rule, problem):
    """One problem as another tool reads it: where it is, which check refused it, and the sentence.

    The sentence is kept whole, head included, rather than cut into the fields beside it. The fields are
    an addition, so a producer whose shape this does not recognise still yields a record a person can read
    instead of a mangled one.
    """
    found = PROBLEM_PLACE.match(problem)
    return {"file": found.group("file") if found else None,
            "line": int(found.group("line")) if found and found.group("line") else None,
            "rule": rule,
            "message": problem}


def scoped_page(name, problem_file):
    """Whether a problem's file is a page a scoped run named, or a page beneath it."""
    if problem_file is None:
        return False
    named = name[:-3] if name.endswith(".md") else name
    named = named[len("pages/"):] if named.startswith("pages/") else named
    return problem_file == named + ".md" or problem_file.startswith(named + "/")


# What the build is needed for, and so what a scoped run cannot say. Everything else reads the pages'
# markdown, and the build is nine tenths of a check's time on a wiki of a few hundred pages.
BUILT_CHECKS = ("budget", "pdf")


def page_checks(root, wiki):
    """Every check that reads the pages' markdown, in the order they are reported, named as it goes.

    The table check comes before the citation checks: a table the renderer threw away still cites
    correctly as markdown, so their silence about it is the thing that needs explaining first.
    """
    return (("picture", picture_problems(root, wiki)),
            ("date", date_problems(root, wiki)),
            ("citation", citation_problems(root, wiki)),
            ("heading", heading_problems(root, wiki)),
            ("pointing", pointing_problems(root, wiki)),
            ("dead-link", dead_link_problems(root, wiki)),
            ("attribution", attribution_problems(root, wiki)),
            ("vague-actor", vague_actor_problems(root, wiki)),
            ("empty-word", empty_word_problems(root, wiki)),
            ("plain-english", plain_english_problems(root, wiki)),
            ("table", table_problems(root, wiki)),
            ("uncited", uncited_problems(root, wiki)),
            ("infobox", infobox_problems(root, wiki)),
            ("family", family_problems(root, wiki)),
            ("index", index_problems(root, wiki)))


def check_pages(root, wiki, version, records, only):
    """The checks that read the markdown, reported for the pages a scoped run named.

    Every one of them runs over the whole wiki, because a check reads one page against the others -- a
    family against its parent, a link against the page it names. Only the reporting narrows, so a scoped
    run can say how many problems it is not showing rather than pretending there are none.
    """
    # A name matching no page would otherwise report nothing wrong with it, which is what a clean page
    # looks like. A typed path is the likeliest way to reach this, and the likeliest to be believed.
    known = sorted(path.relative_to(wiki / "pages").with_suffix("").as_posix()
                   for path in (wiki / "pages").rglob("*.md"))
    for name in only:
        if not any(scoped_page(name, page + ".md") for page in known):
            raise WikiError(f"there is no page or folder {name} to check; name one by its path under "
                            "pages, such as checks/budgets or checks")
    problems, elsewhere = [], 0
    named = list(page_checks(root, wiki))
    if version:
        named.append(("version", version_problems(read_config(wiki)[0], version)))
    for rule, found in named:
        for problem in found:
            record = problem_record(rule, problem)
            if not any(scoped_page(name, record["file"]) for name in only):
                elsewhere += 1
                continue
            problems.append(problem)
            if records is not None:
                records.append(record)
    return problems, elsewhere


def check(root, wiki=None, version=None, records=None, only=None, skipped=None):
    """Every reason the wiki is not fit to read, as sentences rather than a diff.

    The rendered site is not committed -- it is built before it is served, so it cannot be stale and
    there is nothing to compare against. What can still go wrong is a page that no longer renders, one
    that states something and cites nothing, a heading that asks a question rather than naming its
    section, a page grown past what anyone will read, and a picture that has outlived its subject.
    """
    wiki = wiki_of(root, wiki)
    problems = []
    if only:
        # The build writes every page to learn two things: each page's word count, and the PDFs the
        # pages link. Both are the whole wiki's business, and neither is worth nine tenths of the time
        # to someone fixing one page. What did not run is reported rather than left for them to assume.
        if skipped is not None:
            skipped.extend(BUILT_CHECKS)
        found, elsewhere = check_pages(root, wiki, version, records, only)
        if skipped is not None:
            skipped.append(elsewhere)
        return found, {}, 0, read_config(wiki)[1]
    with tempfile.TemporaryDirectory() as work:
        # Checked as it will be read: from the place the site is actually served from.
        # The PDF links are the ones this build writes, so the check can never read a link the build does not.
        pdf_links = []
        counts, goals_words, budget, _ = build(root, Path(work) / "site", "internal",
                                               wiki / "site", record=False, wiki_dir=wiki, pdf_links=pdf_links)
        def add(rule, found):
            """Keep one check's problems, and a record of each naming the check that refused it.

            The rule comes from here rather than from the sentence, because the aggregator is the only
            place that knows which check produced which problems without every producer being rewritten.
            """
            problems.extend(found)
            if records is not None:
                records.extend(problem_record(rule, problem) for problem in found)

        # The two the build is for, together, and then everything that reads the markdown.
        add("budget", budget_problems(counts, goals_words, budget))
        add("pdf", pdf_problems(root, wiki, pdf_links))
        for rule, found in page_checks(root, wiki):
            add(rule, found)
        if version:
            site, _, _ = read_config(wiki)
            add("version", version_problems(site, version))
    return problems, counts, goals_words, budget


def bless(root, picture, reason, wiki=None):
    """Record that someone looked and the picture is still true, with why."""
    images_dir = wiki_of(root, wiki) / "images"
    ledger = read_ledger(images_dir)
    if picture not in ledger:
        raise WikiError(f"{picture} has no entry in {LEDGER}")
    if not reason.strip():
        raise WikiError("a blessing needs a reason; it is the record that the picture was looked at")
    ledger[picture]["digest"] = subject_digest(root, ledger[picture].get("depicts", []))
    ledger[picture]["blessed"] = reason.strip()
    write_ledger(images_dir, ledger)
    return f"wiki: {picture} blessed -- {reason.strip()}"


# A line number, or a range of lines, after a cited file: src/app.py:12 or src/app.py:12-34.
LINE_NUMBER = re.compile(r":\d+(?:-\d+)?$")


def cited_paths(body):
    """Every project path a page's references name in backticks, as written, without a line number.

    A code block shows a reference rather than making one, so fenced code is taken out first.
    """
    for note in FOOTNOTE.finditer(FENCED.sub("", body)):
        for code in INLINE_CODE.findall(note.group(1)):
            name = LINE_NUMBER.sub("", code.strip("`").strip())
            if name and not any(mark in name for mark in (" ", "://", "*")) and not name.startswith(("/", "-")):
                yield name


def coverage(root, wiki=None):
    """The source files no page cites, and every citation of a file that does not exist.

    Counted from the project's side, so a wiki cannot hide its own gaps: `wiki check` proves each sentence
    cites something, and this names the files nothing cites. A folder covers none of its files, because a
    citation of a folder says nothing about what any one file in it does. None when wiki.toml has no
    [coverage] table.
    """
    wiki = wiki_of(root, wiki)
    patterns = read_coverage(wiki)
    if patterns is None:
        return None
    include, exclude = patterns

    def matching(globs):
        return {path.relative_to(root).as_posix() for pattern in globs for path in root.glob(pattern)
                if path.is_file()}

    files = sorted(matching(include) - matching(exclude))
    if not files:
        raise WikiError(f"{CONFIG}: coverage.include matches no files in {root}; name the project's source "
                        'files relative to the project, such as include = ["src/**/*.py"]')
    pages_dir = wiki / "pages"
    cited, missing = set(), set()
    for path in sorted(pages_dir.rglob("*.md")):
        _, body = read_front_matter(path)
        for name in cited_paths(body):
            target = posixpath.normpath(name)
            if (root / target).is_file():
                cited.add(target)
            # A reference also names an action, a media type, a generated folder or a file a reader creates,
            # none of which is in the project. Only a file with an extension, under a folder the project
            # has, is taken for a citation that has gone stale.
            elif (not name.endswith("/") and "." in posixpath.basename(target) and "/" in target
                  and (root / target.split("/")[0]).is_dir() and not (root / target).exists()):
                missing.add((path.relative_to(pages_dir).as_posix(), name))
    return {"files": files, "uncited": [name for name in files if name not in cited], "missing": sorted(missing)}


def citation_counts(root, wiki=None):
    """How many sources each page cites, and how many of its claims carry the mark for no source.

    A source is counted once however often it is cited. A claim marked missing is a `{missing}` in the
    prose or a `missing = true` infobox row. Printed on every build and check, so whoever runs the tool --
    a person or an agent -- sees how much of the wiki is traced to the code and how much is taken on faith.
    """
    pages_dir = wiki_of(root, wiki) / "pages"
    counts = {}
    for path in sorted(pages_dir.rglob("*.md")):
        meta, body = read_front_matter(path)
        prose = FENCED.sub("", FOOTNOTE.sub("", body))
        cited = {unikey(key) for key in CITED.findall(prose)} & {unikey(key) for key in DEFINED.findall(body)}
        rows = [row for group in meta.get("infobox", []) for row in group.get("rows", [])]
        missing = len(MISSING.findall(INLINE_CODE.sub("", prose))) + sum(1 for row in rows if row.get("missing"))
        counts[path.relative_to(pages_dir).with_suffix("").as_posix()] = (len(cited), missing)
    return counts


def report(counts, goals_words, budget, drafts=(), citations=None):
    """What each page costs to read and how much of it is cited, every run, while it is being spent."""
    for page_id in sorted(counts):
        line = "wiki: %-32s %4d words" % (page_id, counts[page_id])
        if citations and page_id in citations:
            line += "  %3d cited  %3d missing" % citations[page_id]
        print(line)
    if citations:
        cited = sum(count for count, _ in citations.values())
        missing = sum(count for _, count in citations.values())
        print("wiki: %d source%s cited, %d claim%s marked as having no source"
              % (cited, "" if cited == 1 else "s", missing, "" if missing == 1 else "s"))
    print("wiki: the collected goals read in %d words" % goals_words)
    if drafts:
        print("wiki: %d page%s waiting on approval, in the sidebar but not in search, the categories "
              "or the goals: %s"
              % (len(drafts), "" if len(drafts) == 1 else "s", ", ".join(drafts)))
    if not budget.get("calibrated"):
        print("wiki: these budgets are PROVISIONAL -- %d words a page, %d for the collected goals. "
              "What this project's readers actually read has not been measured; until it is, the "
              "numbers are a guess that happens to be enforced. Set budget.calibrated in %s once it "
              "is." % (budget["page"], budget["goals"], CONFIG))

