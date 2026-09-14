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
from .build import (ASSETS, SKILL, bless, build, check, report, wiki_of)
from .config import CONFIG, WikiError, record_version
from .serve import serve

PORT = 8787

# The directory a skill lives in is named for the skill. Named once here so the tool and the skill's own
# front matter cannot drift apart.
SKILL_NAME = "writing-wiki-pages"


def skill_home(root):
    """Where this project keeps its agent skills.

    Two conventions exist and a project has usually picked one already; the tool follows rather than
    imposes. `.agents/skills` is preferred where both are present because `.claude/skills` is often a
    symlink to it, and writing through the symlink would be writing to the same place twice.
    """
    for name in (".agents/skills", ".claude/skills"):
        if (root / name).is_dir():
            return root / name / SKILL_NAME
    return root / ".claude/skills" / SKILL_NAME


def sync(root, wiki):
    """Put the skill where this project's agents will read it, and record the release it came from.

    The skill has to live in the project rather than inside the package: agents read it from the
    repository, and a change to how pages must be written belongs in a diff somebody reviews.
    """
    home = skill_home(root)
    (home / "references").mkdir(parents=True, exist_ok=True)
    written = []
    for source, destination in ((SKILL / "SKILL.md", home / "SKILL.md"),
                                (SKILL / "references" / "the-standard.md",
                                 home / "references" / "the-standard.md")):
        text = source.read_text(encoding="utf-8")
        if not destination.is_file() or destination.read_text(encoding="utf-8") != text:
            destination.write_text(text, encoding="utf-8", newline="\n")
            written.append(destination.relative_to(root))
    record_version(wiki, __version__)
    for path in written:
        print(f"wiki: wrote {path}")
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
    commands.add_parser("sync", parents=[place],
                        help="write the skill into this project and record the release")
    served = commands.add_parser("serve", parents=[place], help="build, serve, and open a browser at it")
    served.add_argument("--port", type=int, default=PORT)
    published = commands.add_parser("publish", parents=[place],
                                     help="build with clean addresses, for a host")
    published.add_argument("out", type=Path)
    player = commands.add_parser("player", parents=[place], help="build the player's view into a directory")
    player.add_argument("out", type=Path)
    blessed = commands.add_parser("bless", parents=[place],
                                  help="record that a picture is still true, and why")
    blessed.add_argument("picture")
    blessed.add_argument("reason")

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
        return sync(root, wiki)

    if command == "bless":
        print(bless(root, args.picture, args.reason, wiki))
        return 0

    if command == "check":
        problems, counts, goals_words, budget = check(root, wiki, __version__)
        for problem in problems:
            print("wiki: " + problem, file=sys.stderr)
        report(counts, goals_words, budget)
        print("wiki: %d pages, %d problems" % (len(counts), len(problems)))
        return 1 if problems else 0

    out = {"publish": lambda: args.out.resolve(),
           "player": lambda: args.out.resolve()}.get(command, lambda: wiki / "site")()
    if not guard_output(out):
        return 2
    out.mkdir(parents=True, exist_ok=True)
    counts, goals_words, budget, drafts = build(
        root, out, "player" if command == "player" else "internal",
        links="clean" if command == "publish" else "file", wiki_dir=wiki)
    report(counts, goals_words, budget, drafts)
    print("wiki: %d pages written to %s" % (len(counts), out))

    if command == "publish":
        print(f"wiki: {out} uses clean addresses and needs a server; the site itself opens without one")
    if command == "serve":
        return serve(root, out.relative_to(root) if out.is_relative_to(root) else out, args.port)
    return 0
