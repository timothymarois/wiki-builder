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
from importlib import resources
from pathlib import Path

import mistune
from mistune.util import unikey

from .config import WikiError, read_config, CONFIG

# Front matter is TOML between these fences, so it is read by the standard library and costs no parser.
FENCE = "+++"

# Where the tool's own files live, so it runs from anywhere rather than only inside a repository laid
# out the way the first one was.
ASSETS = resources.files(__package__) / "assets"


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

# When each page last changed, and what it looked like then. Committed, because the rendered site is not:
# a date taken from the clock on every build would say "today" forever and tell a reader nothing. The
# date moves only when the page's own content moves, which is also what decides whether it is rewritten.
DATES = "UPDATED.toml"
MONTHS = ("January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")

# A link the renderer must not touch: it already points where it means to.
SETTLED_LINK = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|#|//)")

HEADING = re.compile(r"<(h2|h3)>(.*?)</\1>", re.S)
TAG = re.compile(r"<[^>]+>")
ATTRIBUTE = re.compile(r'(href|src)="([^"]*)"')
LONE_FIGURE = re.compile(r"<p>(<figure.*?</figure>)</p>", re.S)
FOOTNOTE_DEFINITION = re.compile(r"^\[\^[^\]]+\]:.*(?:\n(?:[ \t]+.*|))*", re.M)

# Everything the player build must not carry. Each is emitted by this file, in this exact shape, so
# stripping them is removing what we put there rather than parsing arbitrary HTML.
# An <aside>, not a <div>: the player build strips this block with a non-greedy match, which would stop
# at the first closing tag of the same kind. Markdown can put a <div> inside a citation -- a table
# wrapper, or raw HTML someone pasted -- and the strip would then truncate and leak the rest of the
# block into a player build. Nothing this renderer emits ever nests an <aside>.
INTERNAL_BLOCK = re.compile(r'<aside class="cites"[^>]*>.*?</aside>', re.S)
INTERNAL_MARKER = re.compile(r'<sup class="ref[^"]*">.*?</sup>', re.S)

# A missing citation. Every statement on a page is either traced to the code or marked here, in the place
# a reader already looks for a source. The owner, 2026-09-14: "every statement, fact, requirement, logic,
# beahvior mentions all require a citation or unknown citation." Two things put the mark there -- the
# thing is not built yet, or nobody has found where it happens -- and for a reader the consequence is the
# same: do not take this on faith. Written {missing} in the prose, or missing = true on an infobox row.
# Never shown to a player.
MISSING = re.compile(r"\{missing\}")
MISSING_CITATION = ('<sup class="ref nocite" data-audience="internal" '
                    'title="No source cited: either this is not built yet, or nobody has found where it '
                    'happens">[?]</sup>')


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
            # Draft until the owner says otherwise. A page states what part of the system is for, and
            # that is the owner's to decide -- an agent may draft one, and drafting is not deciding.
            "status": meta.get("status", "draft"),
            "categories": list(meta.get("categories", [])),
            "words": len(strip_footnote_definitions(body).split()),
        }
    if not pages:
        raise WikiError(f"{pages_dir} holds no pages; a wiki that renders nothing did not run")
    return pages


def strip_footnote_definitions(body):
    """Prose only. A citation is provenance, and counting it against a page would punish citing."""
    return FOOTNOTE_DEFINITION.sub("", body)


def read_dates(wiki):
    """What each page hashed to when it last changed, and the day that was."""
    path = wiki / DATES
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def write_dates(wiki, dates):
    lines = [
        "# When each page last changed, and what it hashed to then.",
        "#",
        "# Written by `wiki build`, never by hand. A page is re-rendered, and its date moves,",
        "# only when its own content has changed -- so the date on a page means something, and a build",
        "# that changed nothing writes nothing.",
        "",
    ]
    for page_id in sorted(dates):
        lines.append("[%s]" % toml_key(page_id))
        lines.append("updated = %s" % toml_string(dates[page_id]["updated"]))
        lines.append("digest = %s" % toml_string(dates[page_id]["digest"]))
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
    return tomllib.loads(path.read_text(encoding="utf-8"))


def write_ledger(images_dir, ledger):
    """Rewrite the ledger. Only the shapes used here -- strings and lists of strings -- are emitted."""
    lines = [
        "# What each picture shows, and what its subject hashed to when the picture was made.",
        "#",
        "# The gate fails when a depicted asset has moved and its picture has not been re-made, because a",
        "# wiki the owner reads instead of the source cannot afford a picture of something that no longer",
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
# serving it -- a browser handed a directory over file:// lists its contents instead of showing the page,
# which is what the owner hit.
#
# Empty for publishing, where "plants/" is the address and nothing ends in .html. That is the only place
# the difference is worth having, and it is a flag rather than the default.
#
# One module-level value rather than an argument threaded through six functions: every link in a build is
# the same kind, build() sets it and puts it back, and there is never more than one build at a time.
LINK_SUFFIX = "index.html"


def relative_directory(from_directory, to_directory):
    """A link from one page's directory to another's."""
    rel = posixpath.relpath("/" + to_directory, "/" + (from_directory or "."))
    return ("./" if rel == "." else rel + "/") + LINK_SUFFIX


def relative_file(from_directory, to_file):
    return posixpath.relpath("/" + to_file, "/" + (from_directory or "."))


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
        renderer=WikiRenderer(escape=False), plugins=["footnotes", "table", "strikethrough"])
    # These three the plugin adds; the renderer defines no method of its own for them, so they take.
    markdown.renderer.register("footnote_ref", footnote_reference)
    markdown.renderer.register("footnote_item", footnote_item)
    markdown.renderer.register("footnotes", footnote_block)
    markdown.renderer.cited = {}
    return markdown


def strip_tags(markup):
    return html_module.unescape(TAG.sub("", markup)).strip()


def for_player(body):
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


def rewrite_references(body, directory, site_root, root, images, page_ids, pages_dir, source_path):
    """Point every link and picture where it will actually resolve from this page's directory.

    A page is written beside its fellows, so its author links the way the repository reads: a sibling
    page as name.md, anything else by its path. Both are translated here -- the sibling to a clean
    address, the path to wherever it sits relative to this page -- so one link works while reading the
    markdown and again in the browser.
    """
    here = site_root / directory if directory else site_root

    def replace(match):
        attribute, target = match.group(1), match.group(2)
        if SETTLED_LINK.match(target):
            return match.group(0)
        address, _, fragment = target.partition("#")
        if attribute == "src":
            name = posixpath.basename(address)
            if name not in images:
                raise WikiError(f"{directory or 'the main page'} shows {name}, which has no entry in {LEDGER}")
            resolved = relative_file(directory, "images/" + name)
        else:
            # The author wrote the link relative to their own file, so resolve it from there. Inside the
            # pages tree it is a sibling page and becomes a clean address; anywhere else it is a path in
            # the repository and becomes a path from this page to it.
            absolute = (source_path.parent / address).resolve()
            # Both sides resolved, or neither: resolve() follows symlinks, and on macOS a path under
            # /var comes back under /private/var. Comparing a resolved path against an unresolved
            # directory then fails, and a link to a sibling page is emitted as an absolute filesystem
            # path that works on exactly one machine.
            pages_root = pages_dir.resolve()
            target_id = None
            if address.endswith(".md"):
                try:
                    target_id = absolute.relative_to(pages_root).with_suffix("").as_posix()
                except ValueError:
                    target_id = None
            if target_id in page_ids:
                resolved = relative_directory(directory, page_directory(target_id))
            else:
                resolved = os.path.relpath(absolute, here.resolve()).replace(os.sep, "/")
        return '%s="%s%s"' % (attribute, resolved, ("#" + fragment) if fragment else "")

    return ATTRIBUTE.sub(replace, body)


def render_source(raw):
    """The page's own markdown, and a button that copies it. The button adds no text of its own inside
    the block, so what is copied is exactly the file."""
    return ('<div class="srcbox"><button class="copy" type="button">Copy</button>'
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
            # A row may name the requirement that promises it. That identifier is traceability for
            # whoever next checks the page against the code, and it is never rendered: the owner did not
            # want a badge beside the rows that carry one.
            if row.get("missing") and audience != "player":
                missing = True
                value += " " + MISSING_CITATION
            elif audience != "player":
                # A row cites the way a sentence does: with the number its footnote has in the prose.
                value += "".join(CITATION % (cited[unikey(key)], cited[unikey(key)])
                                 for key in row_cites(row) if unikey(key) in (cited or {}))
            note = row.get("note")
            parts.append('<div class="r"><b>%s</b><span>%s%s</span></div>'
                         % (html_module.escape(str(row.get("label", ""))), value,
                            "<i>%s</i>" % html_module.escape(str(note)) if note else ""))
    if shown and missing:
        parts.append('<div class="legend">A row marked %s has no source to cite: either it is not built '
                     "yet, or nobody has found where it happens.</div>" % MISSING_CITATION)
    parts.append("</aside>")
    return "\n".join(parts)


def visible_to(audience, marked):
    """Whether something marked for one audience belongs in a build for another.

    One predicate rather than the same De Morgan pair written out at every call site: the internal and
    player split is what keeps a requirement identifier or an internal page out of a player build, and a
    rule restated five times is a rule that will be changed in four places.
    """
    return audience != "player" or marked == "player"


def descendants_of(page_id, page_ids):
    """A page and everything beneath it, depth first."""
    yield page_id
    for child in children_of(page_id, page_ids):
        yield from descendants_of(child, page_ids)


def children_of(page_id, page_ids):
    """The pages that live directly beneath this one. A page's place in the tree is its own address."""
    return sorted(other for other in page_ids
                  if other != page_id and other.rsplit("/", 1)[0] == page_id)


def render_nav(sections, pages, categories, current, directory, audience):
    """The sidebar. Its shape comes from the pages, not from labels written beside them.

    A section names the pages that start a branch; everything beneath one nests under it automatically,
    because a page that lives at a/b/c is a child of the page at a/b. Nothing has to be listed twice, and
    a new page appears in the right place by being put in the right directory.
    """
    # Every page is in the sidebar, draft or not. The owner, 2026-09-14: "all pages should always be on
    # the nav regardless of status". A draft still says so above everything else on it, and search, the
    # categories and the goals still offer only what has been approved.
    visible = {page_id for page_id in pages
               if visible_to(audience, pages[page_id]["audience"])}

    def branch(page_id):
        # Children are gathered from every page, not only the visible ones: a page hidden from this
        # audience must not take its visible children down with it. They rise to where it stood.
        below = "".join(branch(child) for child in children_of(page_id, set(pages)))
        if page_id not in visible:
            return below
        link = ('<li><a class="%s" href="%s">%s</a>'
                % ("on" if page_id == current else "",
                   relative_directory(directory, page_directory(page_id)),
                   html_module.escape(pages[page_id]["title"])))
        return link + ("<ul>%s</ul>" % below if below else "") + "</li>"

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
        markup.append("<h5>%s</h5><ul>%s</ul>"
                      % (html_module.escape(section.get("title", "")), "".join(items)))
    return "".join(markup)


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
    body = []
    for page_id in ordered:
        page = pages[page_id]
        body.append("<h2>%s</h2>" % html_module.escape(page["title"]))
        body.append("<p>%s</p>" % html_module.escape(page["intent"]))
    return "\n".join(body), sum(len(pages[page_id]["intent"].split()) for page_id in ordered)


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


def render_page(title, subtitle, hatnote, body_html, infobox, categories_bar, nav, index, site,
                directory, template, tabs=ARTICLE_ONLY, updated="", stamp_css="", stamp_js="",
                draft=False):
    body_html, entries = number_headings(body_html)
    filled = {
        "tabs": tabs,
        "tab_title": html_module.escape("%s — %s" % (title, site["name"])),
        "css": relative_file(directory, "assets/wiki.css") + stamp_css,
        "js": relative_file(directory, "assets/wiki.js") + stamp_js,
        "home": relative_directory(directory, ""),
        "site_name": html_module.escape(site["name"]),
        "tagline_line": ("<span>%s</span>" % html_module.escape(site["tagline"])) if site.get("tagline") else "",
        "nav": nav,
        "title": html_module.escape(title),
        "subtitle": html_module.escape(subtitle),
        "hatnote": (('      <p class="hat draft"><b>This page is a draft.</b> Nobody has agreed that what '
                     'it says this part of the system is for is what it should be for, so read it as a '
                     'proposal rather than as the wiki.</p>\n' if draft else "")
                    + ('      <p class="hat">%s</p>' % html_module.escape(hatnote) if hatnote else "")),
        "infobox": infobox,
        "contents": render_contents(entries),
        "body": body_html,
        "categories": categories_bar,
        "footer": ('      <div class="foot"><span>Last updated %s</span></div>'
                   % html_module.escape(spoken_date(updated))) if updated else "",
        "index": index,
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: filled.get(m.group(1), ""), template)


def build(root, out, audience, link_root=None, today=None, record=True, links="file", wiki_dir=None):
    """Write the whole site, and return the per-page word counts.

    `links` is "file" -- links that work served and off disk alike -- or "clean" for publishing.

    `out` is where the bytes go; `link_root` is where the site will be read from, which is not always the
    same place -- a check renders into a temporary directory to inspect what the real one would contain,
    and a link to a file outside the site has to be counted from where the site actually sits.
    """
    global LINK_SUFFIX
    was = LINK_SUFFIX
    LINK_SUFFIX = "" if links == "clean" else "index.html"
    try:
        return write_site(root, out, audience, link_root, today, record, wiki_of(root, wiki_dir))
    finally:
        LINK_SUFFIX = was


def write_site(root, out, audience, link_root, today, record, wiki):
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
                            "so nobody could reach it")
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
        index_entries.append({"u": page_directory(page_id), "t": pages[page_id]["title"],
                              "s": pages[page_id]["subtitle"]})
    for slug in sorted(categories):
        index_entries.append({"u": category_directory(slug),
                              "t": "Category: " + categories[slug]["name"], "s": "a category page"})

    def index_for(directory):
        """The search index as this page must address it: every other page relative to this one.

        The entries are collected site-relative, which is the only sane way to collect them and the wrong
        thing to put in a page: a browser resolves "b/" against the directory it is already in, so one
        shared index sends every result clicked on /a/ to /a/b/, and every one of them is a miss.
        """
        return json.dumps([{"u": relative_directory(directory, entry["u"]), "t": entry["t"],
                            "s": entry["s"]} for entry in index_entries],
                          sort_keys=True, separators=(",", ":"))

    # What a page is, for the purpose of "has it changed": its own markdown, and for the page generated
    # from other pages' intents, those intents too. The template and the stylesheet are deliberately not
    # part of it -- restyling the site is not the page being updated.
    def content_of(page_id):
        if page_id == GOALS_ID:
            return pages[page_id]["raw"] + "\n".join(
                pages[other]["intent"] for other in sorted(pages))
        return pages[page_id]["raw"]

    changed = []
    for page_id in sorted(pages):
        digest = hashlib.sha256(content_of(page_id).encode("utf-8")).hexdigest()
        if dates.get(page_id, {}).get("digest") != digest:
            changed.append(page_id)
            dates[page_id] = {"updated": today, "digest": digest}
    for gone in sorted(set(dates) - set(pages)):
        del dates[gone]
        changed.append(gone)
    if changed and record:
        write_dates(wiki, dates)

    counts = {}
    written = []

    def emit(directory, markup):
        destination = (out / directory / "index.html") if directory else (out / "index.html")
        destination.parent.mkdir(parents=True, exist_ok=True)
        # A page whose bytes have not moved is left alone, so what a build touched is what a build
        # actually changed.
        if not destination.is_file() or destination.read_text(encoding="utf-8") != markup:
            destination.write_text(markup, encoding="utf-8", newline="\n")
        written.append(destination)

    for page_id in emitted:
        page = pages[page_id]
        directory = page_directory(page_id)
        markdown.renderer.cited = {}
        body = markdown(page["body"])
        if page_id == GOALS_ID:
            body += goals_html
            page["raw"] += ("\n<!-- Every intent below this page's own text is collected from the other\n"
                            "     pages when the wiki is built, and is not written here. -->\n")
        body = LONE_FIGURE.sub(r"\1", body)
        # A page's own table takes the wiki's table style, and scrolls inside its wrapper on a narrow
        # screen rather than widening the page.
        body = body.replace("<table>", '<div class="wt"><table class="w">').replace("</table>",
                                                                                    "</table></div>")
        body = MISSING.sub(MISSING_CITATION, body)
        body = rewrite_references(body, directory, site_root, root, ledger, set(pages),
                                  wiki / "pages", page["path"])
        if audience == "player":
            body = for_player(body)
        # The source view names paths and internal identifiers by its nature, so it is internal only.
        with_source = audience != "player"
        emit(directory, render_page(
            page["title"], page["subtitle"], page["hatnote"], body,
            render_infobox(page, audience, directory, ledger, markdown.renderer.cited),
            render_categories(page, directory, categories),
            render_nav(sections, pages, categories, page_id, directory, audience),
            index_for(directory), site, directory, template,
            on_article() if with_source else ARTICLE_ONLY, dates[page_id]["updated"],
            stamps["wiki.css"], stamps["wiki.js"], page["status"] != "approved"))
        if with_source:
            source_directory = directory + "source/"
            emit(source_directory, render_page(
                page["title"], "markdown source of this page", "",
                render_source(page["raw"]), "", "",
                render_nav(sections, pages, categories, page_id, source_directory, audience),
                index_for(source_directory), site, source_directory, template, on_source(),
                dates[page_id]["updated"], stamps["wiki.css"], stamps["wiki.js"]))
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
            stamps["wiki.css"], stamps["wiki.js"]))

    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("wiki.css", "wiki.js"):
        written.append(copy_if_changed(ASSETS / name, assets / name))
    if ledger:
        (out / "images").mkdir(parents=True, exist_ok=True)
        for name in sorted(ledger):
            source = images_dir / name
            if not source.is_file():
                raise WikiError(f"{LEDGER} lists {name}, which is not in {images_dir}")
            written.append(copy_if_changed(source, out / "images" / name))

    # Whatever the site no longer makes goes, so a page that was deleted leaves nothing behind.
    kept = {path.resolve() for path in written}
    for path in sorted(out.rglob("*"), reverse=True):
        if path.is_file() and path.resolve() not in kept:
            path.unlink()
    for path in sorted(out.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    return counts, goals_words, budget, sorted(
        page_id for page_id in pages if pages[page_id]["status"] != "approved")


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


# A reference in a footnote definition, and a link inside one.
FOOTNOTE = re.compile(r"^\[\^[^\]]+\]:(.*(?:\n(?:[ \t]+.*|))*)", re.M)
DOCUMENT_LINK = re.compile(r"\]\(([^)]*\.md[^)]*)\)")


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
            for link in DOCUMENT_LINK.finditer(note.group(1)):
                problems.append(
                    f"{path.relative_to(pages_dir)} cites {link.group(1)}, which is a document; "
                    "a reference must name the code that does the thing")
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


# What says where a statement came from: a citation, or the mark that says there is none.
CLAIM = re.compile(r"\[\^[^\]]+\]|\{missing\}")
# Any heading line. Removed before a page is read as statements, so prose written directly beneath one is
# read like any other.
HEADING_ANY = re.compile(r"^#{1,6}[ \t].*$", re.M)
# The start of a list item inside a block, so each item is read on its own.
LIST_ITEM = re.compile(r"\n(?=[ \t]*(?:[-*+]|\d+\.)[ \t])")
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


def statements(block):
    """The statements in one block of prose: each sentence of each list item, or a table as a whole."""
    if block.startswith("|"):
        return [block]
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

    body = HEADING_ANY.sub("", FENCED.sub(blank, FOOTNOTE.sub(blank, body)))
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


def uncited_problems(root, wiki=None):
    """Sentences that state something and say nothing about where they came from.

    A reader uses this instead of reading the source, so a sentence they cannot trace is one they have to
    take on faith. Every sentence carries a reference, or the mark that says there is none -- and the
    second is a fine answer. What is not a fine answer is silence, because silence looks exactly like a
    cited claim to someone scanning the page. A sentence never borrows its neighbour's citation: one
    citation used to cover a whole paragraph, and a claim beside a cited one read as though it were checked.

    A sentence that links to another page is excused, because that page carries the citations. A table is
    held as a whole, because a row is not a sentence.
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
            if CLAIM.search(statement) or PAGE_LINK.search(statement):
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
                 for line, statement in page_statements(path) if MISSING.search(statement)]
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
        _, body = read_front_matter(path)
        for heading in HEADING_LINE.finditer(FENCED.sub("", body)):
            title = heading.group(1)
            if QUESTION_WORD.match(title):
                problems.append(f"{path.relative_to(pages_dir)}: the heading {title!r} asks a question; "
                                "name the thing the section is about")
            elif EDITORIAL.search(title):
                problems.append(f"{path.relative_to(pages_dir)}: the heading {title!r} rates its own "
                                "contents; name them instead")
    return problems


def date_problems(root, wiki=None):
    """Pages whose content has moved since the record was written.

    The record is committed and the rendered site is not, so this is what stops a page being edited,
    committed, and read by someone under a date from before the edit.
    """
    wiki = wiki_of(root, wiki)
    _, budget, _ = read_config(wiki)
    pages = read_pages(wiki / "pages", budget["intent"])
    dates = read_dates(wiki)
    problems = []
    for page_id in sorted(pages):
        content = pages[page_id]["raw"]
        if page_id == GOALS_ID:
            content += "\n".join(pages[other]["intent"] for other in sorted(pages))
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if dates.get(page_id, {}).get("digest") != digest:
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


def check(root, wiki=None, version=None):
    """Every reason the wiki is not fit to read, as sentences rather than a diff.

    The rendered site is not committed -- it is built before it is served, so it cannot be stale and
    there is nothing to compare against. What can still go wrong is a page that no longer renders, one
    that states something and cites nothing, a heading that asks a question rather than naming its
    section, a page grown past what anyone will read, and a picture that has outlived its subject.
    """
    wiki = wiki_of(root, wiki)
    problems = []
    with tempfile.TemporaryDirectory() as work:
        # Checked as it will be read: from the place the site is actually served from.
        counts, goals_words, budget, _ = build(root, Path(work) / "site", "internal",
                                               wiki / "site", record=False, wiki_dir=wiki)
        problems += budget_problems(counts, goals_words, budget)
        problems += picture_problems(root, wiki)
        problems += date_problems(root, wiki)
        problems += citation_problems(root, wiki)
        problems += heading_problems(root, wiki)
        problems += uncited_problems(root, wiki)
        problems += infobox_problems(root, wiki)
        if version:
            site, _, _ = read_config(wiki)
            problems += version_problems(site, version)
    return problems, counts, goals_words, budget


def bless(root, picture, reason, wiki=None):
    """Record that someone looked and the picture is still true, with why."""
    images_dir = wiki_of(root, wiki) / "images"
    ledger = read_ledger(images_dir)
    if picture not in ledger:
        raise WikiError(f"{picture} has no entry in {LEDGER}")
    if not reason.strip():
        raise WikiError("a blessing needs a reason; it is the record that someone actually looked")
    ledger[picture]["digest"] = subject_digest(root, ledger[picture].get("depicts", []))
    ledger[picture]["blessed"] = reason.strip()
    write_ledger(images_dir, ledger)
    return f"wiki: {picture} blessed -- {reason.strip()}"


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
        missing = len(MISSING.findall(prose)) + sum(1 for row in rows if row.get("missing"))
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
        print("wiki: %d page%s waiting on the owner, in the sidebar but not in search, the categories "
              "or the goals: %s"
              % (len(drafts), "" if len(drafts) == 1 else "s", ", ".join(drafts)))
    if not budget.get("calibrated"):
        print("wiki: these budgets are PROVISIONAL -- %d words a page, %d for the collected goals. "
              "Nobody has measured what this project's reader will actually read; until they have, the "
              "numbers are a guess that happens to be enforced. Set budget.calibrated in %s when they "
              "have." % (budget["page"], budget["goals"], CONFIG))

