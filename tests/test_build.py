"""The rules, each case breaking one of them.

A generator nobody has watched refuse anything is a generator that reports success. Every case here
builds a small wiki in a temporary directory, breaks exactly one rule, and asserts the tool names it --
plus the properties the whole scheme rests on: addresses that resolve wherever they are read, a build
that writes nowhere but its output, and a tool that names nothing about any project it documents.
"""

import http.client
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import tomllib
import unittest

from builder import build as wiki
from builder import cli, serve as serving
from builder.config import CONFIG, WikiError

# The installed package, wherever it is: the tests prove what a project gets, not what the source tree
# happens to hold.
PACKAGE = Path(wiki.__file__).resolve().parent


def wiki_version():
    import builder
    return builder.__version__

CONFIGURATION = """
[site]
name = "A Wiki"

[budget]
page = 500
intent = 120
goals = 3500
calibrated = true

[[section]]
title = "Navigation"
pages = ["index", "goals"]

[[section]]
title = "Things"
pages = ["thing"]

[tool]
version = "VERSION"
""".replace("VERSION", __import__("builder").__version__)

PAGE = '''+++
title = "A thing"
subtitle = "the thing, its speed and its ground"
categories = ["Things"]
status = "approved"
intent = """
A thing exists so that something else can happen. It should be plain what it is for.
"""

[[infobox]]
group = "Facts"
rows = [
  { label = "Held to", value = "a promise", guaranteed = "THING-001", cite = "why" },
  { label = "Today", value = "a number", cite = "why" },
]
+++

A thing does what it does.[^why]

## Speed

It does it slowly.[^why]

## Ground

Because speed would change it. {missing}

[^why]: The reason — `Source/Thing.h`.
'''

INDEX = '''+++
title = "Front"
subtitle = "the front"
goals = false
status = "approved"
intent = """
The front page exists to send a reader somewhere useful.
"""
+++

Go to [a thing](thing.md).
'''

GOALS = '''+++
title = "Goals"
subtitle = "every purpose"
goals = false
status = "approved"
intent = """
This page collects what each part is for.
"""
+++

What each part is for.
'''


class WikiTests(unittest.TestCase):
    """Each case breaks one rule and asserts the generator says which."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.pages = self.root / "docs/wiki/pages"
        self.pages.mkdir(parents=True)
        (self.root / "docs/wiki/images").mkdir(parents=True)
        self.write("index", INDEX)
        self.write("goals", GOALS)
        self.write("thing", PAGE)
        self.nav(CONFIGURATION)
        self.out = self.root / "out"
        self.budget = {"page": 500, "intent": 120, "goals": 3500, "calibrated": True}

    # --- helpers ---------------------------------------------------------------------------------

    def write(self, page_id, text):
        path = self.pages / (page_id + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def nav(self, text):
        (self.root / "docs/wiki" / CONFIG).write_text(text, encoding="utf-8")

    def build(self, audience="internal", today="2026-01-02"):
        # The day is given rather than taken from the clock, so a test says what it means.
        counts, goals_words, self.budget, self.drafts = wiki.build(
            self.root, self.out, audience, today=today)
        return counts, goals_words

    def refused(self, fragment):
        with self.assertRaises(wiki.WikiError) as caught:
            self.build()
        self.assertIn(fragment, str(caught.exception).lower(),
                      f"refused, but not for {fragment!r}: {caught.exception}")

    FORBIDDEN = ((r"\bticks?\b", "a tick count"),
                 (r"\d+\s*cm\b", "a measurement in centimetres"),
                 (r"\b[A-Z][A-Za-z]*/[A-Za-z/._-]+\.(?:h|cpp|py|ini|toml|md|json)\b", "a file path"),
                 (r"\b[A-Z]{3,}(?:-[A-Z]+)*-\d{3}\b", "a requirement identifier"),
                 (r"\bnot built yet\b", "a gap list"))

    @classmethod
    def technical_side(cls, site):
        """Every article carrying the builder's register, as sentences.

        The references are exempt and only they: naming a path is what they are for, and a user build
        carries neither them nor the marks that point into them. The source view is exempt for the same
        reason -- it exists to show the file.
        """
        offences = []
        for path in sorted(site.rglob("index.html")):
            if path.parent.name == "source":
                continue
            page = path.read_text(encoding="utf-8")
            if "<article" not in page:
                continue
            article = page[page.index("<article"):page.index("</article>")]
            prose = re.sub(r'<aside class="cites".*?</aside>', "", article, flags=re.S)
            prose = re.sub(r"<[^>]+>", " ", prose)
            for pattern, what in cls.FORBIDDEN:
                found = re.search(pattern, prose)
                if found:
                    offences.append(f"{path.parent.name or 'the front page'} carries {what}: "
                                    f"{found.group()!r}")
        return offences

    def emitted(self):
        return {path: path.read_text(encoding="utf-8")
                for path in sorted(self.out.rglob("*.html"))}

    def references(self):
        found = []
        for text in self.emitted().values():
            found += re.findall(r'(?:href|src)="([^"]*)"', text)
        return found

    # --- the page model --------------------------------------------------------------------------

    def test_front_matter_becomes_the_page(self):
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn("<h1>A thing</h1>", page)
        self.assertIn('<p class="sub">the thing, its speed and its ground</p>', page)

    def test_a_page_still_using_kicker_is_told_to_rename_it(self):
        # The subtitle was called kicker before. Reading it silently as nothing would lose every one.
        self.write("thing", PAGE.replace('subtitle = "the thing, its speed and its ground"', 'kicker = "the thing, its speed and its ground"'))
        self.refused("rename kicker to subtitle")

    def test_a_page_with_an_audience_the_build_does_not_know_is_refused(self):
        # The user audience was once called by a game's word. A page still using it is told, not quietly left
        # out of the user build.
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "player"'))
        self.refused('an audience is "internal" or "user"')

    def test_a_source_view_says_what_it_shows(self):
        self.build()
        source = (self.out / "thing/source/index.html").read_text(encoding="utf-8")
        self.assertIn('<p class="sub">markdown source of this page</p>', source)

    # An agent reads markdown far better than a rendered page, and a static host cannot choose between
    # the two by what the reader asks for, so each page sits beside a markdown copy of itself.

    def test_every_page_has_a_markdown_copy_for_agents(self):
        self.build()
        copy = (self.out / "thing/index.md").read_text(encoding="utf-8")
        self.assertTrue(copy.startswith("# A thing\n"), copy[:80])
        self.assertIn("A thing exists so that something else can happen.", copy)
        self.assertIn("It does it slowly.[^why]", copy)
        self.assertIn("[^why]: The reason — `Source/Thing.h`.", copy)
        self.assertNotIn("+++", copy)
        self.assertNotIn("<p>", copy)

    def test_a_page_link_in_a_markdown_copy_points_at_that_pages_copy(self):
        self.build()
        front = (self.out / "index.md").read_text(encoding="utf-8")
        self.assertIn("[a thing](thing/index.md)", front)

    def test_the_goals_copy_carries_the_collected_intents(self):
        self.build()
        goals = (self.out / "goals/index.md").read_text(encoding="utf-8")
        self.assertIn("A thing exists so that something else can happen.", goals)

    def test_a_page_names_its_markdown_copy_and_the_agent_index(self):
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="alternate" type="text/markdown" href="index.md">', page)
        self.assertIn('<link rel="describedby" href="../llms.txt">', page)

    def test_llms_txt_lists_every_page_by_its_markdown_copy(self):
        self.build()
        index = (self.out / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(index.startswith("# "), index[:60])
        self.assertIn("- [A thing](thing/index.md): the thing, its speed and its ground", index)

    def test_a_source_view_links_to_the_markdown_file(self):
        # A reader can open a page as pure markdown: its Source view links to the markdown file, in place of
        # a separate markdown tab.
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        source = (self.out / "thing/source/index.html").read_text(encoding="utf-8")
        self.assertIn('<a href="../index.md">index.md</a>', source)
        self.assertNotIn(">Markdown</a>", page, "the tab row still carries a Markdown tab")
        self.assertNotIn(">Markdown</a>", source, "the tab row still carries a Markdown tab")
        self.assertTrue((self.out / "thing/index.md").is_file())

    def test_a_user_build_has_no_markdown_copy_and_no_agent_index(self):
        # The copy is the page as written, references and marks included, which a user build withholds.
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "user"'))
        self.build("user")
        self.assertTrue((self.out / "thing/index.html").is_file())
        self.assertFalse((self.out / "thing/index.md").exists())
        self.assertFalse((self.out / "llms.txt").exists())

    def test_a_paragraph_that_states_something_and_cites_nothing_is_refused(self):
        """The rule the whole wiki rests on: a reader uses this instead of the source, so a sentence they
        cannot trace is one they must take on faith -- and it looks exactly like one that was checked."""
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "It does it slowly."))
        problems = wiki.uncited_problems(self.root)
        self.assertTrue(any("It does it slowly" in problem for problem in problems), problems)
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(1, status, "the gate would have passed an untraceable claim")
        self.assertIn("cites nothing", output)

    def test_the_mark_for_no_source_satisfies_the_rule(self):
        # "No source" is a fine answer. Silence is not.
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "It does it slowly. {missing}"))
        self.assertEqual([], wiki.uncited_problems(self.root))

    def test_a_sentence_riding_on_its_neighbours_citation_is_refused(self):
        """Every sentence states something, so every sentence says where it came from.

        One citation used to cover its whole paragraph, and a claim beside a cited one read exactly as
        though it had been checked.
        """
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "It does it slowly.[^why] It never hurries."))
        problems = wiki.uncited_problems(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("It never hurries", problems[0])

    def test_a_citation_after_the_full_stop_belongs_to_its_sentence(self):
        # Neither a version number nor an abbreviation ends a sentence.
        self.write("thing", PAGE.replace(
            "It does it slowly.[^why]",
            "It does it slowly.[^why] It needs version 3.11, e.g. the current one.[^why] It waits. {missing}"))
        self.assertEqual([], wiki.uncited_problems(self.root))

    def test_a_sentence_linking_to_another_page_needs_no_citation(self):
        # The page it links to carries the citations; a sentence that only points there has none of its own.
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "It does it slowly.[^why] How it began is on [the front](index.md)."))
        self.assertEqual([], wiki.uncited_problems(self.root))

    # Where one sentence ends and the next begins. Each case is a block and the statements it must split
    # into, exactly: a split in the wrong place lets an uncited sentence hide inside a cited one, or cuts
    # a cited sentence off from its own citation.
    SPLITS = (
        ("a citation after the full stop", "One.[^a] Two.[^b]", ["One.[^a]", "Two.[^b]"]),
        ("several citations after one full stop", "It cites twice.[^a][^b] Next one.",
         ["It cites twice.[^a][^b]", "Next one."]),
        ("a citation before the full stop", "It is fast[^a]. It is cheap.", ["It is fast[^a].", "It is cheap."]),
        ("a version number", "It needs 3.11 or newer.[^a]", ["It needs 3.11 or newer.[^a]"]),
        ("dotted versions", "Versions v0.1.0 and 1.2.3 stay whole.[^a]", ["Versions v0.1.0 and 1.2.3 stay whole.[^a]"]),
        ("an abbreviation", "Use e.g. the default, i.e. none.[^a]", ["Use e.g. the default, i.e. none.[^a]"]),
        ("a file name in code", "It reads `wiki.toml` first.[^a]", ["It reads `wiki.toml` first.[^a]"]),
        ("code ending a sentence", "It reads `wiki.toml`. Then it builds.[^a]",
         ["It reads `wiki.toml`.", "Then it builds.[^a]"]),
        ("a full stop and capital inside code", "It prints `done. Next` at the end.[^a]",
         ["It prints `done. Next` at the end.[^a]"]),
        ("exclamation and question marks", "It is fast! Is it safe? Yes.", ["It is fast!", "Is it safe?", "Yes."]),
        ("a closing quote", 'It says "stop." Then it stops.', ['It says "stop."', "Then it stops."]),
        ("bold", "**It is bold.** It is plain.", ["**It is bold.**", "It is plain."]),
        ("emphasis with underscores", "It is _done._ It is next.", ["It is _done._", "It is next."]),
        ("a closing parenthesis", "(It is cached.) It is served.", ["(It is cached.)", "It is served."]),
        ("the mark for no source", "It waits. {missing} It stops.[^a]", ["It waits. {missing}", "It stops.[^a]"]),
        ("a sentence starting with a digit", "It has 3 parts. 2 are cited.[^a]", ["It has 3 parts.", "2 are cited.[^a]"]),
        ("a wrapped line", "It spans\na wrapped line.[^a]", ["It spans a wrapped line.[^a]"]),
        ("list items", "- one item\n- another item", ["- one item", "- another item"]),
        ("numbered items", "1. first step\n2. second step", ["1. first step", "2. second step"]),
        ("a colon and a semicolon", "It is cheap; it is fast: both hold.[^a]", ["It is cheap; it is fast: both hold.[^a]"]),
        ("an ellipsis", "It waits... Then it goes.", ["It waits...", "Then it goes."]),
        ("a table, row by row, without its header", "| a | b |\n|---|---|\n| c | d |\n| e | f |",
         ["| c | d |", "| e | f |"]),
        ("a table with an aligned separator", "| a | b |\n|:--|--:|\n| c | d |", ["| c | d |"]),
        ("a table with only a header", "| a | b |\n|---|---|", []),
    )

    def test_a_block_splits_into_its_sentences(self):
        for case, block, expected in self.SPLITS:
            with self.subTest(case):
                self.assertEqual(expected, wiki.statements(block))

    # A body the check must pass or refuse, and the start of each sentence it must name.
    UNCITED = (
        ("a link to another page", "It is described on [the front](index.md).", []),
        ("a link to a section of another page", "It is on [the front](index.md#top).", []),
        ("a link off the site", "It is on [the web](https://example.com/page).", ["It is on [the web]"]),
        ("a link to a picture", "It looks like [this](../images/thing.png).", ["It looks like"]),
        ("a table with no citation", "| a | b |\n|---|---|\n| c | d |", ["| c | d |"]),
        ("a table with one citation", "| a | b |\n|---|---|\n| c[^why] | d |", []),
        # A table row needs at least one citation in any of its columns. One cited row no longer covers the
        # rows beside it.
        ("a cited row beside an uncited one", "| a | b |\n|---|---|\n| c[^why] | d |\n| e | f |", ["| e | f |"]),
        ("a citation in the last cell", "| a | b |\n|---|---|\n| c | d[^why] |", []),
        ("a row marked as having no source", "| a | b |\n|---|---|\n| c | d {missing} |", []),
        ("a row linking to another page", "| a | b |\n|---|---|\n| c | [the front](index.md) |", []),
        ("a row whose only mark is in code", "| a | b |\n|---|---|\n| c | `{missing}` |", ["| c |"]),
        ("a header that cites nothing", "| a | b |\n|---|---|\n| c[^why] | d |", []),
        ("a quotation", "> It is quoted.", ["> It is quoted."]),
        ("a child item under a cited one", "- It is cited.[^why]\n  - It is not.", ["- It is not."]),
        ("a horizontal rule", "---", []),
        ("code inside a cited sentence", "It prints `done. Next` at the end.[^why]", []),
        ("the mark in the middle", "It waits {missing} and then stops.", []),
        ("a cited sentence beside an uncited one", "It is cited.[^why] It is not.", ["It is not."]),
    )

    def test_each_sentence_is_held_to_its_own_citation(self):
        for case, prose, expected in self.UNCITED:
            with self.subTest(case):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", prose))
                problems = wiki.uncited_problems(self.root)
                named = [problem.split("“", 1)[1] for problem in problems]
                self.assertEqual(len(expected), len(problems), problems)
                for start, name in zip(expected, named):
                    self.assertTrue(name.startswith(start), f"expected {start!r}, got {name!r}")

    def line_of(self, page_id, fragment):
        """The line of a page's file a fragment starts on, counted independently of the tool."""
        text = (self.pages / (page_id + ".md")).read_text(encoding="utf-8")
        return text[:text.index(fragment)].count("\n") + 1

    def test_an_uncited_sentence_is_named_with_the_line_it_is_on(self):
        # Code with blank lines sits above it, and a heading, so a count that dropped them would be wrong.
        self.write("thing", PAGE.replace("## Ground", self.SAMPLE + "\nThis says something.\n\n## Ground"))
        problems = wiki.uncited_problems(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertTrue(problems[0].startswith("thing.md:%d: " % self.line_of("thing", "This says something")),
                        problems[0])

    def test_check_lists_every_claim_marked_as_having_no_source(self):
        """So the work left is a list a person or an agent can act on, not only a count."""
        self.write("thing", PAGE.replace('{ label = "Today", value = "a number", cite = "why" }',
                                         '{ label = "Today", value = "a number", missing = true }'))
        self.build()
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(0, status, "a claim marked as having no source is an answer, not a failure")
        self.assertIn("wiki: thing.md:%d: “Because speed would change it. {missing}” is marked as having no source"
                      % self.line_of("thing", "Because speed"), output)
        self.assertIn("wiki: thing.md:%d: the infobox row 'Today' is marked as having no source"
                      % self.line_of("thing", 'label = "Today"'), output)

    def test_a_paragraph_directly_under_its_heading_is_checked(self):
        self.write("thing", PAGE.replace("## Speed\n\nIt does it slowly.[^why]", "## Speed\nIt does it slowly."))
        problems = wiki.uncited_problems(self.root)
        self.assertTrue(any("It does it slowly" in problem for problem in problems), problems)

    def test_a_list_of_bare_links_states_nothing_to_cite(self):
        links = ("## Ground\n\n- [Host guide](https://example.com/guide)\n"
                 "- [Custom domains](https://example.com/domains/)\n")
        self.write("thing", PAGE.replace("## Ground\n\nBecause speed would change it. {missing}", links))
        self.assertEqual([], [p for p in wiki.uncited_problems(self.root) if "thing.md" in p])

    def test_a_sentence_around_an_outside_link_still_needs_a_citation(self):
        for text in ("- [Host guide](https://example.com/guide) serves every folder.",
                     "The [host guide](https://example.com/guide) says so."):
            with self.subTest(text=text):
                self.write("thing", PAGE.replace("Because speed would change it. {missing}", text))
                problems = wiki.uncited_problems(self.root)
                self.assertTrue(any("thing.md" in p and "cites nothing" in p for p in problems), problems)

    def test_a_page_about_the_wiki_itself_needs_no_citations(self):
        # index.md and goals.md carry `goals = false`: they describe no behaviour, so there is nothing
        # for them to cite and the rule would be noise.
        self.assertEqual([], [p for p in wiki.uncited_problems(self.root) if "index.md" in p])

    def test_a_heading_that_asks_a_question_is_refused(self):
        # "Where they go" is the writer wondering what belongs in the section. The reader wanted "Ground".
        for bad in ("Where they go", "How a forest spreads", "What an animal decides", "Why it matters"):
            with self.subTest(heading=bad):
                self.write("thing", PAGE.replace("## Speed", "## " + bad))
                problems = wiki.heading_problems(self.root)
                self.assertTrue(any(bad in problem for problem in problems), problems)

    def test_a_subtitle_that_asks_a_question_is_refused(self):
        # "what a person writes" names nothing. A subtitle says which things the page covers, so a reader
        # choosing between pages in search can tell them apart.
        for bad in ("what a person writes", "How a page sits on the screen", "where it lives", "why it exists"):
            with self.subTest(subtitle=bad):
                self.write("thing", PAGE.replace('subtitle = "the thing, its speed and its ground"',
                                                 'subtitle = "%s"' % bad))
                self.assertIn("thing.md: the subtitle %r asks a question; name the things the page covers" % bad,
                              wiki.heading_problems(self.root))

    def test_a_subtitle_that_names_what_the_page_covers_passes(self):
        for good in ("word limits for a page, an intent and the goals page", "however it is measured"):
            with self.subTest(subtitle=good):
                self.write("thing", PAGE.replace('subtitle = "the thing, its speed and its ground"',
                                                 'subtitle = "%s"' % good))
                self.assertEqual([], [problem for problem in wiki.heading_problems(self.root)
                                      if "subtitle" in problem])

    def test_a_heading_that_rates_its_own_contents_is_refused(self):
        for bad in ("Fast enough to matter", "Important details", "Overview"):
            with self.subTest(heading=bad):
                self.write("thing", PAGE.replace("## Speed", "## " + bad))
                self.assertTrue(wiki.heading_problems(self.root))

    def test_a_heading_that_names_its_contents_passes(self):
        for good in ("Water", "Predators", "Ground", "Hunting", "Breeding and splitting"):
            with self.subTest(heading=good):
                self.write("thing", PAGE.replace("## Speed", "## " + good))
                self.assertEqual([], wiki.heading_problems(self.root))

    def test_a_heading_that_points_at_the_page_is_refused(self):
        # "This site" names nothing in a contents box or a search result. The reader wanted "Domain".
        for bad in ("This site", "This repository", "Our setup", "These options", "Here"):
            with self.subTest(heading=bad):
                self.write("thing", PAGE.replace("## Speed", "## " + bad))
                problems = wiki.heading_problems(self.root)
                self.assertTrue(any(repr(bad) in problem and "points at" in problem for problem in problems),
                                problems)

    def test_a_heading_that_only_starts_like_a_demonstrative_passes(self):
        for good in ("Thistle", "Hereford", "Outcome"):
            with self.subTest(heading=good):
                self.write("thing", PAGE.replace("## Speed", "## " + good))
                self.assertEqual([], wiki.heading_problems(self.root))

    def test_a_name_in_the_front_matter_that_points_at_the_page_is_refused(self):
        cases = {
            "title": ('title = "A thing"', 'title = "This tool"', "the title 'This tool'"),
            "group": ('group = "Facts"', 'group = "Our facts"', "the infobox group 'Our facts'"),
            "label": ('label = "Today"', 'label = "This site"', "the infobox label 'This site'"),
        }
        for kind, (old, new, expected) in cases.items():
            with self.subTest(kind=kind):
                self.write("thing", PAGE.replace(old, new))
                problems = wiki.pointing_problems(self.root)
                self.assertTrue(any(problem.startswith("thing.md: " + expected) for problem in problems),
                                problems)

    def test_prose_that_points_at_the_project_is_refused_where_it_is_written(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "It does it slowly, as this repository does.[^why]"))
        problems = wiki.pointing_problems(self.root)
        self.assertIn("thing.md:%d: “It does it slowly, as this repository does.[^why]” points at the "
                      "project with 'this repository' instead of naming it; use its name"
                      % self.line_of("thing", "It does it slowly"), problems)

    def test_front_matter_prose_that_points_at_the_project_is_refused(self):
        for old, new, field in (
                ('subtitle = "the thing, its speed and its ground"', 'subtitle = "the tool that builds this wiki"', "subtitle"),
                ("It should be plain", "This site should make it plain", "intent")):
            with self.subTest(field=field):
                self.write("thing", PAGE.replace(old, new))
                problems = wiki.pointing_problems(self.root)
                self.assertTrue(any(problem.startswith("thing.md: the %s points at the project" % field)
                                    for problem in problems), problems)

    def test_prose_that_names_the_project_or_quotes_code_passes(self):
        for sentence in ("wiki-builder deploys its own wiki.[^why]",
                         "The message reads `not written by this tool`.[^why]",
                         "This page covers speed, and that wiki covers ground.[^why]",
                         "Thistle grows beside this pathway.[^why]"):
            with self.subTest(sentence=sentence):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", sentence))
                self.assertEqual([], wiki.pointing_problems(self.root))

    def test_a_reference_to_a_markdown_document_is_refused(self):
        self.write("thing", PAGE.replace("[^why]: The reason — `Source/Thing.h`.",
                                         "[^why]: The reason — [the design](../design.md)."))
        problems = wiki.citation_problems(self.root)
        self.assertEqual(["thing.md cites ../design.md, which is a document; a reference names the code that "
                          "does the thing, or an outside service's own documentation"], problems)

    def test_a_reference_to_an_outside_services_documentation_passes(self):
        # A reference may cite an outside service's own documentation for how that service behaves.
        self.write("thing", PAGE.replace(
            "[^why]: The reason — `Source/Thing.h`.",
            "[^why]: Host Docs — [Custom domains](https://docs.example.com/pages/custom-domains/): a\n"
            "    subdomain needs a `CNAME` record."))
        self.assertEqual([], wiki.citation_problems(self.root))

    def test_a_rule_attributed_to_a_person_is_refused_where_it_is_written(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         'It does it slowly. The owner, 2026-09-14: "make it slow".[^why]'))
        problems = wiki.attribution_problems(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertTrue(problems[0].startswith("thing.md:%d: " % self.line_of("thing", "It does it slowly")),
                        problems)
        self.assertIn("attributes a rule to a person; state the rule itself", problems[0])

    def test_an_intent_attributed_to_a_person_is_refused(self):
        self.write("thing", PAGE.replace("It should be plain what it is for.",
                                         'The owner said so. It should be plain what it is for.'))
        self.assertTrue(any(problem.startswith("thing.md: the intent attributes")
                            for problem in wiki.attribution_problems(self.root)))

    def test_an_approval_role_named_as_a_rule_passes(self):
        for text in ("Changing it needs the owner's approval.[^why]",
                     "The owner decides what changes.[^why]",
                     "Write `The owner, 2026-09-14:` nowhere.[^why]"):
            with self.subTest(text=text):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", text))
                self.assertEqual([], wiki.attribution_problems(self.root))

    def test_the_check_refuses_an_attribution_to_the_owner(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "The owner, 2026-09-14: slowly.[^why]"))
        problems, *_ = wiki.check(self.root)
        self.assertTrue(any("attributes a rule to a person" in problem for problem in problems), problems)

    def test_a_sentence_with_a_vague_actor_is_refused_where_it_is_written(self):
        # "Nobody has approved it" hides who. The page names the reader, the writer, an agent or the part that
        # acts.
        for word in ("nobody", "Somebody", "someone", "anyone", "everyone", "no one"):
            with self.subTest(word=word):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", "It does it slowly for %s.[^why]" % word))
                problems = wiki.vague_actor_problems(self.root)
                self.assertEqual(1, len(problems), problems)
                self.assertTrue(problems[0].startswith("thing.md:%d: " % self.line_of("thing", "It does it slowly")))
                self.assertIn("says %r instead of naming who acts" % word.lower(), problems[0])

    def test_a_vague_actor_in_the_front_matter_is_refused(self):
        self.write("thing", PAGE.replace("It should be plain what it is for.", "Anyone should see what it is for."))
        self.assertTrue(any(problem.startswith("thing.md: the intent says 'anyone'")
                            for problem in wiki.vague_actor_problems(self.root)))

    def test_a_named_actor_or_code_passes(self):
        for text in ("The reader sees it slowly.[^why]",
                     "The writer approves it, and no reader can reach it.[^why]",
                     "The flag is `--nobody`.[^why]"):
            with self.subTest(text=text):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", text))
                self.assertEqual([], wiki.vague_actor_problems(self.root))

    def test_the_check_refuses_a_vague_actor(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "Somebody does it slowly.[^why]"))
        problems, *_ = wiki.check(self.root)
        self.assertTrue(any("instead of naming who acts" in problem for problem in problems), problems)

    def test_a_word_that_says_nothing_is_refused_where_it_is_written(self):
        # Words that mean nothing in documentation are refused.
        # One word from each list, each refused with the line it is on and what to write instead.
        cases = {
            "powerful": "say what it does",
            "Simply": "delete the word",
            "typically": "say what happens",
            "please note that": "keep the fact and drop the frame",
            "etc.": "give the whole list",
            "currently": "note at the end of the page",
            "a number of": "give the number",
            "the one": "name the thing",
            "the ones": "name the thing",
        }
        for word, fix in cases.items():
            with self.subTest(word=word):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", "It does it %s slowly.[^why]" % word))
                problems = wiki.empty_word_problems(self.root)
                self.assertEqual(1, len(problems), problems)
                self.assertTrue(problems[0].startswith("thing.md:%d: " % self.line_of("thing", "It does it")),
                                problems)
                self.assertIn("says %r" % word.lower(), problems[0])
                self.assertIn(fix, problems[0])

    def test_a_word_that_says_nothing_in_the_front_matter_is_refused(self):
        for old, new, place in (
                ('subtitle = "the thing, its speed and its ground"', 'subtitle = "a powerful thing"', "the subtitle"),
                ("It should be plain", "It should generally be plain", "the intent"),
                ('value = "a promise"', 'value = "a robust promise"', "the infobox value"),
                ('label = "Today"', 'label = "Currently"', "the infobox label")):
            with self.subTest(place=place):
                self.write("thing", PAGE.replace(old, new))
                problems = wiki.empty_word_problems(self.root)
                self.assertTrue(any(problem.startswith("thing.md: %s says" % place) for problem in problems),
                                problems)

    def test_an_infobox_value_that_says_nothing_is_refused(self):
        for value in ("yes", "Configurable", "varies", "depends"):
            with self.subTest(value=value):
                self.write("thing", PAGE.replace('value = "a number"', 'value = "%s"' % value))
                self.assertEqual(["thing.md: the infobox row 'Today' gives %r as its value, which a reader "
                                  "cannot check; give the default or the condition, or drop the row" % value],
                                 wiki.empty_word_problems(self.root))

    def test_a_word_with_a_plain_meaning_passes(self):
        # "may" grants permission, "just" can mean a moment ago, and "some" and "new" state facts: a word list
        # cannot tell those uses from empty ones, so they are left to the writer.
        for text in ("Either option may be given.[^why]",
                     "It shows what was just built.[^why]",
                     "Some pages are drafts, and a new page is one of them.[^why]",
                     "It lists every problem, not only the first, and a failure is unlikely.[^why]",
                     "The flag is `--simply`, and the value `yes` is quoted.[^why]",
                     "It sends the one-time code, and one is enough.[^why]"):
            with self.subTest(text=text):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", text))
                self.assertEqual([], wiki.empty_word_problems(self.root))

    def test_note_that_is_refused_only_as_a_frame(self):
        # "note" is also a noun, and a wiki about notes says "each note that is archived". The frame opens a
        # sentence or a clause, or follows please, also, to, should or must.
        for text in ("Note that it does it slowly.[^why]",
                     "It does it slowly; note that it waits.[^why]",
                     "Please note that it does it slowly.[^why]",
                     "It is important to note that it does it slowly.[^why]"):
            with self.subTest(text=text):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", text))
                problems = wiki.empty_word_problems(self.root)
                self.assertEqual(1, len(problems), problems)
                self.assertIn("which frames the fact", problems[0])
        for text in ("It keeps each note that is archived.[^why]",
                     "The note that it writes is short.[^why]",
                     "It keeps every archived note\nthat has a title.[^why]"):
            with self.subTest(text=text):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", text))
                self.assertEqual([], wiki.empty_word_problems(self.root))

    def test_the_check_refuses_a_word_that_says_nothing(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "It simply does it slowly.[^why]"))
        problems, *_ = wiki.check(self.root)
        self.assertTrue(any("says 'simply'" in problem for problem in problems), problems)

    def test_a_word_standing_in_for_a_thing_is_refused(self):
        # "anything" and "kept" both leave out the fact the sentence was for: which thing, and who keeps it.
        for word, fix in (("anything", "name the thing"), ("kept", "name who keeps it")):
            with self.subTest(word=word):
                self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                                 "It does %s slowly.[^why]" % word))
                problems = wiki.empty_word_problems(self.root)
                self.assertEqual(1, len(problems), problems)
                self.assertTrue(problems[0].startswith("thing.md:%d: " % self.line_of("thing", "It does")),
                                problems)
                self.assertIn("says %r" % word, problems[0])
                self.assertIn(fix, problems[0])

    def test_a_spelling_that_is_not_american_is_refused(self):
        # One English for every wiki, and the message names the word to write, not merely the word to drop.
        for word, american in (("behaviour", "behavior"), ("colour", "color"), ("labelled", "labeled"),
                               ("licence", "license"), ("organisation", "organization"),
                               ("summarises", "summarizes"), ("judgement", "judgment"),
                               ("towards", "toward"), ("grey", "gray"), ("analysed", "analyzed")):
            with self.subTest(word=word):
                self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                                 "It does the %s slowly.[^why]" % word))
                problems = wiki.plain_english_problems(self.root)
                self.assertEqual(1, len(problems), problems)
                self.assertTrue(problems[0].startswith("thing.md:%d: " % self.line_of("thing", "It does")),
                                problems)
                self.assertIn("says %r" % word, problems[0])
                self.assertIn("write %r" % american, problems[0])

    def test_a_word_people_do_not_say_is_refused(self):
        # Old and legal English reads as ceremony, and a reader who would not say the word aloud reads it
        # twice. Each is refused with the plain word that replaces it.
        for word, plain in (("whilst", "while"), ("amongst", "among"), ("hereby", "delete"),
                            ("notwithstanding", "even so"), ("shall", "will"), ("thus", "so"),
                            ("aforementioned", "name")):
            with self.subTest(word=word):
                self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                                 "It does %s it slowly.[^why]" % word))
                problems = wiki.plain_english_problems(self.root)
                self.assertEqual(1, len(problems), problems)
                self.assertIn("says %r" % word, problems[0])
                self.assertIn(plain, problems[0])

    def test_a_word_that_is_not_a_word_is_refused(self):
        # Not a spelling of anything: agents write it, and no dictionary has it.
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "It has fellen slowly.[^why]"))
        problems = wiki.plain_english_problems(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("is not a word", problems[0])
        self.assertIn("fallen", problems[0])

    def test_every_word_in_one_sentence_is_named_at_once(self):
        # With this many words listed, one refusal a run would have a writer fix a sentence, run the check
        # again, and meet the next word in the same sentence.
        self.write("thing", PAGE.replace(
            "It does it slowly.[^why]",
            "The colour is whilst it has fellen, centred amongst the licence.[^why]"))
        problems = wiki.plain_english_problems(self.root)
        self.assertEqual(6, len(problems), problems)
        for word in ("colour", "whilst", "fellen", "centred", "amongst", "licence"):
            with self.subTest(word=word):
                self.assertTrue(any("says %r" % word in problem for problem in problems), problems)

    def test_one_word_twice_in_a_sentence_is_named_once(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "The colour is the colour it was.[^why]"))
        self.assertEqual(1, len(wiki.plain_english_problems(self.root)))

    def test_a_word_a_suffix_rule_would_catch_passes(self):
        """The refused spellings are listed one by one, never matched by their ending.

        A rule on -ise takes raise, precise, promise, otherwise, surprise, advise, revise and exercise with
        it, and every one of those is correct and already on these pages. This is the case that fails the
        moment the list becomes a pattern.
        """
        for word in ("raise", "raises", "raised", "precise", "concise", "promise", "promises", "otherwise",
                     "surprise", "surprises", "advise", "revise", "revised", "exercise", "wise", "rise",
                     "rises", "disguise", "franchise", "supervise", "improvise", "merchandise", "demise",
                     "compromise", "arise", "paradise", "expertise", "premise", "likewise", "noise",
                     "practice", "license plate", "defense", "center", "color", "behavior", "gray",
                     "toward", "analyze", "organize", "judgment", "labeled"):
            with self.subTest(word=word):
                self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                                 "It does the %s slowly.[^why]" % word))
                self.assertEqual([], wiki.plain_english_problems(self.root),
                                 "%r is correct English and was refused" % word)

    def test_a_spelling_inside_code_passes(self):
        # A name the software owns is written the way the software spells it, however a page spells prose.
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "It calls `chartColours()` slowly.[^why]"))
        self.assertEqual([], wiki.plain_english_problems(self.root))

    def test_a_word_people_do_not_say_in_the_front_matter_is_refused(self):
        for old, new, place in (
                ('subtitle = "the thing, its speed and its ground"', 'subtitle = "the thing and its colour"',
                 "the subtitle"),
                ("It should be plain", "It shall be plain", "the intent"),
                ('value = "a promise"', 'value = "grey"', "the infobox value")):
            with self.subTest(place=place):
                self.write("thing", PAGE.replace(old, new))
                problems = wiki.plain_english_problems(self.root)
                self.assertTrue(any(problem.startswith("thing.md: %s says" % place) for problem in problems),
                                problems)

    def test_the_check_refuses_a_word_that_is_not_plain_english(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "It behaves whilst it does it slowly.[^why]"))
        problems, *_ = wiki.check(self.root)
        self.assertTrue(any("says 'whilst'" in problem for problem in problems), problems)

    def test_the_check_refuses_a_name_that_points_at_the_page(self):
        self.write("thing", PAGE.replace('label = "Today"', 'label = "This site"'))
        problems, *_ = wiki.check(self.root)
        self.assertTrue(any("'This site'" in problem for problem in problems), problems)

    SAMPLE ="Type it like this.[^why]\n\n```sh\nwiki build\n\n## What it prints\n```\n"

    def test_a_code_sample_is_not_prose(self):
        # A sample is the thing itself, not a claim about it: a blank line inside one does not start a
        # paragraph that cites nothing, and a line in one that starts with # is not a heading.
        self.write("thing", PAGE.replace("## Ground", self.SAMPLE + "\n## Ground"))
        self.assertEqual([], wiki.uncited_problems(self.root))
        self.assertEqual([], wiki.heading_problems(self.root))

    def test_prose_after_a_code_sample_is_still_checked(self):
        self.write("thing", PAGE.replace("## Ground", self.SAMPLE + "\nThis says something.\n\n## Ground"))
        problems = wiki.uncited_problems(self.root)
        self.assertTrue(any("This says something" in problem for problem in problems), problems)

    def test_a_page_with_no_intent_is_refused(self):
        self.write("thing", PAGE.replace('intent = """\nA thing exists so that something else can '
                                         'happen. It should be plain what it is for.\n"""', ""))
        self.refused("intent")

    def test_an_intent_longer_than_the_budget_is_refused(self):
        self.write("thing", PAGE.replace("A thing exists so that something else can happen.",
                                         "word " * 200))
        self.refused("intent")

    def test_a_page_in_no_navigation_section_is_refused(self):
        self.write("orphan", PAGE.replace("A thing", "An orphan"))
        self.refused("navigation section")

    def test_navigation_naming_a_page_that_does_not_exist_is_refused(self):
        self.nav(CONFIGURATION.replace('pages = ["thing"]', 'pages = ["thing", "ghost"]'))
        self.refused("does not exist")

    def test_navigation_naming_a_category_no_page_belongs_to_is_refused(self):
        self.nav(CONFIGURATION.replace('pages = ["thing"]',
                                       'pages = ["thing"]\ncategories = ["Nobody"]'))
        self.refused("no page belongs to")

    def test_a_page_may_not_be_called_source(self):
        self.write("source", PAGE)
        self.refused("source view")

    # --- the infobox -----------------------------------------------------------------------------

    def test_a_row_citing_a_requirement_carries_no_badge(self):
        # The requirement a row names is traceability for whoever next checks the page against the code.
        # It is never rendered, and neither is any mark saying the row has one.
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn("a promise", page)
        self.assertNotIn("Guaranteed", page)
        self.assertNotIn("chip", page)

    def test_a_requirement_identifier_never_reaches_an_article(self):
        # The article says what is guaranteed, never which requirement guarantees it. The source view is
        # the markdown itself, front matter and all, which is the point of it and is internal only.
        self.build()
        for path, text in self.emitted().items():
            if path.parent.name == "source":
                continue
            self.assertNotIn("THING-001", text, f"{path.name} shows a requirement identifier")

    def test_a_user_build_carries_no_requirement_identifier_anywhere(self):
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "user"'))
        self.build("user")
        for text in self.emitted().values():
            self.assertNotIn("THING-001", text)

    def test_a_row_with_no_source_is_marked_missing(self):
        self.write("thing", PAGE.replace('{ label = "Today", value = "a number", cite = "why" }',
                                         '{ label = "Today", value = "a number", missing = true }'))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn("nocite", page)
        self.assertIn("[?]", page)
        self.assertEqual([], wiki.infobox_problems(self.root), "a row marked missing needs no citation")

    def test_an_infobox_row_that_cites_nothing_is_refused(self):
        """A row states a fact in the most visible place on the page, so it is held to the prose's rule."""
        self.write("thing", PAGE.replace('{ label = "Today", value = "a number", cite = "why" }',
                                         '{ label = "Today", value = "a number" }'))
        problems = wiki.infobox_problems(self.root)
        self.assertTrue(any("'Today'" in p and "cites nothing" in p for p in problems), problems)
        self.build()
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(1, status, output)
        self.assertIn("cites nothing", output)

    def test_an_infobox_row_citing_a_reference_no_sentence_uses_is_refused(self):
        # Citing only a definition would let a row carry a fact the page itself never states.
        self.write("thing", PAGE.replace('{ label = "Today", value = "a number", cite = "why" }',
                                         '{ label = "Today", value = "a number", cite = "aside" }')
                   + "[^aside]: Defined, and cited by no sentence — `Source/Aside.h`.\n")
        problems = wiki.infobox_problems(self.root)
        self.assertTrue(any("'Today'" in p and "aside" in p for p in problems), problems)

    def test_an_infobox_citation_carries_the_texts_own_number(self):
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        infobox = page[page.index('<aside class="ib">'):page.index("</aside>")]
        self.assertIn('<sup class="ref">[<a href="#cite-1">1</a>]</sup>', infobox)

    def test_an_infobox_value_links_outside_the_wiki(self):
        self.write("thing", PAGE.replace('{ label = "Today", value = "a number", cite = "why" }',
                                         '{ label = "Today", value = "a number", cite = "why", '
                                         'link = "https://example.com/" }'))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<b>Today</b><span><a href="https://example.com/" class="ext" target="_blank" '
                      'rel="nofollow noopener noreferrer">a number</a>', page)

    def test_an_infobox_value_linking_inside_the_wiki_is_refused(self):
        # A row's link is written into the page as it stands, so a page address in one would resolve from
        # nowhere in particular. A page is linked from the text.
        self.write("thing", PAGE.replace('{ label = "Today", value = "a number", cite = "why" }',
                                         '{ label = "Today", value = "a number", cite = "why", link = "front.md" }'))
        self.refused("not an address outside the wiki")

    def test_a_user_build_carries_no_infobox_citation(self):
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "user"'))
        self.build("user")
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertNotIn("#cite-", page)

    def test_citation_counts_are_sources_cited_and_claims_marked_missing(self):
        # The fixture cites one source in its prose, marks one claim as having none, and cites that same
        # source from both infobox rows: a source counts once however often it is cited.
        self.assertEqual((1, 1), wiki.citation_counts(self.root)["thing"])
        self.write("thing", PAGE.replace('{ label = "Today", value = "a number", cite = "why" }',
                                         '{ label = "Today", value = "a number", missing = true }'))
        self.assertEqual((1, 2), wiki.citation_counts(self.root)["thing"])

    def test_every_build_and_check_prints_the_citation_counts(self):
        """So whoever runs the tool, person or agent, sees how much of the wiki is traced to the code."""
        for command in ("build", "check"):
            with self.subTest(command=command):
                _, output = self.run_main(["--root", str(self.root), command])
                self.assertRegex(output, r"wiki: thing\s+\d+ words\s+1 cited\s+1 missing")
                self.assertIn("wiki: 1 source cited, 1 claim marked as having no source", output)

    def test_a_code_block_carries_a_copy_button(self):
        # The same button the source view has, which the page's script already knows how to work.
        self.write("thing", PAGE.replace("## Ground", self.SAMPLE + "\n## Ground"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="srcbox"><button class="copy" type="button">Copy</button><pre><code', page)
        self.assertIn("</code></pre></div>", page)

    def test_an_outside_link_opens_in_a_new_tab_and_is_not_followed(self):
        links = "- [Host guide](https://example.com/guide)\n- [Other host](//example.org/)\n- [A thing](thing.md)\n"
        self.write("thing", PAGE.replace("## Ground", links + "\n## Ground"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        for address in ("https://example.com/guide", "//example.org/"):
            with self.subTest(address=address):
                self.assertIn('<a href="%s" class="ext" target="_blank" rel="nofollow noopener noreferrer">' % address, page)
        self.assertEqual(2, page.count('target="_blank"'), "only a link that leaves the wiki opens a new tab")

    def test_the_missing_mark_written_in_code_is_shown_as_written(self):
        # A page that teaches the mark, or a prompt that tells an agent to use it, shows it in code. Drawn
        # as a red mark there, the sample said something else and the page counted a claim it never made.
        sample = "Write `{missing}` after it.[^why]\n\n```text\nMark it {missing} when there is none.\n```\n"
        self.write("thing", PAGE.replace("## Ground", sample + "\n## Ground"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertEqual(1, page.count('class="ref nocite"'), "only the claim in the prose is marked")
        self.assertIn("<code>{missing}</code>", page)
        self.assertIn("Mark it {missing} when there is none.", page)
        self.assertEqual((1, 1), wiki.citation_counts(self.root)["thing"])
        self.assertEqual(1, sum("thing.md" in mark for mark in wiki.missing_marks(self.root)))

    def test_a_mark_shown_in_code_does_not_mark_its_sentence(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "It is written `{missing}` or `[^key]`."))
        problems = wiki.uncited_problems(self.root)
        self.assertTrue(any("It is written" in problem for problem in problems), problems)

    # A link to a page the wiki does not have: drawn red instead of blue, and refused by the dead link check.

    def test_a_link_to_a_page_the_wiki_does_not_have_is_drawn_red(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "It does it slowly, as [a gone page](gone.md) says.[^why]"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<a href="../gone/index.html" class="new" title="This page does not exist">a gone page</a>',
                      page)
        front = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="new"', front, "a link to a page that exists was drawn red")

    def test_the_check_names_a_link_to_a_page_the_wiki_does_not_have(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "It does it slowly, as [a gone\npage](gone.md#top) says.[^why]"))
        self.assertEqual(["thing.md:%d: links to gone.md#top, which is no page in the wiki; write that page, "
                          "or link to one that exists" % self.line_of("thing", "It does it slowly")],
                         wiki.dead_link_problems(self.root))
        problems, *_ = wiki.check(self.root)
        self.assertTrue(any("gone.md#top" in problem for problem in problems), problems)

    def test_a_link_that_is_not_to_a_missing_page_is_not_dead(self):
        for text in ("See [the front](index.md).[^why]",
                     "Type `[x](gone.md)` for a link.[^why]",
                     "A sample.[^why]\n\n```markdown\n[x](gone.md)\n```",
                     "See [the notes](../../../README.md).[^why]",
                     "See [the web](https://example.com/gone.md).[^why]"):
            with self.subTest(text=text):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", text))
                self.assertEqual([], wiki.dead_link_problems(self.root))

    # Diagrams: flows and charts drawn from a ```mermaid block, the way GitHub draws them.

    DIAGRAM = "It flows.[^why]\n\n```mermaid\nflowchart LR\n  a --> b{ok?}\n  b -- yes --> c\n```\n"

    def test_a_mermaid_block_is_drawn_as_a_diagram(self):
        self.write("thing", PAGE.replace("## Ground", self.DIAGRAM + "\n## Ground"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<pre class="mermaid">flowchart LR\n  a --&gt; b{ok?}\n  b -- yes --&gt; c\n</pre>', page)
        self.assertNotIn("language-mermaid", page, "the diagram was left as a code sample")
        # Mermaid is several megabytes, so the page names it for its script to fetch when a diagram nears the
        # screen, and never loads it with a tag that holds up every script after it.
        self.assertIn('<script>const WIKI_MERMAID="../assets/%s";</script>' % wiki.MERMAID, page)
        self.assertNotIn('<script src="../assets/%s"' % wiki.MERMAID, page)
        self.assertTrue((self.out / "assets" / wiki.MERMAID).is_file())

    def test_a_diagram_leaves_the_page_whole(self):
        # The code-block box closed after every </pre>, the diagram's included, and that stray </div> ended
        # the article at the diagram: everything below it fell out of the page.
        self.write("thing", PAGE.replace("## Ground", self.SAMPLE + "\n" + self.DIAGRAM + "\n## Ground"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("<div"), page.count("</div>"), "a diagram left the page's boxes unbalanced")
        self.assertIn('<pre class="mermaid">flowchart LR', page)
        self.assertEqual(1, page.count('<button class="copy"'), "only the code sample is a code block")
        article = page[page.index('<article class="art">'):page.index("</article>")]
        self.assertIn("Because speed would change it.", article, "the text after the diagram left the article")

    def test_a_page_without_a_diagram_loads_no_diagram_script(self):
        self.write("thing", PAGE.replace("## Ground", self.DIAGRAM + "\n## Ground"))
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertNotIn(wiki.MERMAID, front)

    def test_a_wiki_with_no_diagram_ships_no_diagram_script(self):
        self.write("thing", PAGE.replace("## Ground", self.DIAGRAM + "\n## Ground"))
        self.build()
        self.write("thing", PAGE)
        self.build()
        self.assertFalse((self.out / "assets" / wiki.MERMAID).exists(), "the script outlived the last diagram")

    # Charts: the same block, drawing figures rather than boxes and arrows.

    CHARTS = ('xychart-beta\n  title "Requests a month"\n  x-axis [Jan, Feb]\n  y-axis "Requests" 0 --> 400\n'
              "  bar [120, 380]\n  line [120, 380]",
              'pie showData\n  title Plans in use\n  "Free" : 60\n  "Team" : 40',
              'quadrantChart\n  x-axis "Cheap" --> "Costly"\n  y-axis "Low value" --> "High value"\n'
              '  "A check": [0.3, 0.8]',
              "sankey-beta\nPages,Approved,30\nPages,Draft,10",
              'radar-beta\n  axis a["Speed"], b["Size"]\n  curve x["Today"]{3, 4}\n  max 5')

    def test_a_chart_block_is_drawn_like_any_other_diagram(self):
        """Every kind of mermaid block is a drawing, not a sample, whatever it draws.

        The build never reads a block's first word, and a check that did would leave every chart on a wiki
        showing its own source to the reader instead of the figures it draws.
        """
        for chart in self.CHARTS:
            kind = chart.split("\n")[0]
            with self.subTest(kind=kind):
                self.write("thing", PAGE.replace(
                    "## Ground", "It counts.[^why]\n\n```mermaid\n%s\n```\n\n## Ground" % chart))
                self.build()
                page = (self.out / "thing/index.html").read_text(encoding="utf-8")
                self.assertIn('<pre class="mermaid">%s\n' % kind, page)
                self.assertNotIn("language-mermaid", page, f"the {kind} block was left as a code sample")
                self.assertTrue((self.out / "assets" / wiki.MERMAID).is_file())

    def test_two_drawings_on_one_page_are_named_apart(self):
        """Mermaid names a drawing after the millisecond it began, and two charts begin in the same one.

        Sharing a name, the second is sized against the first: it keeps no height of its own and paints
        over the drawing above it. Numbered ids are what stop that, and a page with two charts is where it
        showed up -- two flowcharts are slow enough to land in different milliseconds and pass by luck.
        """
        self.write("thing", PAGE.replace(
            "## Ground", self.DIAGRAM + "\nIt counts.[^why]\n\n```mermaid\n%s\n```\n\n## Ground" % self.CHARTS[0]))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertEqual(2, page.count('<pre class="mermaid">'), "the page does not hold two drawings")
        script = (self.out / "assets/wiki.js").read_text(encoding="utf-8")
        settings = re.search(r"mermaid\.initialize\((.*?)\);", script, re.S)
        self.assertIsNotNone(settings, "the page's script does not set Mermaid up")
        self.assertIn("deterministicIds: true", settings.group(1),
                      "Mermaid names each drawing after the clock, so two charts collide")

    def test_a_chart_takes_the_pages_own_colours(self):
        """A chart is drawn in the wiki's colours, not Mermaid's, in either theme.

        Left to itself Mermaid draws a pie's first slice in very nearly the page's own black and puts an xy
        chart in a grey panel; a sankey's colours are fixed inside Mermaid where no setting reaches them, so
        the stylesheet paints over those instead.
        """
        self.write("thing", PAGE.replace(
            "## Ground", "It counts.[^why]\n\n```mermaid\n%s\n```\n\n## Ground" % self.CHARTS[0]))
        self.build()
        script = (self.out / "assets/wiki.js").read_text(encoding="utf-8")
        self.assertIn("themeVariables: chartColours(dark)", script,
                      "the drawing is left to Mermaid's own colours")
        for named in ("plotColorPalette", "pieSectionTextColor", "quadrantPointFill", "cScale"):
            with self.subTest(named=named):
                self.assertIn(named, script)
        # A sankey is painted from a scheme inside Mermaid, so the page swaps those colours for its own once
        # the drawing is done, which keeps each band the gradient Mermaid drew it as.
        self.assertIn("recolourFlows", script, "a sankey keeps Mermaid's own colours")
        style = (self.out / "assets/wiki.css").read_text(encoding="utf-8")
        self.assertIn("mix-blend-mode:normal !important", style,
                      "a sankey's bands are multiplied into the page, which blacks them out on a dark one")

    def test_a_diagram_stays_mermaid_in_the_markdown_copy(self):
        self.write("thing", PAGE.replace("## Ground", self.DIAGRAM + "\n## Ground"))
        self.build()
        copy = (self.out / "thing/index.md").read_text(encoding="utf-8")
        self.assertIn("```mermaid\nflowchart LR\n  a --> b{ok?}\n", copy)

    # The footer: each page's word count, reading time and citation counts, generated by the build.

    def footer(self, page_id="thing"):
        page = (self.out / page_id / "index.html").read_text(encoding="utf-8")
        return page[page.index('<div class="foot">'):page.index("</div>", page.index('<div class="foot">'))]

    def test_a_page_footer_carries_its_own_counts(self):
        counts, _ = self.build()
        footer = self.footer()
        self.assertIn("%d words" % counts["thing"], footer)
        self.assertIn("about 1 minute to read", footer)
        self.assertIn("1 source cited", footer)
        self.assertIn("1 claim with no source", footer)

    def test_a_footer_counts_in_the_plural(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "It does it slowly.[^how] {missing}")
                   .replace("[^why]: The reason", "[^how]: How — `Source/Thing.h`.\n[^why]: The reason"))
        self.build()
        footer = self.footer()
        self.assertIn("2 sources cited", footer)
        self.assertIn("2 claims with no source", footer)

    def test_reading_time_is_counted_at_the_pace_the_budget_assumes(self):
        # 500 words a page is meant to answer in about two minutes, so a minute is 250 words, rounded up.
        for words, minutes in ((0, 1), (1, 1), (250, 1), (251, 2), (500, 2), (501, 3)):
            with self.subTest(words=words):
                self.assertEqual(minutes, wiki.reading_minutes(words))

    def test_a_page_excused_from_citations_counts_none_in_its_footer(self):
        # A goals page, or any page excused from citations, has neither citation count in its footer. The
        # front page and the goals page both say goals = false.
        self.build()
        for path in (self.out / "index.html", self.out / "goals/index.html"):
            with self.subTest(page=path.parent.name or "index"):
                page = path.read_text(encoding="utf-8")
                footer = page[page.index('<div class="foot">'):page.index("</div>", page.index('<div class="foot">'))]
                self.assertIn(" words", footer)
                self.assertNotIn("cited", footer)
                self.assertNotIn("no source", footer)

    def test_a_user_footer_leaves_out_the_citation_counts(self):
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "user"'))
        self.build("user")
        footer = self.footer()
        self.assertIn(" words", footer)
        self.assertNotIn("cited", footer)
        self.assertNotIn("no source", footer)

    def test_a_markdown_table_is_drawn_as_a_wiki_table(self):
        # Without the class, a page's own table had no borders, no header row and no padding.
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "| a | b |\n|---|---|\n| c[^why] | d |"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="wt"><table class="w">', page)
        self.assertIn("</table></div>", page)
        self.assertNotIn("<table>", page)

    # --- tables the renderer will not draw ------------------------------------------------------

    SOUND_TABLE = "| a | b |\n|---|---|\n| c[^why] | d |"

    def table(self, rows):
        """A page whose one table is the rows given, in place of the page's second sentence."""
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "| a | b |\n|---|---|\n" + rows))
        return wiki.table_problems(self.root)

    def test_a_row_carrying_text_after_its_last_pipe_is_refused(self):
        """The mark landed past the closing pipe, the row fell out of the table, and the check stayed green.

        Every other check reads the markdown, where the row is still a row that cites its source, so a
        page could render as a paragraph of raw pipes and pass the gate that exists to stop exactly that.
        """
        problems = self.table("| c[^why] | d | {missing}")
        self.assertEqual(1, len(problems), problems)
        self.assertTrue(problems[0].startswith(
            "thing.md:%d: " % self.line_of("thing", "| c[^why] | d | {missing}")), problems[0])
        self.assertIn("carries text after its last |", problems[0])
        # The renderer really does drop it: the table is drawn with no body row at all.
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn("<tbody></tbody>", page.replace("\n", "").replace(" ", ""),
                      "the row did not fall out, so this is no longer the failure being caught")

    def test_a_row_with_the_wrong_number_of_cells_is_refused(self):
        # A ragged row does not lose only itself: the renderer throws the whole table away.
        for rows, says in (("| e[^why] |", "has 1 cell where its header has 2"),
                           ("| c[^why] | d | e |", "has 3 cells where its header has 2")):
            with self.subTest(rows=rows):
                problems = self.table(rows)
                self.assertEqual(1, len(problems), problems)
                self.assertIn(says, problems[0])
                self.assertIn("give the row 2 cells", problems[0])

    def test_a_sound_table_is_left_alone(self):
        # In one case with a broken one, so an empty result cannot pass for a check that ran.
        self.assertEqual([], self.table("| c[^why] | d |"))
        self.assertNotEqual([], self.table("| c[^why] | d | e |"),
                            "the check found nothing wrong with a table the renderer refuses")

    def test_a_table_in_a_code_sample_is_not_checked(self):
        # A sample showing a broken table is the thing itself, not a claim, and the renderer never sees it.
        broken = "```md\n| a | b |\n|---|---|\n| e |\n```"
        self.write("thing", PAGE.replace("It does it slowly.[^why]", broken))
        self.assertEqual([], wiki.table_problems(self.root))
        self.write("thing", PAGE.replace("It does it slowly.[^why]", broken.replace("```md\n", "").replace("\n```", "")))
        self.assertNotEqual([], wiki.table_problems(self.root), "the same table outside a fence passed")

    def test_a_broken_table_is_found_on_a_wiki_that_also_has_written_ones(self):
        """The health table and a family's member table are written after the page is rendered.

        The check renders each page's own markdown, so neither is in what it counts. What this proves is
        that a wiki carrying both still has a page's own broken table named, and that the written tables
        raise nothing of their own.
        """
        # [family] goes after the last top-level key: put in the middle, it swallows the keys below it
        # into its own table, and the page silently stops having an intent or a family at all.
        family = ('"""\n\n[family]\nheadings = ["Speed", "Ground"]\nlabels = ["Held to", "Today"]\n'
                  'table = ["Held to"]')
        self.write("health", INDEX.replace("Front", "Health").replace("the front", "every page"))
        self.nav(CONFIGURATION.replace('pages = ["index", "goals"]', 'pages = ["index", "goals", "health"]')
                 .replace('pages = ["thing"]', 'pages = ["thing"]'))
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "{family-table}")
                   .replace('"""\n\n[[infobox]]', family + "\n\n[[infobox]]", 1))
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        # Both tables are really on the built pages, or this proves nothing about leaving them out.
        self.assertIn('class="w family"', (self.out / "thing/index.html").read_text(encoding="utf-8"),
                      "the family table was not drawn, so the case does not cover it")
        self.assertIn('class="w health"', (self.out / "health/index.html").read_text(encoding="utf-8"),
                      "the health table was not drawn, so the case does not cover it")
        self.assertEqual([], wiki.table_problems(self.root))
        # And a page's own broken table is still found on the same wiki.
        self.write("thing/part", PAGE.replace("A thing", "A part")
                   .replace("It does it slowly.[^why]", "| a | b |\n|---|---|\n| e |"))
        problems = wiki.table_problems(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertTrue(problems[0].startswith("thing/part.md:"), problems[0])

    def test_check_names_a_table_the_renderer_will_not_draw(self):
        # Through the command, because the gate is what a project runs.
        self.table("| c[^why] | d | {missing}")
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(1, status, output)
        self.assertIn("carries text after its last |", output)

    def test_a_count_of_one_is_singular(self):
        # "1 pages written" and "1 problems" were printed by every one-page build and one-problem check.
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"'))
        _, output = self.run_main(["--root", str(self.root), "user", str(self.out)])
        self.assertIn("wiki: 1 page written to", output)
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "It does it slowly."))
        self.build()
        _, output = self.run_main(["--root", str(self.root), "check"])
        self.assertRegex(output, r"wiki: 3 pages, 1 problem\n")

    # --- citations -------------------------------------------------------------------------------

    def test_a_citation_is_a_numbered_superscript_and_a_numbered_reference(self):
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<sup class="ref">[<a href="#cite-1">1</a>]</sup>', page)
        self.assertIn('<li id="cite-1">', page)
        self.assertIn("Source/Thing.h", page)

    # --- addresses -------------------------------------------------------------------------------

    def test_a_published_build_has_no_html_in_any_address(self):
        # The rule still holds where it matters -- on a host. The default build is opened off disk as
        # well as served, and a browser handed a directory over file:// lists it instead of showing the
        # page, so its links say index.html on purpose.
        wiki.build(self.root, self.out, "internal", links="clean")[:2]
        self.assertEqual([], [ref for ref in self.references() if ".html" in ref])

    def published_addresses(self, audience="internal", links="clean"):
        """The addresses and days sitemap.xml lists, in the order it lists them."""
        import xml.etree.ElementTree as ElementTree
        wiki.build(self.root, self.out, audience, links=links, today="2026-01-02", sitemap=True)
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = ElementTree.parse(self.out / wiki.SITEMAP).getroot().findall("s:url", namespace)
        return [(url.findtext("s:loc", namespaces=namespace), url.findtext("s:lastmod", namespaces=namespace))
                for url in urls]

    def test_a_published_wiki_lists_its_approved_pages_in_a_sitemap(self):
        # A search engine finds every page from one file, so each page is listed at the full address a host
        # serves it from, with the day it last changed. A draft is not listed, and nor is a Source view.
        self.nav(CONFIGURATION.replace('name = "A Wiki"', 'name = "A Wiki"\nurl = "https://docs.example.org/"'))
        self.write("thing/proposal", PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal"))
        self.assertEqual([("https://docs.example.org/", "2026-01-02"),
                          ("https://docs.example.org/category/things/", None),
                          ("https://docs.example.org/goals/", "2026-01-02"),
                          ("https://docs.example.org/thing/", "2026-01-02")],
                         self.published_addresses())

    def test_a_user_build_lists_only_the_pages_marked_for_users_in_its_sitemap(self):
        self.nav(CONFIGURATION.replace('name = "A Wiki"', 'name = "A Wiki"\nurl = "https://docs.example.org"'))
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"'))
        self.assertEqual([("https://docs.example.org/category/things/index.html", None),
                          ("https://docs.example.org/thing/index.html", "2026-01-02")],
                         self.published_addresses("user", links="file"))

    def test_no_sitemap_is_written_without_an_address_or_for_reading_on_this_computer(self):
        wiki.build(self.root, self.out, "internal", links="clean", sitemap=True)
        self.assertFalse((self.out / wiki.SITEMAP).exists(), "a sitemap was written with no site.url")
        self.nav(CONFIGURATION.replace('name = "A Wiki"', 'name = "A Wiki"\nurl = "https://docs.example.org"'))
        self.build()
        self.assertFalse((self.out / wiki.SITEMAP).exists(), "wiki build wrote a sitemap")

    def test_a_site_address_that_is_not_a_full_address_is_refused(self):
        self.nav(CONFIGURATION.replace('name = "A Wiki"', 'name = "A Wiki"\nurl = "docs.example.org"'))
        self.refused("site.url")

    def test_a_published_build_still_puts_every_page_in_its_own_directory(self):
        wiki.build(self.root, self.out, "internal", links="clean")[:2]
        self.assertTrue((self.out / "thing/index.html").is_file())
        self.assertIn('href="thing/"', (self.out / "index.html").read_text(encoding="utf-8"))

    def test_no_emitted_reference_is_absolute(self):
        self.build()
        offenders = [ref for ref in self.references() if ref.startswith("/")]
        self.assertEqual([], offenders)

    def test_a_page_is_a_directory_holding_an_index(self):
        self.build()
        self.assertTrue((self.out / "thing/index.html").is_file())
        self.assertFalse((self.out / "thing.html").exists())

    def test_a_link_between_pages_resolves_wherever_it_is_read(self):
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="thing/index.html"', front)

    # --- what an agent may not decide ---------------------------------------------------------------

    def draft(self):
        """A proposal nobody has approved, listed in the navigation like any other page."""
        self.write("proposal", PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal"))
        self.nav(CONFIGURATION.replace('pages = ["thing"]', 'pages = ["thing", "proposal"]'))

    def test_a_page_is_a_draft_unless_it_says_otherwise(self):
        """An agent may write a page. Deciding that it belongs in the wiki needs approval."""
        self.draft()
        self.build()
        self.assertIn("proposal", self.drafts)

    def test_a_draft_is_built_so_it_can_be_read(self):
        self.draft()
        self.build()
        self.assertTrue((self.out / "proposal/index.html").is_file())

    def test_a_draft_says_it_is_one_before_it_says_anything_else(self):
        self.draft()
        self.build()
        page = (self.out / "proposal/index.html").read_text(encoding="utf-8")
        banner = '<p class="hat draft"><b>Draft</b> — not approved yet.</p>'
        self.assertIn(banner, page)
        self.assertLess(page.index(banner), page.index("<h2"))
        self.assertNotIn("read it as a proposal", page)

    def test_the_copy_for_agents_says_a_draft_is_one(self):
        self.draft()
        self.build()
        copy = (self.out / "proposal/index.md").read_text(encoding="utf-8")
        self.assertIn("**Status.** Draft, not approved yet.", copy)
        self.assertNotIn("has not been approved yet", copy)

    def test_a_draft_is_in_the_sidebar(self):
        """Every page is in the navigation, whatever its status."""
        self.draft()
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        sidebar = front[front.index('<div id="nav">'):front.index("</nav>")]
        self.assertIn('href="proposal/index.html"', sidebar)

    def test_a_draft_is_not_offered_by_search(self):
        # The sidebar shows every page; search, like the categories and the goals, offers approved ones.
        self.draft()
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        index = front[front.index("const WIKI_INDEX="):]
        self.assertNotIn("proposal/", index[:index.index("</script>")])

    def test_search_names_the_pages_above_a_child_page(self):
        # A child page's title names only what sets it apart within its parent, so two children can share
        # one; each result says where its page sits.
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        start = front.index("const WIKI_INDEX=") + len("const WIKI_INDEX=")
        index = json.loads(front[start:front.index(";</script>", start)])
        by_title = {entry["t"]: entry for entry in index}
        self.assertEqual("A thing", by_title["A part"]["p"])
        self.assertEqual("", by_title["A thing"]["p"])

    def test_a_title_cannot_break_out_of_the_search_index(self):
        # Every page carries the search index inside a script. A title that closed that script would run a
        # script of its own on every page, so the index is written with its angle brackets escaped.
        self.write("thing", PAGE.replace('title = "A thing"',
                                         'title = "A </script><script>alert(1)</script> thing"'))
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        script = front[front.index("const WIKI_INDEX="):]
        script = script[:script.index("</script>")]
        self.assertNotIn("<", script)
        self.assertIn("\\u003c/script\\u003e", script)

    def test_html_written_in_a_page_is_shown_as_text(self):
        # A page is markdown. HTML written in it is shown as written and never run: a script in a page would
        # otherwise run for every reader of the published site.
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "It does it <script>alert(1)</script> slowly.[^why]"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_an_infobox_group_marked_internal_is_left_out_of_a_user_build(self):
        # A group takes the page's audience unless it names its own, so a page for users can keep one group
        # of internal facts out of what users see.
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"')
                   .replace(']\n+++\n', ']\n\n[[infobox]]\ngroup = "Internals"\naudience = "internal"\nrows = [\n'
                                        '  { label = "Table", value = "things", cite = "why" },\n]\n+++\n'))
        self.build()
        internal = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="grp">Internals</div>', internal)
        self.build("user")
        user = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="grp">Facts</div>', user)
        self.assertNotIn('<div class="grp">Internals</div>', user, "an internal group reached a user build")

    def test_a_draft_for_users_is_built_for_users_under_its_banner(self):
        user = 'categories = ["Things"]\naudience = "user"'
        self.write("thing", PAGE.replace('categories = ["Things"]', user))
        self.write("thing/part", PAGE.replace('status = "approved"\n', "").replace("A thing", "A part")
                   .replace('categories = ["Things"]', user))
        self.build("user")
        part = self.out / "thing/part/index.html"
        self.assertTrue(part.is_file(), "a draft marked for users was left out of the user build")
        self.assertIn('<p class="hat draft"><b>Draft</b> — not approved yet.</p>', part.read_text(encoding="utf-8"))

    def test_a_github_address_puts_a_github_link_beside_the_site_name(self):
        # The link opens the project's GitHub page in a new tab, on every page, and a user build keeps it.
        self.nav(CONFIGURATION.replace('name = "A Wiki"', 'name = "A Wiki"\ngithub = "https://github.com/example/project"'))
        link = ('<a class="github" href="https://github.com/example/project" target="_blank" '
                'rel="noopener noreferrer" aria-label="GitHub" title="GitHub">')
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn(link, page)
        self.assertIn("<svg", page[page.index(link):])
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"'))
        self.build("user")
        self.assertIn(link, (self.out / "thing/index.html").read_text(encoding="utf-8"))

    def test_no_github_link_is_drawn_without_a_github_address(self):
        self.build()
        self.assertNotIn('class="github"', (self.out / "thing/index.html").read_text(encoding="utf-8"))

    def test_a_github_address_that_is_not_a_full_address_is_refused(self):
        self.nav(CONFIGURATION.replace('name = "A Wiki"', 'name = "A Wiki"\ngithub = "github.com/example/project"'))
        self.refused("site.github")

    def test_a_page_starts_in_the_light_theme(self):
        # Light is the theme a reader sees until they choose Dark or Auto, even with scripts turned off.
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="en" data-theme="light">', page)
        self.assertIn('<button class="theme" type="button" title="Light, dark, or follow the system">Light</button>',
                      page)

    def test_a_draft_is_not_in_the_collected_goals(self):
        self.write("proposal", PAGE.replace('status = "approved"\n', "")
                   .replace("A thing exists so that something else can happen.", "A proposal is made."))
        self.nav(CONFIGURATION.replace('pages = ["thing"]', 'pages = ["thing", "proposal"]'))
        self.build()
        goals = (self.out / "goals/index.html").read_text(encoding="utf-8")
        self.assertNotIn("A proposal is made.", goals)

    def test_the_goals_date_moves_only_when_the_collected_goals_do(self):
        # The goals page shows each approved page's title and intent, in sidebar order. A draft is not on
        # it, so editing a draft's intent leaves the goals page's date where it was.
        draft = PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal")
        self.write("proposal", draft)
        self.nav(CONFIGURATION.replace('pages = ["thing"]', 'pages = ["thing", "proposal"]'))
        self.build(today="2026-01-02")
        self.write("proposal", draft.replace("It should be plain what it is for.", "It should be plainer."))
        self.build(today="2026-02-03")
        self.assertEqual("2026-01-02", wiki.read_dates(self.root / "docs/wiki")["goals"]["updated"],
                         "a draft's intent moved the goals page's date")
        self.write("thing", PAGE.replace('title = "A thing"', 'title = "A renamed thing"'))
        self.build(today="2026-03-04")
        self.assertEqual("2026-03-04", wiki.read_dates(self.root / "docs/wiki")["goals"]["updated"],
                         "a collected page's title changed and the goals page's date did not move")

    def test_a_draft_in_no_navigation_section_is_refused(self):
        # Every page is in the sidebar, so a draft nobody could reach is refused like any other page.
        self.write("proposal", PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal"))
        self.refused("navigation section")

    # --- opening it off disk ------------------------------------------------------------------------

    def test_a_file_build_links_to_files_and_resolves_on_disk(self):
        """The whole point: opened with no server, every link still goes somewhere.

        A browser given a directory over file:// lists it rather than serving its index, so a clean
        address is a dead link there. This build says index.html and means it.
        """
        wiki.build(self.root, self.out, "internal", links="file")[:2]
        checked, broken = 0, []
        for page in sorted(self.out.rglob("*.html")):
            for ref in set(re.findall(r'(?:href|src)="([^"]*)"',
                                      page.read_text(encoding="utf-8"))):
                if ref.startswith("#") or re.match(r"^[a-z]+:", ref):
                    continue
                checked += 1
                if not (page.parent / ref.split("#")[0].split("?")[0]).resolve().exists():
                    broken.append((page.name, ref))
        self.assertTrue(checked, "a check that resolved no references did not run")
        self.assertEqual([], broken)

    def test_the_stylesheet_is_addressed_by_its_contents(self):
        # Kept in both modes: it works from file:// and the dev server needs it, since no header can
        # evict a stylesheet a tab already holds.
        self.build()
        page = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertRegex(page, r'href="assets/wiki\.css\?v=[0-9a-f]{8}"')

    # --- sub-pages -------------------------------------------------------------------------------

    def test_a_page_in_a_subdirectory_keeps_its_path_in_its_address(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        self.assertTrue((self.out / "thing/part/index.html").is_file())
        self.assertTrue((self.out / "thing/part/source/index.html").is_file())
        self.assertTrue((self.out / "thing/index.html").is_file(),
                        "a page with children is still a page")

    def test_a_sub_page_links_to_a_page_above_it(self):
        self.write("thing/part", PAGE.replace("A thing does what it does.",
                                              "See [the thing](../thing.md)."))
        self.build()
        page = (self.out / "thing/part/index.html").read_text(encoding="utf-8")
        # From /thing/part/ the parent page is one level up, not a path back down to it.
        self.assertIn('<a href="../index.html">the thing</a>', page)

    def test_a_child_page_nests_under_its_parent_without_being_listed(self):
        # The navigation names "thing" and nothing else; the child appears because of where it lives.
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        nav = front[front.index('<div id="nav">'):front.index("</div></nav>")]
        self.assertIn('<a class="" href="thing/index.html">A thing</a><ul>', nav)
        self.assertIn('href="thing/part/index.html">A part</a>', nav)

    def test_a_grandchild_nests_two_deep(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.write("thing/part/bit", PAGE.replace("A thing", "A bit"))
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        nav = front[front.index('<div id="nav">'):front.index("</div></nav>")]
        self.assertIn('href="thing/index.html">A thing</a><ul>', nav)
        self.assertIn('href="thing/part/index.html">A part</a><ul>', nav)
        self.assertIn('href="thing/part/bit/index.html">A bit</a>', nav)

    def test_the_branch_holding_the_current_page_is_marked(self):
        # A reader on a child page sees which branch they are in: every page above theirs is marked, and so
        # is every list that holds it. A page outside the branch carries neither mark.
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.write("thing/part/bit", PAGE.replace("A thing", "A bit"))
        self.build()

        def nav_of(path):
            page = (self.out / path).read_text(encoding="utf-8")
            return page[page.index('<div id="nav">'):page.index("</div></nav>")]

        nav = nav_of("thing/part/bit/index.html")
        self.assertRegex(nav, r'<a class="up" href="[^"]*">A thing</a><ul class="here">')
        self.assertRegex(nav, r'<a class="up" href="[^"]*">A part</a><ul class="here">')
        self.assertRegex(nav, r'<a class="on" href="[^"]*">A bit</a>')

        nav = nav_of("thing/index.html")
        self.assertRegex(nav, r'<a class="on" href="[^"]*">A thing</a><ul class="here">')
        self.assertNotIn('class="up"', nav)

        nav = nav_of("index.html")
        self.assertNotIn('class="up"', nav)
        self.assertNotIn('class="here"', nav)

    def test_a_section_is_a_control_that_opens_and_shuts_it(self):
        """A section header is one button, so a long sidebar can be folded down to the parts in use.

        The key is the section's title slugged, not its position: a section added above another would
        otherwise take over what the reader had shut.
        """
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        nav = front[front.index('<div id="nav">'):front.index("</div></nav>")]
        self.assertIn('<h5 data-sec="things"><button type="button"', nav,
                      "a section header is not a control")
        self.assertIn("</button></h5><div class=\"fold\"><ul>", nav,
                      "a section's pages sit in nothing the slide can size")
        # The tree inside a section is untouched: a child still nests under its parent.
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        front = (self.out / "index.html").read_text(encoding="utf-8")
        nav = front[front.index('<div id="nav">'):front.index("</div></nav>")]
        self.assertIn('<a class="" href="thing/index.html">A thing</a><ul>', nav)

    def test_two_sections_with_one_title_are_refused(self):
        # The title is the key the browser remembers a section by, so two of them would shut together.
        self.nav(CONFIGURATION.replace('title = "Things"', 'title = "Navigation"'))
        self.refused("has two sections both titled")

    def test_a_section_with_no_title_is_refused(self):
        # An untitled section draws a line and a blank header, and has no key to be remembered by.
        self.nav(CONFIGURATION.replace('title = "Things"\n', ""))
        self.refused("has a section with no title")

    def test_the_page_carries_what_the_sidebar_remembers(self):
        """The shut sections are applied in the head, before the sidebar is parsed, so none of it flashes.

        The key carries the site's name because localStorage is shared by every wiki on one address, and
        by every page opened off disk, where two sections named alike would otherwise toggle together.
        """
        self.build()
        page = (self.out / "index.html").read_text(encoding="utf-8")
        head = page[:page.index("</head>")]
        self.assertIn("wiki-nav-shut:a-wiki", head, "the sidebar's state is not kept per wiki")
        self.assertIn("grid-template-rows:0fr", head, "the head does not shut a stored section")
        # Reloading is not arriving: a section the reader just shut would otherwise come back every time
        # they refreshed the page they shut it on.
        self.assertIn('"reload"', head, "a reload counts as arriving, so a shut section reopens")
        self.assertLess(page.index("wiki-nav-shut"), page.index('<div id="nav">'),
                        "the sidebar is drawn before its stored state is applied, so it flashes")

    def test_the_sidebar_keeps_its_state_and_its_place(self):
        # What the reader chose outlives a page change: which sections are shut, and where the list is
        # scrolled. pagehide covers a normal move and the back/forward cache; visibilitychange covers a
        # phone being put away, where pagehide may never fire.
        self.build()
        script = (self.out / "assets/wiki.js").read_text(encoding="utf-8")
        for needed in ("data-navkey", '"wiki-nav-scroll"', '"wiki-seen"', '"pagehide"',
                       '"visibilitychange"', "persisted"):
            with self.subTest(needed=needed):
                self.assertIn(needed, script)

    def test_a_shut_section_leaves_the_keyboard(self):
        # Clipped to no height, a shut section's links stay focusable and announced, and Tab walks into a
        # box the reader cannot see. The slide is CSS, so it costs no measured height in script.
        self.build()
        style = (self.out / "assets/wiki.css").read_text(encoding="utf-8")
        self.assertIn("grid-template-rows:0fr", style, "a section is not shut by the stylesheet")
        self.assertIn("visibility:hidden", style, "a shut section keeps its links focusable")

    def test_the_sidebar_names_the_release_that_built_the_site(self):
        """The foot of the sidebar says which release drew the page, and links the tool it came from.

        It sits outside the part that scrolls, so a reader deep in a long page list still has it, and a
        page built by an older release can be told from one built by a newer without reading wiki.toml.
        A reader outside the team sees it too: it carries no reference and names nothing internal.
        """
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "user"'))
        footer = ('<div class="railfoot"><a href="https://github.com/timothymarois/wiki-builder">'
                  "Wiki v%s</a></div>" % wiki.__version__)
        # A user build writes only the pages marked for users, so each audience is read where it lands.
        for audience, name in (("internal", "index.html"), ("user", "thing/index.html")):
            with self.subTest(audience=audience):
                self.build(audience)
                page = (self.out / name).read_text(encoding="utf-8")
                self.assertIn(footer, page,
                              "the sidebar does not name the release that built the site")
                # Outside #nav and inside the rail: in #nav it would scroll away with the pages.
                rail = page[page.index('<div class="rail-in">'):page.index("</div></nav>")]
                self.assertLess(rail.index('<div id="nav">'), rail.index('class="railfoot"'),
                                "the release sits inside the page list, so it scrolls away")

    def test_a_shut_section_takes_up_no_more_than_its_header(self):
        """The space under a section's pages collapses with the section, so a shut one is a row.

        A margin under the list, or padding inside it, sizes the grid track that the slide shuts, and
        left 14px below every shut section -- a sidebar of nine shut sections carried 126px of nothing.
        The space belongs to the last page instead, inside the box the slide clips.
        """
        self.build()
        style = (self.out / "assets/wiki.css").read_text(encoding="utf-8")
        self.assertIn(".fold > ul > li:last-child{margin-bottom:14px}", style,
                      "the space under a section is not on the last page in it")
        self.assertNotRegex(style, r"\.rail ul\{[^}]*margin:0 0 14px",
                            "the space under a section is back on the list, where the slide cannot shut it")
        self.assertNotRegex(style, r"\.fold > ul\{[^}]*padding-bottom",
                            "padding inside the list gives the shut section a height it cannot go under")

    def test_a_section_header_is_padded_evenly(self):
        # A shut section is a row on its own, and uneven padding left its name sitting high in it.
        self.build()
        style = (self.out / "assets/wiki.css").read_text(encoding="utf-8")
        self.assertIn("padding:8px var(--pad-r);", style, "a section header is not padded evenly")
        self.assertRegex(style, r"\.rail h5\{margin:0 calc\(-1 \* var\(--pad-r\)\) 0 ",
                         "the header keeps a bottom margin, which a shut section cannot shed")

    def test_a_child_page_shows_the_pages_above_it_as_a_trail(self):
        # A reader on a child page, on a narrow screen especially, sees where it sits and can climb back up.
        # A top page has nothing above it, so it shows no trail.
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.write("thing/part/bit", PAGE.replace("A thing", "A bit"))
        self.build()
        page = (self.out / "thing/part/bit/index.html").read_text(encoding="utf-8")
        self.assertRegex(page, r'<nav class="crumbs" aria-label="Breadcrumb"><a href="[^"]*">A thing</a> › '
                               r'<a href="[^"]*">A part</a> › <span aria-current="page">A bit</span></nav>')
        top = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="crumbs"', top)

    def test_a_trail_leaves_out_a_page_a_user_build_does_not_have(self):
        # The trail follows the sidebar: a page hidden from users is skipped, and with nothing left above a
        # page, no trail is shown at all.
        user = 'categories = ["Things"]\naudience = "user"'
        self.write("thing/part", PAGE.replace("A thing", "A part").replace('categories = ["Things"]', user))
        self.write("thing/part/bit", PAGE.replace("A thing", "A bit").replace('categories = ["Things"]', user))
        self.build("user")
        bit = (self.out / "thing/part/bit/index.html").read_text(encoding="utf-8")
        self.assertRegex(bit, r'<nav class="crumbs" aria-label="Breadcrumb"><a href="[^"]*">A part</a> › '
                              r'<span aria-current="page">A bit</span></nav>')
        self.assertNotIn(">A thing</a> ›", bit)
        part = (self.out / "thing/part/index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="crumbs"', part)

    def test_a_page_beneath_nothing_listed_is_still_refused(self):
        self.write("elsewhere/lost", PAGE.replace("A thing", "Lost"))
        self.refused("navigation section")

    # --- pictures --------------------------------------------------------------------------------

    def test_a_picture_with_no_entry_in_the_ledger_is_refused(self):
        self.write("thing", PAGE.replace("A thing does what it does.",
                                         "![A thing](thing.png)"))
        self.refused("pictures.toml")

    def test_a_picture_whose_subject_has_moved_is_reported(self):
        envelope = self.root / "SourceAssets/Kit/thing"
        envelope.mkdir(parents=True)
        (envelope / "asset.json").write_text(json.dumps({"v": 1}), encoding="utf-8")
        digest = wiki.subject_digest(self.root, ["SourceAssets/Kit/thing"])
        images = self.root / "docs/wiki/images"
        wiki.write_ledger(images, {"thing.png": {"depicts": ["SourceAssets/Kit/thing"],
                                                "digest": digest, "made": "by hand"}})
        self.assertEqual([], wiki.picture_problems(self.root))
        (envelope / "asset.json").write_text(json.dumps({"v": 2}), encoding="utf-8")
        problems = wiki.picture_problems(self.root)
        self.assertEqual(1, len(problems))
        self.assertIn("thing.png", problems[0])

    def test_blessing_a_picture_records_the_reason_and_clears_it(self):
        envelope = self.root / "SourceAssets/Kit/thing"
        envelope.mkdir(parents=True)
        (envelope / "asset.json").write_text(json.dumps({"v": 1}), encoding="utf-8")
        images = self.root / "docs/wiki/images"
        wiki.write_ledger(images, {"thing.png": {"depicts": ["SourceAssets/Kit/thing"],
                                                "digest": "sha256:stale", "made": "by hand"}})
        self.assertEqual(1, len(wiki.picture_problems(self.root)))
        wiki.bless(self.root, "thing.png", "the crown did not move")
        self.assertEqual([], wiki.picture_problems(self.root))
        self.assertIn("the crown did not move",
                      (images / wiki.LEDGER).read_text(encoding="utf-8"))

    def test_a_blessing_without_a_reason_is_refused(self):
        images = self.root / "docs/wiki/images"
        wiki.write_ledger(images, {"thing.png": {"depicts": [], "digest": "", "made": "by hand"}})
        with self.assertRaises(wiki.WikiError):
            wiki.bless(self.root, "thing.png", "   ")

    # --- the reading budget ----------------------------------------------------------------------

    def test_a_page_over_the_budget_is_reported(self):
        self.write("thing", PAGE + ("\n\nword " * self.budget["page"]))
        counts, goals_words = self.build()
        problems = wiki.budget_problems(counts, goals_words, self.budget)
        self.assertTrue(any("thing.md" in problem for problem in problems), problems)

    def test_a_page_inside_the_budget_is_not_reported(self):
        counts, goals_words = self.build()
        self.assertEqual([], wiki.budget_problems(counts, goals_words, self.budget))

    # --- audience --------------------------------------------------------------------------------

    def test_a_user_build_carries_no_internal_page(self):
        self.build("user")
        self.assertFalse((self.out / "thing/index.html").exists())

    def test_a_user_build_carries_no_source_view_no_citation_and_no_path(self):
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "user"'))
        self.build("user")
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertNotIn("Source/Thing.h", page)
        self.assertNotIn('class="cites"', page)
        self.assertNotIn('class="ref"', page)
        self.assertFalse((self.out / "thing/source/index.html").exists())

    def test_a_user_build_carries_no_missing_mark(self):
        # The red mark carries a title and an audience beside its class, so a pattern that expects the class
        # to end the tag misses it, and a user reads a mark the wiki promises they never see.
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "user"'))
        self.build("user")
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertNotIn("nocite", page)
        self.assertNotIn("[?]", page)

    # --- the build itself ------------------------------------------------------------------------

    def test_the_generator_never_writes_to_a_page(self):
        """It reads pages and writes the site. The one file it keeps under docs/wiki is the record of
        when each page last changed, which is bookkeeping and never a page."""
        def snapshot():
            return {path: path.read_bytes()
                    for path in sorted((self.root / "docs/wiki").rglob("*"))
                    if path.is_file() and path.name != wiki.DATES}

        before = snapshot()
        self.build()
        self.assertEqual(before, snapshot(), "the generator changed a file it only reads")
        self.assertTrue(any(path.suffix == ".md" for path in before), "nothing was being watched")

    def test_two_builds_of_one_wiki_are_identical(self):
        self.build()
        first = wiki.tree_digest(self.out)
        shutil.rmtree(self.out)
        self.build()
        self.assertEqual(first, wiki.tree_digest(self.out))

    def test_a_removed_page_leaves_nothing_behind(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        self.assertTrue((self.out / "thing/part/index.html").is_file())
        (self.pages / "thing/part.md").unlink()
        self.build()
        self.assertFalse((self.out / "thing/part").exists())

    def test_a_file_the_build_did_not_write_is_kept(self):
        # A host reads files placed beside the site by hand, such as a CNAME naming its domain. A build
        # deletes only what an earlier build wrote.
        self.build()
        (self.out / "CNAME").write_text("wiki.example.org\n", encoding="utf-8")
        (self.out / ".well-known").mkdir()
        (self.out / ".well-known/security.txt").write_text("Contact: mailto:a@example.org\n", encoding="utf-8")
        self.build()
        self.assertTrue((self.out / "CNAME").is_file(), "a rebuild deleted a file the build never wrote")
        self.assertTrue((self.out / ".well-known/security.txt").is_file())

    def test_a_build_record_naming_a_file_outside_the_site_deletes_nothing_there(self):
        # The record is text anyone can edit, so a name leading out of the site folder is not the build's.
        outside = self.root / "keep.txt"
        outside.write_text("kept", encoding="utf-8")
        self.build()
        record = self.out / wiki.BUILD_RECORD
        record.write_text(record.read_text(encoding="utf-8") + "../keep.txt\n", encoding="utf-8")
        self.build()
        self.assertTrue(outside.is_file(), "a rebuild deleted a file outside the site")

    def test_a_site_with_no_build_record_loses_its_stale_pictures(self):
        images = self.root / "docs/wiki/images"
        (images / "thing.png").write_bytes(b"\x89PNG\r\n")
        wiki.write_ledger(images, {"thing.png": {"depicts": [], "digest": "", "made": "by hand"}})
        self.write("thing", PAGE.replace("A thing does what it does.[^why]", "![A thing](../images/thing.png)"))
        self.build()
        (self.out / wiki.BUILD_RECORD).unlink()
        self.write("thing", PAGE)
        self.build()
        self.assertFalse((self.out / "images/thing.png").exists(), "a picture no page shows was left behind")

    def test_a_site_with_no_build_record_loses_only_what_a_build_writes(self):
        # A site written before builds kept a record still has its old pages cleared, and nothing else.
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        (self.out / wiki.BUILD_RECORD).unlink()
        (self.pages / "thing/part.md").unlink()
        (self.out / "CNAME").write_text("wiki.example.org\n", encoding="utf-8")
        self.build()
        self.assertFalse((self.out / "thing/part").exists(), "a page from the earlier build was left behind")
        self.assertTrue((self.out / "CNAME").is_file(), "a file the build never wrote was deleted")
        self.assertTrue((self.out / wiki.BUILD_RECORD).is_file(), "the build kept no record")

    def test_a_wiki_with_no_pages_is_a_failure_not_an_empty_site(self):
        for path in self.pages.glob("*.md"):
            path.unlink()
        self.refused("no pages")


    # --- the goals page --------------------------------------------------------------------------

    def test_the_goals_page_collects_every_intent_in_navigation_order(self):
        self.build()
        goals = (self.out / "goals/index.html").read_text(encoding="utf-8")
        self.assertIn("A thing exists so that something else can happen", goals)

    def test_the_goals_page_leaves_out_pages_that_state_no_goal(self):
        # index and goals both carry `goals = false`: they are about the wiki, not about the game.
        self.build()
        goals = (self.out / "goals/index.html").read_text(encoding="utf-8")
        self.assertNotIn("The front page exists to send a reader somewhere useful", goals)
        self.assertNotIn("This page collects what each part is for", goals)

    def test_the_goals_page_orders_intents_as_the_navigation_does(self):
        self.write("alpha", PAGE.replace(
            "A thing exists so that something else can happen.", "Alpha is first.").replace(
            "A thing", "Alpha"))
        self.write("omega", PAGE.replace(
            "A thing exists so that something else can happen.", "Omega is last.").replace(
            "A thing", "Omega"))
        self.nav(CONFIGURATION.replace('pages = ["thing"]', 'pages = ["omega", "thing", "alpha"]'))
        self.build()
        goals = (self.out / "goals/index.html").read_text(encoding="utf-8")
        self.assertLess(goals.index("Omega is last."), goals.index("Alpha is first."),
                        "the goals page is not in the order the sidebar puts them")

    def test_a_goals_page_over_its_budget_is_reported(self):
        # The page the whole scheme depends on being read in one sitting.
        for index in range(40):
            self.write("filler%d" % index, PAGE.replace(
                "A thing exists so that something else can happen. It should be plain what it is for.",
                "word " * 110).replace("A thing", "Filler %d" % index))
        self.nav(CONFIGURATION.replace('pages = ["thing"]',
                             'pages = ["thing", %s]'
                             % ", ".join('"filler%d"' % i for i in range(40))))
        counts, goals_words = self.build()
        self.assertGreater(goals_words, self.budget["goals"])
        problems = wiki.budget_problems(counts, goals_words, self.budget)
        self.assertTrue(any("collected goals" in problem for problem in problems), problems)

    # --- what a page must never carry --------------------------------------------------------------

    def test_no_article_carries_the_technical_side(self):
        """The promise the whole wiki rests on: an article is free of the builder's register.

        The citation block is exempt and only there -- it exists to name paths, and a user build has
        neither it nor the marks that point into it.
        """
        self.build()
        for offence in self.technical_side(self.out):
            self.fail(offence)

    def test_the_technical_side_check_catches_each_kind(self):
        """Proof the guard above has teeth: every register it forbids, put on a page on purpose."""
        for prose, what in (("It takes 40 ticks.", "a tick count"),
                            ("It moves 250 cm.", "centimetres"),
                            ("See Source/Thing.h for it.", "a file path"),
                            ("Promised by WILDLIFE-015.", "a requirement identifier"),
                            ("Hides are not built yet.", "a gap list")):
            with self.subTest(what=what):
                self.write("thing", PAGE.replace("It does it slowly.", prose))
                shutil.rmtree(self.out, ignore_errors=True)
                self.build()
                self.assertTrue(self.technical_side(self.out),
                                f"{what} passed the check that exists to catch it")

    # --- the rest of the page ----------------------------------------------------------------------

    def test_the_contents_box_numbers_its_sections(self):
        self.write("thing", PAGE + "\n\n## A third heading\n\nWords.\n\n### Beneath it\n\nMore.\n")
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="toc">', page)
        self.assertIn('<span class="tn">1</span>Speed', page)
        self.assertIn('<span class="tn">3.1</span>Beneath it', page,
                      "a sub-heading is not numbered beneath its section")
        self.assertIn('<h3 id="s3-1">', page)

    def test_a_category_page_lists_the_pages_in_it(self):
        self.build()
        category = (self.out / "category/things/index.html").read_text(encoding="utf-8")
        self.assertIn("1 page in this category", category)
        self.assertIn('href="../../thing/index.html"', category)
        article = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="cats">', article)
        self.assertIn('href="../category/things/index.html">Things</a>', article)

    def test_a_body_picture_becomes_a_figure_with_its_caption(self):
        images = self.root / "docs/wiki/images"
        (images / "thing.png").write_bytes(b"\x89PNG\r\n")
        wiki.write_ledger(images, {"thing.png": {"depicts": [], "digest": "", "made": "by hand"}})
        self.write("thing", PAGE.replace("A thing does what it does.[^why]",
                                         "![A thing, seen whole](../images/thing.png)"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<figure class="fig"><img src="../images/thing.png"', page)
        self.assertIn("<figcaption>A thing, seen whole</figcaption>", page)
        self.assertNotIn("<p><figure", page,
                         "a picture on its own line is still wrapped in a paragraph")
        self.assertTrue((self.out / "images/thing.png").is_file(), "the picture was not copied")

    def test_a_settings_file_that_is_not_utf8_is_a_sentence_not_a_traceback(self):
        (self.root / "docs/wiki" / CONFIG).write_bytes(CONFIGURATION.replace("A Wiki", "Caf\xe9").encode("latin-1"))
        self.refused("wiki.toml is unreadable")

    def test_an_unreadable_dates_file_is_a_sentence_not_a_traceback(self):
        (self.root / "docs/wiki" / wiki.DATES).write_text('["thing"]\nupdated = \n', encoding="utf-8")
        self.refused("updated.toml is unreadable")

    def test_an_unreadable_picture_record_is_a_sentence_not_a_traceback(self):
        (self.root / "docs/wiki/images" / wiki.LEDGER).write_text('["thing.png"\n', encoding="utf-8")
        self.refused("pictures.toml is unreadable")

    def test_a_picture_named_outside_the_images_folder_is_refused(self):
        # A build copies each picture into the site's images folder by the name its table carries. A name
        # that climbs out of the folder would copy any file in the project to wherever the name points.
        images = self.root / "docs/wiki/images"
        (self.root / "docs/wiki/secret.png").write_bytes(b"\x89PNG\r\n")
        wiki.write_ledger(images, {"../secret.png": {"depicts": [], "digest": "", "made": "by hand"}})
        self.refused("../secret.png")
        self.assertFalse((self.out / "secret.png").exists())

    def test_a_page_named_with_a_space_and_an_accent_is_linked_and_listed(self):
        # The markdown parser hands over a link already percent-encoded, so it is decoded before it is looked
        # up; encoded again, it would name a folder that does not exist.
        self.write("thing/café notes", PAGE.replace("A thing", "Café notes"))
        self.write("thing", PAGE.replace("A thing does what it does.[^why]",
                                         "A thing keeps [notes](thing/caf%C3%A9%20notes.md).[^why]"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('href="caf%C3%A9%20notes/index.html"', page)
        self.assertNotIn('href="caf%C3%A9%20notes/index.html"' + wiki.NEW_PAGE, page, "a page that exists is drawn red")
        self.assertNotIn("caf%25", page, "an address was percent-encoded twice")
        self.assertEqual([], wiki.dead_link_problems(self.root))
        self.assertIn("(thing/caf%C3%A9%20notes/index.md)", (self.out / wiki.AGENT_INDEX).read_text(encoding="utf-8"))

    def test_a_body_picture_named_with_a_space_is_found_and_carried(self):
        images = self.root / "docs/wiki/images"
        (images / "my pic.png").write_bytes(b"\x89PNG\r\n")
        wiki.write_ledger(images, {"my pic.png": {"depicts": [], "digest": "", "made": "by hand"}})
        self.write("thing", PAGE.replace("A thing does what it does.[^why]", "![A thing](<../images/my pic.png>)"))
        self.build()
        self.assertIn('src="../images/my%20pic.png"', (self.out / "thing/index.html").read_text(encoding="utf-8"))
        self.assertTrue((self.out / "images/my pic.png").is_file(), "the picture was not copied")

    def test_a_file_name_cannot_write_into_a_link_or_a_picture(self):
        # A page's address and a picture's are their file names, written into an href or a src. A name holding
        # a quote would add an attribute of its own, and one holding a colon would read as a scheme.
        images = self.root / "docs/wiki/images"
        picture = 'q" onerror="alert(3).png'
        (images / picture).write_bytes(b"\x89PNG\r\n")
        wiki.write_ledger(images, {picture: {"depicts": [], "digest": "", "made": "by hand"}})
        self.write("thing", PAGE.replace('status = "approved"', 'status = "approved"\nimage = %s' % json.dumps(picture)))
        self.write('thing/x" onmouseover="alert(1)', PAGE.replace("A thing", "A quoted part"))
        self.write("thing/javascript:alert(2)", PAGE.replace("A thing", "A scheme part"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn("A quoted part", page, "the page with a quote in its name is not in the sidebar")
        self.assertNotIn('onmouseover="', page)
        self.assertNotIn('onerror="', page)
        self.assertNotIn('href="javascript:', page)
        self.assertNotIn('"u":"javascript:', page)

    def test_a_picture_linked_to_a_file_outside_the_images_folder_is_refused(self):
        # Git keeps a symbolic link, and copying one copies what it points at: a picture linked to the
        # project's .env would publish the secrets in it.
        images = self.root / "docs/wiki/images"
        (self.root / ".env").write_text("TOKEN=secret", encoding="utf-8")
        (images / "diagram.png").symlink_to(self.root / ".env")
        wiki.write_ledger(images, {"diagram.png": {"depicts": [], "digest": "", "made": "by hand"}})
        self.write("thing", PAGE.replace("A thing does what it does.[^why]", "![A thing](../images/diagram.png)"))
        self.refused("outside the images folder")
        self.assertFalse((self.out / "images/diagram.png").exists(), "the linked file was published")

    def test_a_record_of_the_wrong_shape_is_a_sentence_not_a_traceback(self):
        wiki_dir = self.root / "docs/wiki"
        for name, content, fragment in ((wiki.DATES, b'thing = "x"\n', "updated.toml"),
                                        (wiki.DATES, b'["thing"]\nupdated = "caf\xe9"\n', "updated.toml"),
                                        ("images/" + wiki.LEDGER, b'"thing.png" = 5\n', "pictures.toml")):
            with self.subTest(name=name, content=content):
                (wiki_dir / name).write_bytes(content)
                try:
                    self.refused(fragment)
                finally:
                    (wiki_dir / name).unlink()

    def test_an_infobox_picture_that_is_not_one_name_is_refused(self):
        self.write("thing", PAGE.replace('status = "approved"', 'status = "approved"\nimage = ["a.png", "b.png"]'))
        self.refused("gives its image as")

    def test_cleanup_stops_at_a_linked_folder_inside_the_site(self):
        self.build()
        (self.out / "real").mkdir()
        (self.out / "real/only.txt").write_text("x", encoding="utf-8")
        (self.out / "linked").symlink_to(self.out / "real")
        record = self.out / wiki.BUILD_RECORD
        record.write_text(record.read_text(encoding="utf-8") + "linked/only.txt\n", encoding="utf-8")
        self.build()
        self.assertTrue((self.out / "linked").is_symlink(), "cleanup removed a linked folder")

    def test_every_picture_name_that_is_not_a_file_name_is_refused(self):
        images = self.root / "docs/wiki/images"
        for name in ("", ".", "..", "sub\\thing.png"):
            with self.subTest(name=name):
                wiki.write_ledger(images, {name: {"depicts": [], "digest": "", "made": "by hand"}})
                self.refused("not a file name")

    def test_a_recorded_picture_whose_file_is_gone_is_refused(self):
        wiki.write_ledger(self.root / "docs/wiki/images", {"gone.png": {"depicts": [], "digest": "", "made": "by hand"}})
        self.refused("gone.png, which is not in")

    def test_an_infobox_picture_is_carried_into_the_site(self):
        images = self.root / "docs/wiki/images"
        (images / "thing.png").write_bytes(b"\x89PNG\r\n")
        wiki.write_ledger(images, {"thing.png": {"depicts": [], "digest": "", "made": "by hand"}})
        self.write("thing", PAGE.replace('status = "approved"', 'status = "approved"\nimage = "thing.png"'))
        self.build()
        self.assertTrue((self.out / "images/thing.png").is_file(), "the infobox picture was not copied")

    def test_a_picture_shown_only_in_a_reference_stays_out_of_a_user_build(self):
        # A user build removes the references, so a picture shown only there is not carried.
        images = self.root / "docs/wiki/images"
        (images / "cited.png").write_bytes(b"\x89PNG\r\n")
        wiki.write_ledger(images, {"cited.png": {"depicts": [], "digest": "", "made": "by hand"}})
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"')
                   .replace("[^why]: The reason — `Source/Thing.h`.",
                            "[^why]: The reason — `Source/Thing.h`, ![as drawn](../images/cited.png)."))
        self.build()
        self.assertTrue((self.out / "images/cited.png").is_file(), "the full wiki did not carry the picture")
        self.build("user")
        self.assertFalse((self.out / "images/cited.png").exists(), "a picture only in a reference reached users")

    def test_a_build_carries_only_the_pictures_its_pages_show(self):
        # A user build leaves internal pages out, and the pictures only they show go with them.
        images = self.root / "docs/wiki/images"
        for name in ("shown.png", "internal.png", "unused.png"):
            (images / name).write_bytes(b"\x89PNG\r\n")
        wiki.write_ledger(images, {name: {"depicts": [], "digest": "", "made": "by hand"}
                                   for name in ("shown.png", "internal.png", "unused.png")})
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"')
                   .replace("A thing does what it does.[^why]", "![Shown](../images/shown.png)"))
        self.write("thing/part", PAGE.replace("A thing", "A part")
                   .replace("A part does what it does.[^why]", "![Internal](../../images/internal.png)"))
        self.build()
        self.assertEqual(["internal.png", "shown.png"],
                         sorted(path.name for path in (self.out / "images").iterdir()))
        self.build("user")
        self.assertEqual(["shown.png"], sorted(path.name for path in (self.out / "images").iterdir()))

    def test_an_infobox_picture_with_no_ledger_entry_is_refused(self):
        self.write("thing", PAGE.replace('subtitle = "the thing, its speed and its ground"',
                                         'subtitle = "the thing, its speed and its ground"\nimage = "absent.png"'))
        self.refused("pictures.toml")

    # --- PDFs --------------------------------------------------------------------------------------
    # A wiki keeps its PDFs in a files folder beside images. A build carries only the PDFs a page links, and
    # the check refuses a link that would be dead once published, or a PDF too large to publish.

    MEGABYTE = 1024 * 1024

    def pdf(self, name, size=3000):
        """A PDF of `size` bytes in the wiki's files folder, written sparse so a large one costs no disk."""
        path = self.root / "docs/wiki/files" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as stream:
            stream.write(b"%PDF-1.4\n")
            stream.truncate(size)
        return path

    def link_pdf(self, *targets):
        """The thing page, linking each target from one sentence."""
        links = ", ".join(f"[the policy {index}]({target})" for index, target in enumerate(targets, 1))
        self.write("thing", PAGE.replace("It does it slowly.[^why]", f"It does it slowly, as {links} say.[^why]"))

    def pdf_problems(self):
        """What `wiki check` says about links to PDFs, after a build has recorded the dates it would otherwise refuse.

        Only link refusals: a sentence quoted for citing nothing can hold a PDF's name too.
        """
        self.build()
        problems, *_ = wiki.check(self.root)
        return [problem for problem in problems if " links to " in problem and ".pdf" in problem]

    def test_a_build_carries_only_the_pdfs_its_pages_link(self):
        self.pdf("policy.pdf")
        self.pdf("unlinked.pdf")
        self.link_pdf("../files/policy.pdf")
        self.build()
        self.assertEqual(["policy.pdf"], sorted(path.name for path in (self.out / "files").iterdir()))
        self.write("thing", PAGE)
        self.build()
        self.assertFalse((self.out / "files").exists(), "a PDF no page links any more was left in the site")

    def test_a_pdf_linked_only_from_an_internal_page_stays_out_of_a_user_build(self):
        self.pdf("public.pdf")
        self.pdf("internal.pdf")
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"')
                   .replace("It does it slowly.[^why]", "It does it slowly, as [the terms](../files/public.pdf) say.[^why]"))
        self.write("thing/part", PAGE.replace("A thing", "A part")
                   .replace("It does it slowly.[^why]", "It does it slowly, as [the notes](../../files/internal.pdf) say.[^why]"))
        self.build("user")
        self.assertEqual(["public.pdf"], sorted(path.name for path in (self.out / "files").iterdir()))

    def test_a_link_to_a_pdf_outside_the_files_folder_is_refused(self):
        (self.root / "docs/wiki/policy.pdf").write_bytes(b"%PDF-1.4\n")
        self.link_pdf("../policy.pdf")
        self.assertEqual(["thing.md:%d: links to ../policy.pdf, which is outside the wiki's files folder and would "
                          "be dead once published; put policy.pdf in the files folder and link it as "
                          "../files/policy.pdf" % self.line_of("thing", "It does it slowly")],
                         self.pdf_problems())

    def test_a_link_to_a_pdf_that_does_not_exist_is_refused(self):
        self.link_pdf("../files/gone.pdf")
        self.assertEqual(["thing.md:%d: links to ../files/gone.pdf, which does not exist; put gone.pdf in the wiki's "
                          "files folder, or correct the link" % self.line_of("thing", "It does it slowly")],
                         self.pdf_problems())

    def test_a_pdf_over_twenty_megabytes_is_refused(self):
        # Exactly the limit passes; one byte over it is refused.
        self.pdf("edge.pdf", 20 * self.MEGABYTE)
        self.pdf("big.pdf", 20 * self.MEGABYTE + 1)
        self.link_pdf("../files/edge.pdf", "../files/big.pdf")
        self.assertEqual(["thing.md:%d: links to ../files/big.pdf, which is 20.1 MB, over the 20 MB a PDF may be; "
                          "make it smaller, such as by compressing its pictures, or split it into parts"
                          % self.line_of("thing", "It does it slowly")],
                         self.pdf_problems())

    def test_a_pdf_named_through_a_folder_is_refused_and_not_published(self):
        # Only a file directly in the files folder is published. A link through a folder inside it, or out of it
        # and back, would otherwise carry a file from wherever the path led.
        self.pdf("sub/policy.pdf")
        (self.root / "docs/wiki/secret.pdf").write_bytes(b"%PDF-1.4\n")
        for target in ("../files/sub/policy.pdf", "../files/../secret.pdf", "../files/..%2Fsecret.pdf"):
            with self.subTest(target=target):
                self.link_pdf(target)
                problems = self.pdf_problems()
                self.assertEqual(1, len(problems), problems)
                self.assertIn("outside the wiki's files folder", problems[0])
                self.assertFalse((self.out / "files").exists(), "a PDF named through a folder was published")

    def test_a_pdf_named_with_an_ampersand_is_published(self):
        # The rendered page writes & as &amp; in an address, so the build has to read it back as &.
        self.pdf("R&D.pdf")
        self.link_pdf("../files/R&D.pdf")
        self.assertEqual([], self.pdf_problems())
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        anchor = re.search(r'<a href="([^"]+)" class="pdf">the policy 1</a> <span class="pdfsize">', page)
        self.assertIsNotNone(anchor, "the link to R&D.pdf is not a published PDF link")
        self.assertTrue((self.out / "thing" / anchor.group(1).replace("%26", "&")).is_file(), "R&D.pdf leads nowhere")

    # Every way markdown writes a link, so the check and the build can never judge one differently.
    PDF_LINK_FORMS = (("a title", 'It does it slowly, as [the policy 1]({} "The policy") says.[^why]'),
                      ("angle brackets", "It does it slowly, as [the policy 1](<{}>) says.[^why]"),
                      ("a reference", "It does it slowly, as [the policy 1][pol] says.[^why]\n\n[pol]: {}"),
                      ("a query", "It does it slowly, as [the policy 1]({}?x=1) says.[^why]"))

    def test_every_form_of_link_to_a_pdf_outside_the_files_folder_is_refused(self):
        (self.root / "docs/wiki/policy.pdf").write_bytes(b"%PDF-1.4\n")
        for form, sentence in self.PDF_LINK_FORMS:
            with self.subTest(form=form):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", sentence.format("../policy.pdf")))
                problems = self.pdf_problems()
                self.assertEqual(1, len(problems), problems)
                self.assertIn("outside the wiki's files folder", problems[0])

    def test_every_form_of_link_to_a_pdf_in_the_files_folder_is_published(self):
        self.pdf("policy.pdf")
        for form, sentence in self.PDF_LINK_FORMS:
            with self.subTest(form=form):
                self.write("thing", PAGE.replace("It does it slowly.[^why]", sentence.format("../files/policy.pdf")))
                self.assertEqual([], self.pdf_problems())
                page = (self.out / "thing/index.html").read_text(encoding="utf-8")
                anchor = re.search(r'<a href="([^"]+)" class="pdf"[^>]*>the policy 1</a> <span class="pdfsize">', page)
                self.assertIsNotNone(anchor, "the link is not a published PDF link")
                self.assertTrue((self.out / "thing" / anchor.group(1).partition("?")[0]).is_file(),
                                f"{anchor.group(1)} leads nowhere")

    def test_a_pdf_linked_to_a_file_outside_the_files_folder_is_refused(self):
        # A symbolic link is copied as the file it points at: a PDF linked to the project's .env would publish it.
        (self.root / ".env").write_text("TOKEN=secret", encoding="utf-8")
        (self.root / "docs/wiki/files").mkdir(parents=True)
        (self.root / "docs/wiki/files/policy.pdf").symlink_to(self.root / ".env")
        self.link_pdf("../files/policy.pdf")
        with self.assertRaises(wiki.WikiError) as caught:
            self.build()
        # No absolute path: a message names the wiki's own folders, the same on every machine.
        self.assertEqual("thing.md links to policy.pdf, which links to a file outside the files folder; put the PDF "
                         "itself in the wiki's files folder", str(caught.exception))
        self.assertFalse((self.out / "files/policy.pdf").exists(), "the linked file was published")

    def test_a_files_folder_that_is_a_symbolic_link_is_refused(self):
        # With the folder itself a link, the file and the folder resolve to the same place elsewhere, so a
        # containment test that resolves both would publish whatever the folder points at.
        (self.root / "elsewhere").mkdir()
        (self.root / "elsewhere/secret.pdf").write_bytes(b"%PDF-1.4\n")
        (self.root / "docs/wiki/files").symlink_to(self.root / "elsewhere")
        self.link_pdf("../files/secret.pdf")
        with self.assertRaises(wiki.WikiError) as caught:
            self.build()
        self.assertEqual("the wiki's files folder is a symbolic link, so a build would publish whatever it points "
                         "at; make files a folder of its own inside the wiki, and put the PDFs in it",
                         str(caught.exception))
        self.assertFalse((self.out / "files/secret.pdf").exists(), "a PDF from outside the wiki was published")

    def test_a_pdf_link_shows_the_pdfs_size(self):
        self.pdf("policy.pdf", 2516582)
        self.pdf("note.pdf", 3000)
        self.link_pdf("../files/policy.pdf", "../files/note.pdf")
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<a href="../files/policy.pdf" class="pdf">the policy 1</a> '
                      '<span class="pdfsize">(PDF, 2.4 MB)</span>', page)
        self.assertIn('<a href="../files/note.pdf" class="pdf">the policy 2</a> '
                      '<span class="pdfsize">(PDF, 3 KB)</span>', page)

    def test_a_pdf_size_reads_right_at_its_edges(self):
        # An empty file is no kilobyte, and a byte under a megabyte rounds up to a megabyte, not to 1024 KB.
        for size, label in ((0, "0 KB"), (1, "1 KB"), (self.MEGABYTE - 1, "1.0 MB"), (self.MEGABYTE, "1.0 MB")):
            with self.subTest(size=size):
                self.pdf("policy.pdf", size)
                self.link_pdf("../files/policy.pdf")
                self.build()
                page = (self.out / "thing/index.html").read_text(encoding="utf-8")
                self.assertIn('<span class="pdfsize">(PDF, %s)</span>' % label, page)

    def test_two_builds_of_a_wiki_with_a_pdf_are_identical(self):
        self.pdf("policy.pdf", 2516582)
        self.link_pdf("../files/policy.pdf")
        self.build()
        first = wiki.tree_digest(self.out)
        self.assertIn("files/policy.pdf", first, "no PDF was built, so the comparison proves nothing about one")
        shutil.rmtree(self.out)
        self.build()
        self.assertEqual(first, wiki.tree_digest(self.out))

    def test_a_pdf_link_carries_what_the_viewer_needs(self):
        self.pdf("policy.pdf")
        self.link_pdf("../files/policy.pdf")
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        # A real link to the published file, so a new tab, a middle click or a download still opens the PDF itself.
        anchor = re.search(r'<a href="([^"]+)" class="pdf">the policy 1</a>', page)
        self.assertIsNotNone(anchor, "the PDF link is not marked for the viewer")
        self.assertTrue((self.out / "thing" / anchor.group(1)).is_file(), "the PDF link leads nowhere")
        script = (self.out / "assets/wiki.js").read_text(encoding="utf-8")
        for needed in ('"a.pdf[href]"', "showModal", "(pointer: coarse)", "pdfViewerEnabled", '"iframe"',
                       "Open in new tab", "Download", "Close"):
            with self.subTest(needed=needed):
                self.assertIn(needed, script)

    def test_a_pdf_link_resolves_in_every_build_and_markdown_copy(self):
        self.pdf("policy.pdf")
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"')
                   .replace("It does it slowly.[^why]", "It does it slowly, as [the policy](../files/policy.pdf) says.[^why]"))
        for audience, links in (("internal", "file"), ("internal", "clean"), ("user", "file")):
            with self.subTest(audience=audience, links=links):
                shutil.rmtree(self.out, ignore_errors=True)
                wiki.build(self.root, self.out, audience, today="2026-01-02", links=links)
                page = (self.out / "thing/index.html").read_text(encoding="utf-8")
                href = re.search(r'<a href="([^"]+)" class="pdf">', page).group(1)
                self.assertTrue((self.out / "thing" / href).is_file(), f"{href} leads nowhere")
                if audience == "internal":
                    copy = (self.out / "thing" / wiki.AGENT_COPY).read_text(encoding="utf-8")
                    target = re.search(r"\[the policy\]\(([^)]+)\)", copy).group(1)
                    self.assertTrue((self.out / "thing" / target).is_file(), f"the markdown copy's {target} leads nowhere")

    def test_a_reference_to_a_pdf_is_refused(self):
        # A PDF is a document, not a citation, wherever it is kept.
        self.pdf("policy.pdf")
        self.write("thing", PAGE.replace("[^why]: The reason — `Source/Thing.h`.",
                                         "[^why]: The reason — [the policy](../files/policy.pdf)."))
        self.assertEqual(["thing.md cites ../files/policy.pdf, which is a document; a reference names the code that "
                          "does the thing, or an outside service's own documentation"],
                         wiki.citation_problems(self.root))
        self.write("thing", PAGE.replace("[^why]: The reason — `Source/Thing.h`.",
                                         "[^why]: The vendor — [the guide](https://example.com/guide.pdf)."))
        self.assertEqual([], wiki.citation_problems(self.root), "an outside service's own PDF was refused")

    def test_a_citation_does_not_count_against_the_reading_budget(self):
        long_note = "[^why]: " + ("word " * 300)
        self.write("thing", PAGE.replace("[^why]: The reason — `Source/Thing.h`.", long_note))
        counts, goals_words = self.build()
        self.assertEqual([], wiki.budget_problems(counts, goals_words, self.budget),
                         "citing a source pushed a page over its budget")

    def test_a_code_block_does_not_count_against_the_reading_budget(self):
        # A sample is copied or run, not read -- a prompt to hand an agent is a page of it. Code blocks
        # are not counted.
        sample = "Type it.[^why]\n\n```text\n" + ("word " * 600) + "\n```\n"
        self.write("thing", PAGE.replace("## Ground", sample + "\n## Ground"))
        counts, goals_words = self.build()
        self.assertEqual([], wiki.budget_problems(counts, goals_words, self.budget),
                         "a code sample pushed a page over its budget")
        self.assertLess(counts["thing"], 100)

    def test_prose_still_counts_against_the_reading_budget(self):
        self.write("thing", PAGE.replace("It does it slowly.[^why]", ("word " * 600) + "[^why]"))
        counts, goals_words = self.build()
        self.assertTrue(any("thing.md runs to" in p for p in wiki.budget_problems(counts, goals_words, self.budget)))

    def test_a_tables_borders_do_not_count_against_the_reading_budget(self):
        # A table's pipes and dashed line are how it is drawn, not what it says: only its cells are read.
        table = "| A | B |\n|---|---|\n| one | two |\n"
        self.write("thing", PAGE.replace("## Ground", table + "\n## Ground"))
        with_table, _ = self.build()
        self.write("thing", PAGE.replace("## Ground", "A B\n\none two\n\n## Ground"))
        with_prose, _ = self.build()
        self.assertEqual(with_prose["thing"], with_table["thing"])

    # --- malformed input ---------------------------------------------------------------------------

    def test_a_page_with_no_front_matter_fence_is_refused(self):
        self.write("thing", "title = \"A thing\"\n\nBody.\n")
        self.refused("front-matter fence")

    def test_a_page_whose_front_matter_never_closes_is_refused(self):
        self.write("thing", "+++\ntitle = \"A thing\"\n\nBody.\n")
        self.refused("never closes")

    def test_a_page_with_unreadable_front_matter_is_refused(self):
        self.write("thing", "+++\ntitle = not a string\n+++\n\nBody.\n")
        self.refused("unreadable front matter")

    def test_a_missing_configuration_file_is_refused(self):
        (self.root / "docs/wiki" / CONFIG).unlink()
        self.refused(f"there is no {CONFIG}".lower())

    def test_a_navigation_file_with_no_sections_is_refused(self):
        self.nav('[site]\nname = "A Wiki"\n')
        self.refused("no sections")

    def test_a_navigation_file_with_no_site_name_is_refused(self):
        self.nav(CONFIGURATION.replace('name = "A Wiki"', ""))
        self.refused("site.name")


    # --- when a page last changed ------------------------------------------------------------------

    def test_a_page_says_when_it_last_changed(self):
        self.build(today="2026-03-04")
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn("Last updated 4 March 2026", page)

    def test_a_build_that_changes_nothing_writes_nothing(self):
        self.build(today="2026-03-04")
        before = {path: path.stat().st_mtime_ns
                  for path in sorted(self.out.rglob("*")) if path.is_file()}
        self.assertTrue(before, "a check that found no files did not run")
        self.build(today="2026-09-09")
        after = {path: path.stat().st_mtime_ns
                 for path in sorted(self.out.rglob("*")) if path.is_file()}
        self.assertEqual(before, after, "a build with nothing to do rewrote the site")

    def test_a_date_moves_only_for_the_page_that_changed(self):
        self.build(today="2026-03-04")
        self.write("thing", PAGE.replace("It does it slowly.", "It does it quickly."))
        self.build(today="2026-09-09")
        changed = (self.out / "thing/index.html").read_text(encoding="utf-8")
        untouched = (self.out / "about/index.html").read_text(encoding="utf-8") \
            if (self.out / "about/index.html").exists() else \
            (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn("Last updated 9 September 2026", changed)
        self.assertIn("Last updated 4 March 2026", untouched,
                      "a page nobody edited had its date moved")

    def test_restyling_the_site_is_not_a_page_being_updated(self):
        self.build(today="2026-03-04")
        # Point the tool at a copy of its own assets and change that, since the real ones are inside the
        # installed package and a test has no business writing there.
        assets = self.root / "assets"
        shutil.copytree(PACKAGE / "assets", assets)
        self.addCleanup(setattr, wiki, "ASSETS", wiki.ASSETS)
        wiki.ASSETS = assets
        (assets / "wiki.css").write_text((assets / "wiki.css").read_text(encoding="utf-8")
                                         + "\n.nothing{color:red}\n", encoding="utf-8")
        self.build(today="2026-09-09")
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn("Last updated 4 March 2026", page,
                      "changing the stylesheet moved a page's date")

    def test_check_reports_a_page_edited_since_its_date_was_recorded(self):
        self.build(today="2026-03-04")
        self.write("thing", PAGE.replace("It does it slowly.", "It does it quickly."))
        problems = wiki.date_problems(self.root)
        self.assertTrue(any("thing.md" in problem for problem in problems), problems)
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(1, status, "the gate would have passed a page under a stale date")
        self.assertIn("since its date was recorded", output)

    def test_a_deleted_page_leaves_no_date_behind(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build(today="2026-03-04")
        self.assertIn("thing/part", wiki.read_dates(self.root / "docs/wiki"))
        (self.pages / "thing/part.md").unlink()
        self.build(today="2026-03-05")
        self.assertNotIn("thing/part", wiki.read_dates(self.root / "docs/wiki"))
        self.assertEqual([], wiki.date_problems(self.root))

    # An audit is the page checked against the code. A page's stats give its last audited date after its
    # last updated date, and say never when it has not been audited.

    def test_a_page_never_audited_says_so_in_its_footer(self):
        self.build()
        self.assertIn("Last audited never", self.footer())

    def test_auditing_a_page_puts_the_day_in_its_footer(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build(today="2026-03-04")
        wiki.audit(self.root, ["thing"], today="2026-09-09")
        self.build(today="2026-09-10")
        footer = self.footer()
        self.assertIn("Last updated 4 March 2026", footer, "auditing a page moved the day it was updated")
        self.assertIn("Last audited 9 September 2026", footer)
        self.assertIn("Last audited never", self.footer("thing/part"), "auditing one page audited another")

    def test_a_page_excused_from_citations_has_no_audit_in_its_footer(self):
        # A goals page, or any page excused from citations, has no audit date in its footer. The front page
        # and the goals page both say goals = false.
        self.build()
        for path in (self.out / "index.html", self.out / "goals/index.html"):
            with self.subTest(page=path.parent.name or "index"):
                page = path.read_text(encoding="utf-8")
                footer = page[page.index('<div class="foot">'):page.index("</div>", page.index('<div class="foot">'))]
                self.assertIn("Last updated", footer)
                self.assertNotIn("audited", footer)

    def test_an_edit_keeps_the_day_a_page_was_last_audited(self):
        self.build(today="2026-03-04")
        wiki.audit(self.root, ["thing"], today="2026-03-05")
        self.write("thing", PAGE.replace("It does it slowly.", "It does it quickly."))
        self.build(today="2026-09-09")
        footer = self.footer()
        self.assertIn("Last updated 9 September 2026", footer)
        self.assertIn("Last audited 5 March 2026", footer)

    def test_auditing_a_page_excused_from_citations_is_refused(self):
        self.build()
        with self.assertRaises(wiki.WikiError) as caught:
            wiki.audit(self.root, ["thing", "goals"], today="2026-01-03")
        self.assertIn("goals.md", str(caught.exception))
        self.assertNotIn("audited", wiki.read_dates(self.root / "docs/wiki")["thing"],
                         "a refused audit recorded the pages beside it")

    def test_auditing_a_page_that_does_not_exist_is_refused(self):
        self.build()
        with self.assertRaises(wiki.WikiError) as caught:
            wiki.audit(self.root, ["nothing"])
        self.assertIn("nothing.md", str(caught.exception))

    def test_auditing_a_page_edited_since_its_date_was_recorded_is_refused(self):
        # An audit is of the page its date records. One edited since has not been built, let alone checked.
        self.build(today="2026-03-04")
        self.write("thing", PAGE.replace("It does it slowly.", "It does it quickly."))
        with self.assertRaises(wiki.WikiError) as caught:
            wiki.audit(self.root, ["thing"], today="2026-03-05")
        self.assertIn("wiki build", str(caught.exception))
        self.assertNotIn("audited", wiki.read_dates(self.root / "docs/wiki")["thing"])

    def test_an_audit_names_a_page_with_or_without_md_and_leaves_the_check_passing(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        wiki.audit(self.root, ["thing", "thing/part.md"], today="2026-01-03")
        dates = wiki.read_dates(self.root / "docs/wiki")
        self.assertEqual("2026-01-03", dates["thing"]["audited"])
        self.assertEqual("2026-01-03", dates["thing/part"]["audited"])
        self.assertEqual([], wiki.date_problems(self.root))

    def test_a_user_footer_leaves_out_the_audit(self):
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "user"'))
        self.build("user")
        footer = self.footer()
        self.assertIn("Last updated", footer)
        self.assertNotIn("audited", footer)

    # --- page families -------------------------------------------------------------------------------

    def family(self, headings=None, labels=None, parent=PAGE, linked=True, table=None, marker=False):
        """The thing page declaring a family, with a link to its part when `linked` and the table marker when
        `marker`; returns the family problems."""
        declaration = "[family]\n"
        for key, value in (("headings", headings), ("labels", labels), ("table", table)):
            if value is not None:
                declaration += "%s = %s\n" % (key, json.dumps(value))
        text = parent.replace("\n[[infobox]]", "\n" + declaration + "\n[[infobox]]", 1)
        if linked:
            text = text.replace("A thing does what it does.[^why]",
                                "A thing does what it does, and has [a part](thing/part.md).[^why]")
        if marker:
            text = text.replace("\n## Speed", "\n{family-table}\n\n## Speed", 1)
        self.write("thing", text)
        return wiki.family_problems(self.root)

    def table_cells(self, page, name):
        """The rows of the generated table of that name on a built page, each a list of its cells' text."""
        table = page[page.index('<table class="w %s">' % name):]
        table = table[:table.index("</table>")]
        return [[re.sub(r"<[^>]+>", "", cell) for cell in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row)]
                for row in re.findall(r"<tr>(.*?)</tr>", table, re.S)]

    def test_a_family_table_lists_each_member_with_its_infobox_values(self):
        # A member that states no value for a column leaves its cell empty, so the gap shows.
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.write("thing/bit", PAGE.replace("A thing", "A bit")
                   .replace('  { label = "Today", value = "a number", cite = "why" },\n', ""))
        problems = self.family(labels=["Held to", "Today"], table=["Today", "Held to"], linked=False, marker=True)
        self.assertEqual([], problems, "a parent whose table lists every member was refused")
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertEqual([["", "Today", "Held to"], ["A bit", "", "a promise"], ["A part", "a number", "a promise"]],
                         self.table_cells(page, "family"))
        self.assertIn('<a href="part/index.html">A part</a>', page)
        self.assertNotIn("{family-table}", page)

    def test_a_family_table_in_a_user_build_lists_only_members_marked_for_users(self):
        user = 'categories = ["Things"]\naudience = "user"'
        self.write("thing/part", PAGE.replace("A thing", "A part").replace('categories = ["Things"]', user))
        self.write("thing/bit", PAGE.replace("A thing", "A bit"))
        self.family(labels=["Held to", "Today"], table=["Today"], linked=False, marker=True,
                    parent=PAGE.replace('categories = ["Things"]', user))
        self.build("user")
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertEqual([["", "Today"], ["A part", "a number"]], self.table_cells(page, "family"))

    def test_a_family_table_is_in_the_parent_markdown_copy(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.family(labels=["Held to", "Today"], table=["Today"], linked=False, marker=True)
        self.build()
        copy = (self.out / "thing/index.md").read_text(encoding="utf-8")
        self.assertIn("| [A part](part/index.md) | a number |", copy)
        self.assertNotIn("{family-table}", copy)

    def test_a_value_with_a_line_break_stays_on_one_row_of_a_markdown_table(self):
        self.write("thing/part", PAGE.replace("A thing", "A part").replace('value = "a number"', 'value = "a\\nnumber | two"'))
        self.family(labels=["Held to", "Today"], table=["Today"], linked=False, marker=True)
        self.build()
        copy = (self.out / "thing/index.md").read_text(encoding="utf-8")
        self.assertIn("| [A part](part/index.md) | a number \\| two |", copy)

    def test_a_family_table_marker_the_build_cannot_replace_is_refused(self):
        # The build writes the table only where the marker is a paragraph of its own; inside a list, or indented
        # into a code block, it would be left on the page as written.
        for placed in ("- A list item.[^why]\n  {family-table}", "    {family-table}"):
            with self.subTest(placed=placed):
                self.write("thing/part", PAGE.replace("A thing", "A part"))
                text = PAGE.replace("\n[[infobox]]", '\n[family]\nlabels = ["Held to", "Today"]\ntable = ["Today"]\n\n[[infobox]]', 1)
                self.write("thing", text.replace("\n## Speed", "\n" + placed + "\n\n## Speed", 1)
                           .replace("A thing does what it does.[^why]", "A thing has [a part](thing/part.md).[^why]"))
                problems = wiki.family_problems(self.root)
                self.assertEqual(1, len(problems), problems)
                self.assertIn("thing.md has {family-table} where the build cannot write the table", problems[0])

    def test_a_family_table_marker_written_twice_is_refused(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.family(labels=["Held to", "Today"], table=["Today"], linked=False, marker=True)
        text = (self.pages / "thing.md").read_text(encoding="utf-8").replace("\n## Ground", "\n{family-table}\n\n## Ground", 1)
        self.write("thing", text)
        problems = wiki.family_problems(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing.md has {family-table} 2 times", problems[0])

    def test_a_family_table_label_the_layout_does_not_list_is_refused(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        problems = self.family(labels=["Held to", "Today"], table=["Colour"], linked=False, marker=True)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing.md: family.table lists 'Colour', which family.labels does not", problems[0])

    def test_a_family_table_needs_both_its_list_and_its_marker(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        problems = self.family(labels=["Held to", "Today"], table=["Today"])
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing.md declares family.table but has no {family-table}", problems[0])
        problems = self.family(labels=["Held to", "Today"], marker=True)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing.md has {family-table} but declares no family.table", problems[0])

    def test_a_family_table_marker_on_a_page_with_no_family_is_refused(self):
        self.write("thing", PAGE.replace("\n## Speed", "\n{family-table}\n\n## Speed", 1))
        problems = wiki.family_problems(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing.md has {family-table} but declares no [family]", problems[0])

    def test_a_family_table_marker_is_not_taken_for_a_sentence(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.family(labels=["Held to", "Today"], table=["Today"], linked=False, marker=True)
        self.assertEqual([], [problem for problem in wiki.uncited_problems(self.root) if "family-table" in problem])

    # --- health page ---------------------------------------------------------------------------------

    HEALTH = '''+++
title = "Health"
subtitle = "every page's status, sources, marks and dates"
goals = false
status = "approved"
intent = """
The health page exists so that a writer sees which pages to check first.
"""
+++

Every page, with its sources and dates.
'''

    def health(self, text=None):
        """The health page, listed in the navigation beside the front page and the goals."""
        self.write("health", text or self.HEALTH)
        self.nav(CONFIGURATION.replace('pages = ["index", "goals"]', 'pages = ["index", "goals", "health"]'))

    def test_a_health_page_lists_every_page_with_its_status_counts_and_dates(self):
        self.health()
        self.build()
        page = (self.out / "health/index.html").read_text(encoding="utf-8")
        self.assertIn("3 pages, 0 drafts waiting on approval, 1 never audited, 1 claim with no source", page)
        rows = self.table_cells(page, "health")
        self.assertEqual(["Page", "Status", "Words", "Cited", "Missing", "Updated", "Audited"], rows[0])
        thing = rows[1]
        self.assertEqual(["A thing", "approved", "1", "1", "2 January 2026", "never"], thing[:2] + thing[3:])
        self.assertTrue(thing[2].isdigit(), thing)
        # Pages that cite nothing cannot be audited, so their citation and audit cells are empty.
        self.assertEqual([["Front", "", "", ""], ["Goals", "", "", ""]],
                         [[row[0], row[3], row[4], row[6]] for row in rows[2:]])
        self.assertNotIn("Health", [row[0] for row in rows], "the health page listed itself")

    def test_the_health_table_lists_pages_by_title_and_marks_claims_with_no_source(self):
        # A to Z by title, whatever the case and whether audited or not; a count over 0 is marked, and 0 is not.
        self.write("thing/part", PAGE.replace("A thing", "a part").replace(" {missing}", "[^why]"))
        self.health()
        self.build()
        wiki.audit(self.root, ["thing"], today="2026-01-03")
        self.build()
        page = (self.out / "health/index.html").read_text(encoding="utf-8")
        rows = self.table_cells(page, "health")
        self.assertEqual(["a part", "A thing", "Front", "Goals"], [row[0] for row in rows[1:]])
        self.assertEqual("3 January 2026", rows[2][6])
        self.assertIn('<td class="missing">1</td>', page)
        self.assertNotIn('<td class="missing">0</td>', page)

    def test_the_health_table_is_in_the_health_page_markdown_copy(self):
        self.health()
        self.build()
        copy = (self.out / "health/index.md").read_text(encoding="utf-8")
        self.assertIn("| [A thing](../thing/index.md) | approved |", copy)

    def test_a_user_build_carries_no_health_table(self):
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "user"'))
        self.health(self.HEALTH.replace('status = "approved"', 'status = "approved"\naudience = "user"'))
        self.build("user")
        self.assertNotIn('class="w health"', (self.out / "health/index.html").read_text(encoding="utf-8"))

    def test_a_family_member_with_a_heading_its_layout_does_not_list_is_refused(self):
        self.write("thing/part", PAGE.replace("A thing", "A part").replace("## Ground", "## Colour"))
        problems = self.family(headings=["Speed", "Ground"])
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing/part.md: the heading 'Colour' is not in the family layout on thing.md", problems[0])
        self.assertIn("family.headings", problems[0])

    def test_a_family_member_may_leave_a_heading_out_but_not_reorder_them(self):
        self.write("thing/part", PAGE.replace("A thing", "A part").replace("## Speed\n\nIt does it slowly.[^why]\n\n", ""))
        self.assertEqual([], self.family(headings=["Speed", "Ground"]), "leaving out a heading was refused")
        swapped = PAGE.replace("A thing", "A part").replace("## Speed", "## First").replace("## Ground", "## Speed")
        self.write("thing/part", swapped.replace("## First", "## Ground"))
        problems = self.family(headings=["Speed", "Ground"])
        self.assertEqual(1, len(problems), problems)
        self.assertIn("comes before", problems[0])

    def test_a_family_member_with_an_infobox_label_its_layout_does_not_list_is_refused(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        problems = self.family(headings=["Speed", "Ground"], labels=["Held to"])
        self.assertEqual(1, len(problems), problems)
        self.assertIn("the infobox label 'Today' is not in the family layout on thing.md", problems[0])
        self.assertIn("family.labels", problems[0])

    def test_a_family_parent_that_does_not_link_a_member_is_refused(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        problems = self.family(headings=["Speed", "Ground"], linked=False)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing.md does not link thing/part.md", problems[0])

    def test_a_family_layout_that_is_not_a_list_is_refused(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        problems = self.family(headings="Speed")
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing.md: family.headings must list", problems[0])

    def test_a_family_heading_is_compared_as_the_page_shows_it(self):
        # A closing run of hashes and backticks around a name change nothing a reader sees.
        self.write("thing/part", PAGE.replace("A thing", "A part").replace("## Speed", "## Speed ##")
                   .replace("## Ground", "## `Ground`"))
        self.assertEqual([], self.family(headings=["Speed", "Ground"]))

    def test_an_empty_family_list_is_refused_with_how_to_leave_it_out(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        problems = self.family(headings=[])
        self.assertEqual(1, len(problems), problems)
        self.assertIn("leave family.headings out", problems[0])

    def test_a_family_that_is_not_a_table_is_refused(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.write("thing", PAGE.replace('status = "approved"', 'status = "approved"\nfamily = ["Speed"]'))
        problems = wiki.family_problems(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("thing.md: family must be a table", problems[0])

    def test_children_of_a_parent_with_no_family_are_not_checked(self):
        self.write("thing/part", PAGE.replace("A thing", "A part").replace("## Ground", "## Colour"))
        self.assertEqual([], wiki.family_problems(self.root))

    def test_check_names_a_member_that_strays_from_its_family(self):
        self.write("thing/part", PAGE.replace("A thing", "A part").replace("## Ground", "## Colour"))
        self.family(headings=["Speed", "Ground"])
        self.build()
        problems, _, _, _ = wiki.check(self.root)
        self.assertTrue(any("is not in the family layout" in problem for problem in problems), problems)

    def test_families_lists_children_that_share_no_layout_and_titles_that_repeat_the_parent(self):
        self.write("thing/part", PAGE.replace("A thing", "A part").replace("## Ground", "## Colour"))
        self.write("thing/notes", PAGE.replace("A thing", "Thing notes"))
        lines = wiki.families_report(self.root)
        self.assertIn("thing.md declares no family for its 2 children", lines)
        self.assertIn("  thing/part.md: Speed, Colour", lines)
        self.assertIn("  thing/notes.md: Speed, Ground", lines)
        self.assertIn("thing/notes.md is titled 'Thing notes', which repeats 'thing' from its parent's title "
                      "'A thing'; a nested page's title names only what sets it apart", lines)

    # --- coverage ------------------------------------------------------------------------------------

    def source(self, *names):
        """Source files in the project, each holding one line."""
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("// source\n", encoding="utf-8")

    def covering(self, include, exclude=None):
        """Set the [coverage] table in wiki.toml, and return the report it gives."""
        table = "\n[coverage]\ninclude = %s\n" % json.dumps(include)
        if exclude is not None:
            table += "exclude = %s\n" % json.dumps(exclude)
        self.nav(CONFIGURATION + table)
        return wiki.coverage(self.root)

    def test_coverage_lists_every_source_file_no_page_cites(self):
        # The thing page cites Source/Thing.h; no page cites Source/Other.h, and the tests are left out.
        self.source("Source/Thing.h", "Source/Other.h", "tests/test_thing.py")
        report = self.covering(["Source/**/*.h", "tests/*.py"], exclude=["tests/*.py"])
        self.assertEqual(["Source/Other.h", "Source/Thing.h"], report["files"])
        self.assertEqual(["Source/Other.h"], report["uncited"])
        self.assertEqual([], report["missing"])

    def test_coverage_names_a_citation_of_a_file_that_does_not_exist(self):
        self.source("Source/Other.h")
        self.assertEqual([("thing.md", "Source/Thing.h")], self.covering(["Source/*.h"])["missing"])

    def test_a_name_that_is_not_a_project_file_is_not_reported_missing(self):
        # A reference also names things that are not files in the project: an action, a media type, a
        # generated or relative folder, and a file a reader creates in a folder the project does not have.
        # Only a file under a folder the project has, with an extension, is taken for a stale citation.
        self.source("Source/Thing.h")
        notes = ("[^why]: The reason — `Source/Thing.h`, `actions/setup-python`, `text/plain`, `_site/CNAME`, "
                 "`docs/wiki/site/`, `images/`, `functions/_middleware.js` and `Source/Gone.h`.")
        self.write("thing", PAGE.replace("[^why]: The reason — `Source/Thing.h`.", notes))
        self.assertEqual([("thing.md", "Source/Gone.h")], self.covering(["Source/*.h"])["missing"])

    def test_a_citation_with_a_line_number_counts_its_file(self):
        self.source("Source/Thing.h")
        self.write("thing", PAGE.replace("`Source/Thing.h`", "`Source/Thing.h:12`"))
        report = self.covering(["Source/*.h"])
        self.assertEqual([], report["uncited"], "a citation with a line number did not count its file")
        self.assertEqual([], report["missing"])

    def test_a_coverage_pattern_that_leads_outside_the_project_is_refused(self):
        self.source("Source/Thing.h")
        for pattern in ("../*.py", "/etc/*.conf", "Source/../../*.h"):
            with self.subTest(pattern=pattern):
                with self.assertRaises(wiki.WikiError) as caught:
                    self.covering([pattern])
                self.assertIn("leads outside the project", str(caught.exception))

    def test_a_folder_citation_covers_none_of_the_files_in_it(self):
        self.source("Source/Thing.h")
        self.write("thing", PAGE.replace("[^why]: The reason — `Source/Thing.h`.", "[^why]: The reason — `Source/`."))
        self.assertEqual(["Source/Thing.h"], self.covering(["Source/*.h"])["uncited"])

    def test_a_citation_shown_in_a_code_sample_is_not_counted(self):
        self.source("Source/Thing.h", "Source/Other.h")
        sample = "```markdown\n[^x]: `Source/Other.h` — `sample()`.\n[^y]: `Source/Gone.h`.\n```\n\n## Ground"
        self.write("thing", PAGE.replace("## Ground", sample))
        report = self.covering(["Source/*.h"])
        self.assertEqual(["Source/Other.h"], report["uncited"])
        self.assertEqual([], report["missing"])

    def test_coverage_patterns_that_match_no_file_are_refused(self):
        with self.assertRaises(wiki.WikiError) as caught:
            self.covering(["nowhere/*.py"])
        self.assertIn("coverage.include matches no files", str(caught.exception))

    def test_coverage_include_that_is_not_a_list_of_patterns_is_refused(self):
        with self.assertRaises(wiki.WikiError) as caught:
            self.covering("Source/*.h")
        self.assertIn("coverage.include must list", str(caught.exception))

    # --- the command line ---------------------------------------------------------------------------

    def run_main(self, argv):
        """The entry point a project's wrapper actually calls, and the status it acts on.

        Nothing `main` should catch is caught here: a problem that escaped it would reach a person as a
        traceback, and a helper that tidied it away would hide exactly that.
        """
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                status = cli.main(argv)
            except SystemExit as refused:
                # argparse refuses a command line by exiting, which is how a person meets it too.
                status = refused.code
        return status, out.getvalue() + err.getvalue()

    def test_a_build_that_stopped_partway_does_not_block_the_next(self):
        # A build that stops on one page has already written the pages before it. The next build must know
        # the folder for its own, or one failure refuses every build after it until a person clears it.
        self.write("thing", PAGE.replace("It does it slowly.[^why]",
                                         "It is drawn ![here](../images/nope.png).[^why]"))
        status, output = self.run_main(["--root", str(self.root), "build"])
        self.assertEqual(1, status, output)
        site = self.root / "docs/wiki/site"
        self.assertTrue(site.is_dir() and any(site.iterdir()),
                        "the failed build wrote nothing, so it proves nothing about the next one")
        self.write("thing", PAGE)
        status, output = self.run_main(["--root", str(self.root), "build"])
        self.assertEqual(0, status, output)

    def test_the_audit_command_names_each_page_it_recorded(self):
        self.write("thing/part", PAGE.replace("A thing", "A part"))
        self.build()
        status, output = self.run_main(["--root", str(self.root), "audit", "thing", "thing/part"])
        self.assertEqual(0, status, output)
        self.assertIn("wiki: thing audited", output)
        self.assertIn("wiki: thing/part audited", output)

    def test_the_audit_command_needs_a_page(self):
        status, output = self.run_main(["--root", str(self.root), "audit"])
        self.assertEqual(2, status)
        self.assertIn("PAGE", output)

    def test_check_passes_on_a_sound_wiki(self):
        # Built first: a wiki that has never been built has recorded no dates, and the check says so.
        self.build()
        status, _ = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(0, status)

    def test_check_refuses_a_wiki_whose_dates_were_never_recorded(self):
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(1, status)
        self.assertIn("since its date was recorded", output)

    def test_check_refuses_a_page_that_will_not_render(self):
        self.write("thing", PAGE.replace('intent = """', 'nope = """'))
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(1, status, "the gate would have passed a page that does not render")
        self.assertIn("intent", output)

    def test_check_refuses_a_page_over_its_budget(self):
        self.write("thing", PAGE + ("\n\nword " * self.budget["page"]))
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(1, status)
        self.assertIn("over the", output)

    def test_a_root_with_no_wiki_is_misuse_not_failure(self):
        status, output = self.run_main(["--root", str(self.root / "docs"), "check"])
        self.assertEqual(2, status, "a wrong root must be misuse, not a failed check")
        self.assertIn("no wiki at", output)

    def test_a_problem_that_stops_the_build_is_a_sentence_not_a_traceback(self):
        (self.pages / "goals.md").unlink()
        status, output = self.run_main(["--root", str(self.root), "check"])
        self.assertEqual(1, status)
        self.assertIn("wiki: there is no goals.md", output)

    def test_publish_names_its_sitemap_or_the_setting_that_writes_one(self):
        status, output = self.run_main(["--root", str(self.root), "publish", str(self.out)])
        self.assertEqual(0, status, output)
        self.assertIn("set site.url in wiki.toml to write sitemap.xml", output)
        self.nav(CONFIGURATION.replace('name = "A Wiki"', 'name = "A Wiki"\nurl = "https://docs.example.org"'))
        status, output = self.run_main(["--root", str(self.root), "publish", str(self.out)])
        self.assertEqual(0, status, output)
        self.assertIn("sitemap.xml lists 4 addresses under https://docs.example.org/", output)

    def test_coverage_without_a_coverage_table_names_the_table_to_add(self):
        status, output = self.run_main(["--root", str(self.root), "coverage"])
        self.assertEqual(2, status, output)
        self.assertIn("[coverage]", output)

    def test_coverage_prints_each_gap_on_its_own_line_then_the_totals(self):
        self.source("Source/Other.h")
        self.nav(CONFIGURATION + '\n[coverage]\ninclude = ["Source/*.h"]\n')
        status, output = self.run_main(["--root", str(self.root), "coverage"])
        self.assertEqual(0, status, output)
        self.assertIn("wiki: Source/Other.h is cited by no page\n", output)
        self.assertIn("wiki: thing.md cites Source/Thing.h, which does not exist\n", output)
        self.assertIn("wiki: 0 of 1 source file cited; 1 citation names a file that does not exist\n", output)

    def test_the_root_may_follow_the_command(self):
        # The wrapper the README gives a project passes --root after whatever command it was handed.
        self.build()
        status, output = self.run_main(["check", "--root", str(self.root),
                                        "--wiki", str(self.root / "docs/wiki")])
        self.assertEqual(0, status, output)

    def test_the_site_s_own_script_is_served_so_a_browser_will_run_it(self):
        """A .js under the site's assets is the site's own code. Answered as text, a browser refuses to
        execute it and the site loses search, the theme and the lightbox, while a .js a reference points
        at anywhere else is still shown rather than downloaded."""
        self.assertIsNone(serving.shown_as_text("docs/wiki/site/assets/wiki.js", "docs/wiki/site"))
        self.assertIsNone(serving.shown_as_text("docs/wiki/site/assets/mermaid.min.js", "docs/wiki/site"))
        self.assertEqual(serving.PLAIN, serving.shown_as_text("src/thing/helper.js", "docs/wiki/site"))
        self.assertEqual(serving.PLAIN, serving.shown_as_text("docs/wiki/site/thing/index.md", "docs/wiki/site"))

    def test_the_program_alone_builds_and_serves(self):
        # `wiki` with no command is `wiki serve`, and serve is the only command that declares a port.
        from unittest import mock
        served = []
        with mock.patch.object(cli, "serve", lambda root, site, port: served.append(port) or 0):
            status, output = self.run_main(["--root", str(self.root)])
        self.assertEqual(0, status, output)
        self.assertEqual([cli.PORT], served)

    def test_building_over_a_directory_this_tool_did_not_write_is_refused(self):
        precious = self.root / "precious"
        precious.mkdir()
        (precious / "important.txt").write_text("irreplaceable", encoding="utf-8")
        status, output = self.run_main(["--root", str(self.root), "publish", str(precious)])
        self.assertEqual(2, status)
        self.assertIn("not empty", output)
        self.assertTrue((precious / "important.txt").is_file(),
                        "the build deleted a directory it did not write")

    def test_building_over_a_previous_build_is_allowed(self):
        status, _ = self.run_main(["--root", str(self.root), "publish", str(self.out)])
        self.assertEqual(0, status)
        status, _ = self.run_main(["--root", str(self.root), "publish", str(self.out)])
        self.assertEqual(0, status, "a second build into its own output was refused")

    def test_links_out_of_the_site_are_counted_from_where_the_site_will_be_read(self):
        # A normal build stages into a temporary directory; a link to a file outside the site has to be
        # counted from where the site ends up, not from where the bytes were written.
        self.write("thing", PAGE.replace("A thing does what it does.",
                                         "See [the rules](../../../AGENTS.md)."))
        (self.root / "AGENTS.md").write_text("rules", encoding="utf-8")
        status, _ = self.run_main(["--root", str(self.root), "publish", str(self.out)])
        self.assertEqual(0, status)
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('href="../../AGENTS.md"', page,
                      "a link out of the site was counted from the staging directory")


class ServingTests(unittest.TestCase):
    """What the browser is handed when a reference is followed."""

    def test_a_cited_file_is_shown_rather_than_downloaded(self):
        # The stock handler answers .md with text/markdown and .h with an unknown type, and a browser
        # downloads both -- so following a citation got you a file on disk instead of the passage.
        for name in ("docs/design/overview.md", "src/session.h", "src/session.cpp",
                     "config/app.ini", "docs/wiki/wiki.toml", "app/main.py", "lib/store.ts"):
            with self.subTest(name=name):
                self.assertEqual("text/plain; charset=utf-8", serving.shown_as_text(name))

    def test_nothing_the_server_hands_out_may_be_cached(self):
        """A real request, because this bug is invisible in the code and obvious in a browser.

        The stock handler sends no cache headers, so a browser applies its own heuristic and goes on
        serving a stylesheet that has since changed. The site is rebuilt constantly; a stale asset makes
        a change look broken rather than unfetched, and that cost three rounds of review once.
        """
        import http.client
        import threading

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        (Path(directory.name) / "wiki.css").write_text("body{}", encoding="utf-8")
        server = serving.http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), serving.functools.partial(serving.Handler,
                                                           directory=directory.name))
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)

        connection = http.client.HTTPConnection(*server.server_address)
        connection.request("GET", "/wiki.css")
        response = connection.getresponse()
        response.read()
        self.assertEqual(200, response.status)
        self.assertIn("no-store", response.getheader("Cache-Control") or "")

    def serve_project(self, root):
        """A running server rooted at a project, and a function that fetches an address from it."""
        server = serving.http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), serving.functools.partial(serving.Handler, directory=str(root)))
        self.addCleanup(server.server_close)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)

        def fetch(address, host=None):
            connection = http.client.HTTPConnection(*server.server_address)
            self.addCleanup(connection.close)
            connection.request("GET", address, headers={"Host": host} if host else {})
            response = connection.getresponse()
            return response, response.read()

        return server, fetch

    def test_a_hidden_file_is_never_served(self):
        # The server shows the whole project, which holds secrets a page never links to: a .env, and every
        # credential and remote in .git. A path with any part starting with a full stop is not found.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / ".env").write_text("TOKEN=secret", encoding="utf-8")
        (root / ".git").mkdir()
        (root / ".git/config").write_text("[remote]", encoding="utf-8")
        (root / "wiki.css").write_text("body{}", encoding="utf-8")
        _, fetch = self.serve_project(root)

        for address, status in (("/.env", 404), ("/.git/config", 404), ("/%2Egit/config", 404),
                                ("/.git/", 404), ("/wiki.css", 200)):
            with self.subTest(address=address):
                response, body = fetch(address)
                self.assertEqual(status, response.status)
                self.assertNotIn(b"secret", body)

    def test_a_linked_file_is_judged_by_where_it_really_is(self):
        # A link in the project reaches whatever it points at, so a file whose real place is a hidden folder
        # is not found. A site folder linked from elsewhere is still served.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        root, outside = Path(directory.name), Path(elsewhere.name)
        (root / ".git").mkdir()
        (root / ".git/config").write_text("token = secret", encoding="utf-8")
        (outside / ".ssh").mkdir()
        (outside / ".ssh/key").write_text("secret", encoding="utf-8")
        (outside / "site").mkdir()
        (outside / "site/index.html").write_text("<p>the site</p>", encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs/gitlink").symlink_to(root / ".git")
        (root / "docs/keys").symlink_to(outside / ".ssh")
        (root / "docs/site").symlink_to(outside / "site")
        _, fetch = self.serve_project(root)
        for address, status in (("/docs/gitlink/config", 404), ("/docs/keys/key", 404),
                                ("/docs/site/index.html", 200)):
            with self.subTest(address=address):
                response, body = fetch(address)
                self.assertEqual(status, response.status)
                self.assertNotIn(b"secret", body)

    def test_the_server_answers_only_a_request_addressed_to_a_local_name(self):
        # A web page can give its own domain the address 127.0.0.1 and then read the server as part of its
        # own site. A request addressed by any other name is refused.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        (Path(directory.name) / "wiki.css").write_text("body{}", encoding="utf-8")
        server, fetch = self.serve_project(directory.name)
        port = server.server_address[1]
        for host, status in (("attacker.example", 403), (f"attacker.example:{port}", 403),
                             (f"localhost:{port}", 200), (f"127.0.0.1:{port}", 200)):
            with self.subTest(host=host):
                response, body = fetch("/wiki.css", host)
                self.assertEqual(status, response.status)
                self.assertEqual(status == 200, body == b"body{}")

    def test_every_answer_tells_the_browser_not_to_guess_its_type(self):
        # A text file answered as text must not be read as a page by a browser that guesses from its contents.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        (Path(directory.name) / "notes.txt").write_text("<script>alert(1)</script>", encoding="utf-8")
        _, fetch = self.serve_project(directory.name)
        response, _ = fetch("/notes.txt")
        self.assertEqual("nosniff", response.getheader("X-Content-Type-Options"))

    def test_a_port_in_use_is_a_sentence_not_a_traceback(self):
        import contextlib
        import io
        import socket
        from unittest import mock

        taken = socket.socket()
        self.addCleanup(taken.close)
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        port = taken.getsockname()[1]
        err = io.StringIO()
        # Should the port somehow be bound anyway, fail rather than serve forever or open a browser.
        with mock.patch.object(serving.http.server.ThreadingHTTPServer, "serve_forever",
                               side_effect=AssertionError("a port already in use was bound")), \
                mock.patch("webbrowser.open"), contextlib.redirect_stderr(err):
            status = serving.serve(Path(tempfile.gettempdir()), "site", port)
        self.assertEqual(2, status)
        self.assertIn(f"port {port}", err.getvalue())
        self.assertIn("--port", err.getvalue())

    def test_the_site_itself_keeps_its_own_types(self):
        for name in ("docs/wiki/site/index.html", "docs/wiki/site/assets/wiki.css",
                     "docs/wiki/site/images/a-picture.png"):
            with self.subTest(name=name):
                self.assertIsNone(serving.shown_as_text(name),
                                  "the site's own files were overridden to plain text")


class PackageTests(unittest.TestCase):
    """The property that makes this a package rather than one project's script."""

    # Words that would tie the tool to whatever it happens to document. It is meant to be installed by
    # any project, and a single one of these in it makes that a rewrite rather than an install.
    SOMEBODY_ELSES = ("deer", "wolf", "wolves", "pine", "settlement", "colonial", "wildlife", "herd",
                      "pasture", "villager", "unreal", "blueprint", "laravel", "django", "rails",
                      "game", "games", "player", "players")

    def test_the_tool_names_nothing_about_any_project(self):
        # Whole words only: "DecodeError" is not a deer, and a directory tree is not a pine. A word that
        # is ordinary English on its own -- tree, bear -- is left out rather than matched and excused.
        for name in ("build.py", "cli.py", "config.py", "serve.py", "__init__.py",
                     "assets/template.html", "assets/wiki.css", "assets/wiki.js"):
            text = (PACKAGE / name).read_text(encoding="utf-8").lower()
            for word in self.SOMEBODY_ELSES:
                self.assertIsNone(re.search(r"\b" + word + r"\b", text),
                                  f"{name} names {word!r}; this package must not know it")

    def test_the_skill_is_written_into_a_directory_of_its_own_name(self):
        """A skill is found by its directory, and declares its name in its own front matter.

        Nothing joins the two but agreement, so a rename that changes one and not the other leaves a
        skill nobody can load and nothing that says so.
        """
        declared = re.search(r"^name:\s*(\S+)", (wiki.SKILL / "SKILL.md").read_text(encoding="utf-8"),
                             re.M)
        self.assertIsNotNone(declared, "the skill declares no name")
        self.assertEqual(cli.SKILL_NAME, declared.group(1))

    def test_sync_writes_the_skill_where_agents_look_for_it(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / ".agents/skills").mkdir(parents=True)
            (root / "docs/wiki").mkdir(parents=True)
            (root / "docs/wiki" / CONFIG).write_text(CONFIGURATION, encoding="utf-8")
            cli.sync(root, root / "docs/wiki")
            home = root / ".agents/skills" / cli.SKILL_NAME
            self.assertTrue((home / "SKILL.md").is_file())
            self.assertTrue((home / "references/page-standard.md").is_file())
            self.assertIn(f'version = "{wiki_version()}"',
                          (root / "docs/wiki" / CONFIG).read_text(encoding="utf-8"))

    def project(self):
        """A project with a wiki and an `.agents/skills` folder, on an older release of the tool."""
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        root = Path(work.name)
        (root / ".agents/skills").mkdir(parents=True)
        (root / "docs/wiki").mkdir(parents=True)
        (root / "docs/wiki" / CONFIG).write_text(
            CONFIGURATION.replace(f'version = "{wiki_version()}"', 'version = "0.0.0"'), encoding="utf-8")
        return root

    def sync(self, root, *options):
        """`wiki sync` as a person types it, and what it said."""
        import contextlib
        import io
        said = io.StringIO()
        with contextlib.redirect_stdout(said), contextlib.redirect_stderr(said):
            try:
                status = cli.main(["--root", str(root), "sync", *options])
            except SystemExit as refused:
                status = refused.code
        return status, said.getvalue()

    def shipped(self, name="SKILL.md"):
        return (wiki.SKILL / name).read_text(encoding="utf-8")

    def test_sync_follows_the_skills_folder_a_project_already_has(self):
        # .agents/skills wins where both exist, because .claude/skills is often a link to it; with neither,
        # the skill goes to .claude/skills.
        for folders, expected in (((".agents/skills", ".claude/skills"), ".agents/skills"),
                                  ((".claude/skills",), ".claude/skills"),
                                  ((), ".claude/skills")):
            with self.subTest(folders=folders):
                root = self.project()
                (root / ".agents/skills").rmdir()
                for folder in folders:
                    (root / folder).mkdir(parents=True, exist_ok=True)
                status, output = self.sync(root)
                self.assertEqual(0, status, output)
                self.assertTrue((root / expected / cli.SKILL_NAME / "SKILL.md").is_file(),
                                f"the skill did not go to {expected}")
                for other in sorted({".agents/skills", ".claude/skills"} - {expected}):
                    self.assertFalse((root / other / cli.SKILL_NAME).exists(), f"the skill also went to {other}")

    def test_sync_puts_the_skill_where_it_is_told(self):
        root = self.project()
        status, output = self.sync(root, "--skill-dir", "tools/skills")
        self.assertEqual(0, status, output)
        home = root / "tools/skills" / cli.SKILL_NAME
        self.assertEqual(self.shipped(), (home / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(self.shipped("references/page-standard.md"),
                         (home / "references/page-standard.md").read_text(encoding="utf-8"))
        self.assertFalse((root / ".agents/skills" / cli.SKILL_NAME).exists(),
                         "the skill went where the tool guessed, not where it was told")

    def test_sync_replaces_a_skill_that_has_fallen_behind(self):
        root = self.project()
        home = root / "tools/skills" / cli.SKILL_NAME
        home.mkdir(parents=True)
        (home / "SKILL.md").write_text("an older skill", encoding="utf-8")
        status, output = self.sync(root, "--skill-dir", "tools/skills")
        self.assertEqual(0, status, output)
        self.assertEqual(self.shipped(), (home / "SKILL.md").read_text(encoding="utf-8"))

    def test_sync_writes_every_file_the_skill_ships(self):
        root = self.project()
        status, output = self.sync(root)
        self.assertEqual(0, status, output)
        home = root / ".agents/skills" / cli.SKILL_NAME
        shipped = sorted(path.relative_to(wiki.SKILL) for path in wiki.SKILL.rglob("*.md"))
        self.assertTrue(shipped, "the skill ships no files")
        for name in shipped:
            written = home / name
            self.assertTrue(written.is_file(), f"sync did not write {name}")
            self.assertEqual((wiki.SKILL / name).read_text(encoding="utf-8"),
                             written.read_text(encoding="utf-8"))

    def test_sync_can_leave_the_skill_out(self):
        root = self.project()
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(0, status, output)
        self.assertFalse((root / ".agents/skills" / cli.SKILL_NAME).exists())
        self.assertFalse((root / ".claude").exists())
        self.assertIn(f'version = "{wiki_version()}"',
                      (root / "docs/wiki" / CONFIG).read_text(encoding="utf-8"),
                      "leaving the skill out must still record the release")

    def test_sync_refuses_to_both_leave_the_skill_out_and_place_it(self):
        root = self.project()
        status, output = self.sync(root, "--no-skill", "--skill-dir", "tools/skills")
        self.assertEqual(2, status)
        self.assertIn("not allowed with", output)
        self.assertFalse((root / "tools").exists())

    def test_sync_records_the_release_in_its_own_table_and_nowhere_else(self):
        # A [tool] table with no version, then a table holding a setting whose name starts with version.
        root = self.project()
        settings = root / "docs/wiki" / CONFIG
        settings.write_text(CONFIGURATION.replace(f'[tool]\nversion = "{wiki_version()}"\n',
                                                  '[tool]\n\n[notes]\nversion_label = "kept"\n'),
                            encoding="utf-8")
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(0, status, output)
        recorded = tomllib.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(wiki_version(), recorded.get("tool", {}).get("version"), "the release was not recorded")
        self.assertEqual({"version_label": "kept"}, recorded["notes"], "another table's setting was changed")

    def test_sync_keeps_the_line_endings_the_settings_file_was_written_with(self):
        root = self.project()
        settings = root / "docs/wiki" / CONFIG
        settings.write_bytes(settings.read_bytes().replace(b"\n", b"\r\n"))
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(0, status, output)
        written = settings.read_bytes()
        self.assertIn(f'version = "{wiki_version()}"\r\n'.encode(), written, "the release was not recorded")
        self.assertNotIn(b"\n", written.replace(b"\r\n", b""), "a line ending was changed")

    def test_sync_changes_nothing_on_the_version_line_but_its_value(self):
        version = wiki_version()
        for before, after in (('[tool]\r\nversion = "0.0.0"\n', f'[tool]\r\nversion = "{version}"\n'),
                              ('[tool]\nversion = "a\\"b"  # kept\n', f'[tool]\nversion = "{version}"  # kept\n'),
                              ('[tool]\nversion = "0.0.0"   \n', f'[tool]\nversion = "{version}"   \n')):
            with self.subTest(before=before):
                root = self.project()
                settings = root / "docs/wiki" / CONFIG
                head = CONFIGURATION.replace(f'[tool]\nversion = "{version}"\n', "")
                settings.write_bytes((head + before).encode("utf-8"))
                status, output = self.sync(root, "--no-skill")
                self.assertEqual(0, status, output)
                self.assertEqual((head + after).encode("utf-8"), settings.read_bytes())

    def test_sync_keeps_a_comment_beside_the_version(self):
        root = self.project()
        settings = root / "docs/wiki" / CONFIG
        text = settings.read_text(encoding="utf-8").replace('version = "0.0.0"', 'version = "0.0.0"  # pinned on purpose')
        settings.write_text(text, encoding="utf-8")
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(0, status, output)
        self.assertIn(f'version = "{wiki_version()}"  # pinned on purpose', settings.read_text(encoding="utf-8"))

    def test_sync_records_the_release_under_a_header_that_carries_a_comment(self):
        root = self.project()
        settings = root / "docs/wiki" / CONFIG
        settings.write_text(CONFIGURATION.replace(f'[tool]\nversion = "{wiki_version()}"\n',
                                                  '[tool]  # written by wiki sync\nname = "kept"\n'),
                            encoding="utf-8")
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(0, status, output)
        recorded = tomllib.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual({"name": "kept", "version": wiki_version()}, recorded.get("tool"))

    def test_sync_records_the_release_when_only_a_comment_names_its_table(self):
        root = self.project()
        settings = root / "docs/wiki" / CONFIG
        settings.write_text(CONFIGURATION.replace(f'[tool]\nversion = "{wiki_version()}"\n',
                                                  "# [tool] is written by wiki sync\n"), encoding="utf-8")
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(0, status, output)
        recorded = tomllib.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(wiki_version(), recorded.get("tool", {}).get("version"), "the release was not recorded")

    def test_sync_refuses_a_settings_file_it_cannot_read(self):
        root = self.project()
        settings = root / "docs/wiki" / CONFIG
        settings.write_text("[site\nname = ", encoding="utf-8")
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(1, status, output)
        self.assertIn(f"{CONFIG} is unreadable", output)
        self.assertEqual("[site\nname = ", settings.read_text(encoding="utf-8"), "an unreadable file was written")

    def test_sync_refuses_to_record_a_release_that_would_change_another_setting(self):
        # [[tool]] is a list of tables, where a release has no single place to go.
        root = self.project()
        settings = root / "docs/wiki" / CONFIG
        text = CONFIGURATION.replace(f'[tool]\nversion = "{wiki_version()}"\n', '[[tool]]\nname = "a"\n')
        settings.write_text(text, encoding="utf-8")
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(1, status, output)
        self.assertIn("by hand", output)
        self.assertEqual(text, settings.read_text(encoding="utf-8"), "the file was written anyway")

    def test_sync_with_no_settings_file_is_a_sentence_not_a_traceback(self):
        root = self.project()
        (root / "docs/wiki" / CONFIG).unlink()
        status, output = self.sync(root, "--no-skill")
        self.assertEqual(1, status, output)
        self.assertIn(f"there is no {CONFIG}", output)

    def test_the_skill_names_nothing_about_any_project(self):
        # The skill ships to every project too, and its worked example is the part most likely to carry
        # somebody's animals in it.
        # Asked of the tool rather than assumed: the skill sits beside the builder in a checkout and
        # inside it in a built wheel, and this property has to hold in both.
        shipped = sorted(wiki.SKILL.rglob("*.md"))
        self.assertGreaterEqual(len(shipped), 2, "no skill files were found to scan")
        for path in shipped:
            name = path.relative_to(wiki.SKILL)
            text = path.read_text(encoding="utf-8").lower()
            for word in self.SOMEBODY_ELSES:
                self.assertIsNone(re.search(r"\b" + word + r"\b", text),
                                  f"{name} names {word!r}; this package must not know it")


if __name__ == "__main__":
    unittest.main()
