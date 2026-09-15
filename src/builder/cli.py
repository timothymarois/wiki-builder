"""What `wiki` does when you type it.

Subcommands rather than flags, because the modes are genuinely exclusive: a build, a check, a blessing
and a sync are different jobs, and expressing them as flags meant the one that happened to be tested
first silently won.
"""

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__
from .build import (ASSETS, SITEMAP, SKILL, audit, bless, build, check, citation_counts, coverage,
                    families_report, missing_marks, report, wiki_of)
from .config import CONFIG, WikiError, read_config, record_version
from .serve import serve

PORT = 8787

# The directory a skill lives in is named for the skill. Named once here so the tool and the skill's own
# front matter cannot drift apart.
SKILL_NAME = "writing-wiki-pages"


def skill_home(root, directory=None):
    """Where this project keeps its agent skills.

    A folder the project names wins, relative to the project: it knows where its agents look better than
    any convention does. Otherwise two conventions exist and a project has usually picked one already;
    the tool follows rather than imposes. `.agents/skills` is preferred where both are present because
    `.claude/skills` is often a symlink to it, and writing through the symlink would be writing to the
    same place twice.
    """
    if directory is not None:
        return root / directory / SKILL_NAME
    for name in (".agents/skills", ".claude/skills"):
        if (root / name).is_dir():
            return root / name / SKILL_NAME
    return root / ".claude/skills" / SKILL_NAME


def sync(root, wiki, skill=True, directory=None):
    """Put the skill where this project's agents will read it, and record the release it came from.

    The skill has to live in the project rather than inside the package: agents read it from the
    repository, and a change to how pages must be written belongs in a diff somebody reviews. A project
    with no agents can leave it out; the release is recorded either way, because `check` compares
    against it whether or not anyone reads the skill.
    """
    written = []
    if skill:
        home = skill_home(root, directory)
        # Every file the skill ships, found rather than listed: a reference added to the skill and
        # missing from a list here would never reach a project, and nothing would say so.
        for source in sorted(SKILL.rglob("*.md")):
            destination = home / source.relative_to(SKILL)
            destination.parent.mkdir(parents=True, exist_ok=True)
            text = source.read_text(encoding="utf-8")
            if not destination.is_file() or destination.read_text(encoding="utf-8") != text:
                destination.write_text(text, encoding="utf-8", newline="\n")
                written.append(destination.relative_to(root) if destination.is_relative_to(root)
                               else destination)
    record_version(wiki, __version__)
    for path in written:
        print(f"wiki: wrote {path}")
    if not skill:
        print("wiki: the skill was left out, as asked")
    print(f"wiki: {CONFIG} records wiki-builder {__version__}")
    return 0


def guard_output(out):
    """Refuse to write a site over a directory this tool did not make.

    The build removes whatever it no longer produces, so `--out` pointing at the wrong place would take
    that directory's contents with it. A previous build is recognisable by the stylesheet it left.
    """
    if out.exists() and any(out.iterdir()) and not (out / "assets" / "wiki.css").is_file():
        print(f"wiki: {out} is not empty and was not written by this tool; remove it yourself if you "
              "meant to replace it", file=sys.stderr)
        return False
    return True


def main(argv=None):
    # Where the project and its wiki are, accepted before the command or after it. A wrapper that passes
    # them after whatever command it was handed is the natural one to write, and the README's does. They
    # are suppressed rather than defaulted on each command, so that leaving them off there does not undo
    # what was given before it. The top level declares its own: a parent's arguments are shared objects,
    # and giving them a default there would give it to every command too.
    place = argparse.ArgumentParser(add_help=False)
    place.add_argument("--root", type=Path, default=argparse.SUPPRESS,
                       help="the project; defaults to the working directory")
    place.add_argument("--wiki", type=Path, default=argparse.SUPPRESS,
                       help="where the wiki lives; defaults to <root>/docs/wiki")
    parser = argparse.ArgumentParser(prog="wiki", description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"wiki-builder {__version__}")
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="the project; defaults to the working directory")
    parser.add_argument("--wiki", type=Path, default=None,
                        help="where the wiki lives; defaults to <root>/docs/wiki")
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("build", parents=[place], help="render the pages into the site")
    commands.add_parser("check", parents=[place], help="every reason the wiki is not fit to read")
    commands.add_parser("coverage", parents=[place], help="list the source files no page cites")
    commands.add_parser("families", parents=[place],
                        help="list the child pages that share no declared layout")
    synced = commands.add_parser("sync", parents=[place],
                                 help="write the skill into the project and record the release")
    skill = synced.add_mutually_exclusive_group()
    skill.add_argument("--skill-dir", type=Path, default=None, metavar="DIR",
                       help="the folder to put the skill in, relative to the project; defaults to "
                            ".agents/skills, or .claude/skills")
    skill.add_argument("--no-skill", action="store_true",
                       help="record the release without writing the skill")
    served = commands.add_parser("serve", parents=[place], help="build, serve, and open a browser at it")
    served.add_argument("--port", type=int, default=PORT, help=f"the port to serve on; defaults to {PORT}")
    published = commands.add_parser("publish", parents=[place],
                                     help="build with clean addresses, for a host")
    published.add_argument("out", type=Path, metavar="OUT",
                           help="the folder to build into, relative to the working directory")
    user = commands.add_parser("user", parents=[place], help="build the user's view into a directory")
    user.add_argument("out", type=Path, metavar="OUT",
                        help="the folder to build into, relative to the working directory")
    blessed = commands.add_parser("bless", parents=[place],
                                  help="record that a picture is still true, and why")
    blessed.add_argument("picture", metavar="PICTURE", help="the picture's file name, as its record names it")
    blessed.add_argument("reason", metavar="REASON", help="why the picture is still true; it cannot be empty")
    audited = commands.add_parser("audit", parents=[place],
                                  help="record that pages were checked against the code today")
    audited.add_argument("pages", nargs="+", metavar="PAGE",
                         help="a page's path under pages, with or without .md, such as checks/budgets")

    args = parser.parse_args(argv)
    root = args.root.resolve()
    wiki = wiki_of(root, args.wiki)
    if not wiki.is_dir():
        print(f"wiki: no wiki at {wiki}", file=sys.stderr)
        return 2
    # A problem that stops the build is already a sentence for a person. Let it escape and they get a
    # traceback with that sentence buried in its last line.
    try:
        return run(args, root, wiki)
    except WikiError as error:
        print(f"wiki: {error}", file=sys.stderr)
        return 1


def run(args, root, wiki):
    """Do the one command asked for, and return its exit status."""
    command = args.command or "serve"

    if command == "sync":
        return sync(root, wiki, skill=not args.no_skill, directory=args.skill_dir)

    if command == "bless":
        print(bless(root, args.picture, args.reason, wiki))
        return 0

    if command == "audit":
        for line in audit(root, args.pages, wiki):
            print(line)
        return 0

    if command == "families":
        # A report, not a gate: whether pages are things of one kind is for a person to decide.
        for line in families_report(root, wiki):
            print("wiki: " + line)
        return 0

    if command == "coverage":
        found = coverage(root, wiki)
        if found is None:
            print("wiki: wiki.toml has no [coverage] table; add one naming the source files to count, such as "
                  '[coverage] include = ["src/**/*.py"]', file=sys.stderr)
            return 2
        # A report, not a gate: each gap is one line an agent can act on, and the command still succeeds.
        for name in found["uncited"]:
            print(f"wiki: {name} is cited by no page")
        for page, name in found["missing"]:
            print(f"wiki: {page} cites {name}, which does not exist")
        total, gone = len(found["files"]), len(found["missing"])
        print("wiki: %d of %d source file%s cited; %d citation%s a file that does not exist"
              % (total - len(found["uncited"]), total, "" if total == 1 else "s", gone,
                 " names" if gone == 1 else "s name"))
        return 0

    if command == "check":
        problems, counts, goals_words, budget = check(root, wiki, __version__)
        for problem in problems:
            print("wiki: " + problem, file=sys.stderr)
        # Not problems: each is an answer, and together they are the work that remains.
        for mark in missing_marks(root, wiki):
            print("wiki: " + mark)
        report(counts, goals_words, budget, citations=citation_counts(root, wiki))
        print("wiki: %d page%s, %d problem%s" % (len(counts), "" if len(counts) == 1 else "s",
                                                len(problems), "" if len(problems) == 1 else "s"))
        return 1 if problems else 0

    out = {"publish": lambda: args.out.resolve(),
           "user": lambda: args.out.resolve()}.get(command, lambda: wiki / "site")()
    if not guard_output(out):
        return 2
    out.mkdir(parents=True, exist_ok=True)
    counts, goals_words, budget, drafts = build(
        root, out, "user" if command == "user" else "internal",
        links="clean" if command == "publish" else "file", wiki_dir=wiki,
        sitemap=command in ("publish", "user"))
    report(counts, goals_words, budget, drafts, citation_counts(root, wiki))
    print("wiki: %d page%s written to %s" % (len(counts), "" if len(counts) == 1 else "s", out))
    if command in ("publish", "user"):
        url = read_config(wiki)[0].get("url")
        if url:
            listed = (out / SITEMAP).read_text(encoding="utf-8").count("<url>")
            print("wiki: %s lists %d address%s under %s/" % (SITEMAP, listed, "" if listed == 1 else "es",
                                                              url.rstrip("/")))
        else:
            print(f"wiki: set site.url in wiki.toml to write {SITEMAP}")

    if command == "publish":
        print(f"wiki: {out} uses clean addresses and needs a server; the site itself opens without one")
    if command == "serve":
        # `wiki` with no command serves too, and only the serve command declares a port.
        return serve(root, out.relative_to(root) if out.is_relative_to(root) else out,
                     getattr(args, "port", PORT))
    return 0
