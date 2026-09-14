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
subtitle = "what it is"
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

        The references are exempt and only they: naming a path is what they are for, and a player build
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
        self.assertIn('<p class="sub">what it is</p>', page)

    def test_a_page_still_using_kicker_is_told_to_rename_it(self):
        # The subtitle was called kicker before. Reading it silently as nothing would lose every one.
        self.write("thing", PAGE.replace('subtitle = "what it is"', 'kicker = "what it is"'))
        self.refused("rename kicker to subtitle")

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
        self.assertIn("- [A thing](thing/index.md): what it is", index)

    def test_a_source_view_links_to_the_markdown_file(self):
        # Anyone can open a page as pure markdown from its Source view. The owner, 2026-09-14: "we would
        # want the docs to be viewable as pure md file content", and then "update markdown tab to be in
        # source. but a link to the markdown file instead".
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        source = (self.out / "thing/source/index.html").read_text(encoding="utf-8")
        self.assertIn('<a href="../index.md">index.md</a>', source)
        self.assertNotIn(">Markdown</a>", page, "the tab row still carries a Markdown tab")
        self.assertNotIn(">Markdown</a>", source, "the tab row still carries a Markdown tab")
        self.assertTrue((self.out / "thing/index.md").is_file())

    def test_a_player_build_has_no_markdown_copy_and_no_agent_index(self):
        # The copy is the page as written, references and marks included, which a player build withholds.
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "player"'))
        self.build("player")
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
        # The owner, 2026-09-14: "a table row must have at least one citation in any of the columns of its
        # row". One cited row no longer covers the rows beside it.
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
                ('subtitle = "what it is"', 'subtitle = "the tool that builds this wiki"', "subtitle"),
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
        # The owner, 2026-09-14: "references can use external documentation to cite how it is".
        self.write("thing", PAGE.replace(
            "[^why]: The reason — `Source/Thing.h`.",
            "[^why]: Host Docs — [Custom domains](https://docs.example.com/pages/custom-domains/): a\n"
            "    subdomain needs a `CNAME` record."))
        self.assertEqual([], wiki.citation_problems(self.root))

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

    def test_a_player_build_carries_no_requirement_identifier_anywhere(self):
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "player"'))
        self.build("player")
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

    def test_a_player_build_carries_no_infobox_citation(self):
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "player"'))
        self.build("player")
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

    # A link to a page the wiki does not have. The owner, 2026-09-14: "then its red instead of blue. and
    # that could be part of our dead link checks".

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

    def test_a_markdown_table_is_drawn_as_a_wiki_table(self):
        # Without the class, a page's own table had no borders, no header row and no padding.
        self.write("thing", PAGE.replace("It does it slowly.[^why]", "| a | b |\n|---|---|\n| c[^why] | d |"))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="wt"><table class="w">', page)
        self.assertIn("</table></div>", page)
        self.assertNotIn("<table>", page)

    def test_a_count_of_one_is_singular(self):
        # "1 pages written" and "1 problems" were printed by every one-page build and one-problem check.
        self.write("thing", PAGE.replace('categories = ["Things"]', 'categories = ["Things"]\naudience = "player"'))
        _, output = self.run_main(["--root", str(self.root), "player", str(self.out)])
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
        """An agent may write a page. Deciding that it belongs in the wiki is the owner's."""
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
        self.assertIn("This page is a draft", page)
        self.assertLess(page.index("This page is a draft"), page.index("<h2"))

    def test_a_draft_is_in_the_sidebar(self):
        """The owner's ruling, 2026-09-14: "all pages should always be on the nav regardless of status"."""
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

    def test_a_draft_is_not_in_the_collected_goals(self):
        self.write("proposal", PAGE.replace('status = "approved"\n', "")
                   .replace("A thing exists so that something else can happen.", "A proposal is made."))
        self.nav(CONFIGURATION.replace('pages = ["thing"]', 'pages = ["thing", "proposal"]'))
        self.build()
        goals = (self.out / "goals/index.html").read_text(encoding="utf-8")
        self.assertNotIn("A proposal is made.", goals)

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

    def test_a_player_build_carries_no_internal_page(self):
        self.build("player")
        self.assertFalse((self.out / "thing/index.html").exists())

    def test_a_player_build_carries_no_source_view_no_citation_and_no_path(self):
        self.write("thing", PAGE.replace('categories = ["Things"]',
                                         'categories = ["Things"]\naudience = "player"'))
        self.build("player")
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertNotIn("Source/Thing.h", page)
        self.assertNotIn('class="cites"', page)
        self.assertNotIn('class="ref"', page)
        self.assertFalse((self.out / "thing/source/index.html").exists())

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
        shutil.rmtree(self.out)
        self.build()
        self.assertFalse((self.out / "thing/part").exists())

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

        The citation block is exempt and only there -- it exists to name paths, and a player build has
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

    def test_an_infobox_picture_with_no_ledger_entry_is_refused(self):
        self.write("thing", PAGE.replace('subtitle = "what it is"',
                                         'subtitle = "what it is"\nimage = "absent.png"'))
        self.refused("pictures.toml")

    def test_a_citation_does_not_count_against_the_reading_budget(self):
        long_note = "[^why]: " + ("word " * 300)
        self.write("thing", PAGE.replace("[^why]: The reason — `Source/Thing.h`.", long_note))
        counts, goals_words = self.build()
        self.assertEqual([], wiki.budget_problems(counts, goals_words, self.budget),
                         "citing a source pushed a page over its budget")

    def test_a_code_block_does_not_count_against_the_reading_budget(self):
        # A sample is copied or run, not read -- a prompt to hand an agent is a page of it. The owner,
        # 2026-09-14, chose not to count code blocks.
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

    def test_the_root_may_follow_the_command(self):
        # The wrapper the README gives a project passes --root after whatever command it was handed.
        self.build()
        status, output = self.run_main(["check", "--root", str(self.root),
                                        "--wiki", str(self.root / "docs/wiki")])
        self.assertEqual(0, status, output)

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
        a change look broken rather than unfetched, and that cost three rounds with the owner once.
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
                      "game", "games")

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
