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
kicker = "what it is"
categories = ["Things"]
status = "approved"
intent = """
A thing exists so that something else can happen. It should be plain what it is for.
"""

[[infobox]]
group = "Facts"
rows = [
  { label = "Held to", value = "a promise", guaranteed = "THING-001" },
  { label = "Today", value = "a number" },
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
kicker = "the front"
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
kicker = "every purpose"
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
        self.assertIn("what it is", page)

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
        self.write("thing", PAGE.replace('{ label = "Today", value = "a number" }',
                                         '{ label = "Today", value = "a number", missing = true }'))
        self.build()
        page = (self.out / "thing/index.html").read_text(encoding="utf-8")
        self.assertIn("nocite", page)
        self.assertIn("[?]", page)

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

    def test_a_page_is_a_draft_unless_it_says_otherwise(self):
        """An agent may write a page. Deciding that it belongs in the wiki is the owner's."""
        self.write("proposal", PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal"))
        self.build()
        self.assertIn("proposal", self.drafts)

    def test_a_draft_is_built_so_it_can_be_read(self):
        self.write("proposal", PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal"))
        self.build()
        self.assertTrue((self.out / "proposal/index.html").is_file())

    def test_a_draft_says_it_is_one_before_it_says_anything_else(self):
        self.write("proposal", PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal"))
        self.build()
        page = (self.out / "proposal/index.html").read_text(encoding="utf-8")
        self.assertIn("This page is a draft", page)
        self.assertLess(page.index("This page is a draft"), page.index("<h2"))

    def test_a_draft_is_linked_from_nowhere(self):
        self.write("proposal", PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal"))
        self.build()
        for path in sorted(self.out.rglob("*.html")):
            if path.parent.name == "proposal" or path.parent.parent.name == "proposal":
                continue
            self.assertNotIn("proposal/", path.read_text(encoding="utf-8"),
                             f"{path.name} links to a page nobody has approved")

    def test_a_draft_is_not_in_the_collected_goals(self):
        self.write("proposal", PAGE.replace('status = "approved"\n', "")
                   .replace("A thing exists so that something else can happen.", "A proposal is made."))
        self.nav(CONFIGURATION.replace('pages = ["thing"]', 'pages = ["thing", "proposal"]'))
        self.build()
        goals = (self.out / "goals/index.html").read_text(encoding="utf-8")
        self.assertNotIn("A proposal is made.", goals)

    def test_a_draft_need_not_be_reachable(self):
        # It is deliberately in no navigation section; that must not be an error.
        self.write("proposal", PAGE.replace('status = "approved"\n', "").replace("A thing", "A proposal"))
        self.assertEqual([], [p for p in wiki.uncited_problems(self.root) if "proposal" in p])
        self.build()

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
        self.write("thing", PAGE.replace('kicker = "what it is"',
                                         'kicker = "what it is"\nimage = "absent.png"'))
        self.refused("pictures.toml")

    def test_a_citation_does_not_count_against_the_reading_budget(self):
        long_note = "[^why]: " + ("word " * 300)
        self.write("thing", PAGE.replace("[^why]: The reason — `Source/Thing.h`.", long_note))
        counts, goals_words = self.build()
        self.assertEqual([], wiki.budget_problems(counts, goals_words, self.budget),
                         "citing a source pushed a page over its budget")

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
        """The entry point dev-check.sh and dev-wiki.sh actually call, and the status they act on."""
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                status = cli.main(argv)
            except wiki.WikiError as error:
                print(f"build-wiki: {error}", file=err)
                status = 1
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
                      "pasture", "villager", "unreal", "blueprint", "laravel", "django", "rails")

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
            self.assertTrue((home / "references/the-standard.md").is_file())
            self.assertIn(f'version = "{wiki_version()}"',
                          (root / "docs/wiki" / CONFIG).read_text(encoding="utf-8"))

    def test_the_skill_names_nothing_about_any_project(self):
        # The skill ships to every project too, and its worked example is the part most likely to carry
        # somebody's animals in it.
        # Asked of the tool rather than assumed: the skill sits beside the builder in a checkout and
        # inside it in a built wheel, and this property has to hold in both.
        for name in ("SKILL.md", "references/the-standard.md"):
            text = (wiki.SKILL / name).read_text(encoding="utf-8").lower()
            for word in self.SOMEBODY_ELSES:
                self.assertIsNone(re.search(r"\b" + word + r"\b", text),
                                  f"{name} names {word!r}; this package must not know it")


if __name__ == "__main__":
    unittest.main()
