#!/usr/bin/env python3
"""Serve a directory, showing source and text files in the browser rather than downloading them.

The stock handler answers a .md file with text/markdown and a .h with an unknown type, and a browser
downloads both instead of displaying them. A wiki whose references point at files is unusable that way:
following a citation gets you a file on disk, not the passage you wanted to read.

Everything a citation can reach is therefore served as plain text. Loopback only; this shows the whole
directory it is given.
"""

import argparse
import functools
import http.server
import sys
import urllib.parse
from pathlib import Path

# Anything a reference might point at. A type not listed here keeps whatever the stock handler decides.
AS_TEXT = (".md", ".txt", ".rst", ".toml", ".ini", ".cfg", ".conf", ".env",
           ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".go", ".rs", ".java", ".kt", ".swift",
           ".py", ".rb", ".php", ".pl", ".lua", ".sh", ".bash", ".zsh", ".sql",
           ".js", ".jsx", ".ts", ".tsx", ".vue", ".json", ".yml", ".yaml", ".xml", ".gradle")


PLAIN = "text/plain; charset=utf-8"

# The names a request may address the server by: it listens on 127.0.0.1 only.
LOCAL_NAMES = ("127.0.0.1", "localhost", "::1")


def shown_as_text(path):
    """The type to answer with, or None to leave the decision where it was.

    A function rather than a method so it can be tested without standing up a request: what a reference
    is answered with is the whole point of this file.
    """
    return PLAIN if Path(path).suffix.lower() in AS_TEXT else None


class Handler(http.server.SimpleHTTPRequestHandler):
    """The stock handler, plus plain text for the files a reference can reach, and nothing cached."""

    def guess_type(self, path):
        return shown_as_text(path) or super().guess_type(path)

    def send_head(self):
        # A web page can give its own domain the address 127.0.0.1 and read this server as its own site, so
        # a request addressed by any other name is refused.
        try:
            host = urllib.parse.urlsplit("//" + (self.headers.get("Host") or "")).hostname
        except ValueError:
            host = None
        if host not in LOCAL_NAMES:
            self.send_error(403, "wiki serve answers only at 127.0.0.1 or localhost")
            return None
        # The project holds what no page links to and nobody should read through a browser: a .env, and
        # the remotes and credentials under .git. Decoded first, so %2Egit is refused as .git is, and judged
        # again where a link in the project really leads, so a link cannot reach .git or a folder such as
        # ~/.ssh. Inside the project only the parts below it count, so a project kept in a hidden folder
        # is still served, and so is a site folder linked from elsewhere.
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        root = Path(self.directory).resolve()
        target = Path(self.translate_path(self.path)).resolve()
        real = target.relative_to(root).parts if target.is_relative_to(root) else target.parts
        if any(part.startswith(".") for part in path.split("/")) or any(part.startswith(".") for part in real):
            self.send_error(404, "File not found")
            return None
        return super().send_head()

    def end_headers(self):
        # Nothing here may be cached. The stock handler sends no cache headers at all, which leaves a
        # browser free to apply its own heuristic -- and it does: a stylesheet edited a minute ago goes on
        # being served from memory, so a change to the site does not appear and the change looks broken
        # rather than unfetched. This is a local server for reading a site that is rebuilt constantly;
        # there is nothing to gain by caching and a whole class of phantom bug to lose.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        # A file answered as text stays text: a browser that guessed from its contents could run it as a page.
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        """One line per request is noise while reading; a failure is not."""
        if not str(args[1] if len(args) > 1 else "").startswith("2"):
            super().log_message(fmt, *args)


def serve(root, site, port):
    """Serve the project and open the wiki in it.

    The document root is the PROJECT, not the site: a page's references point at the code they were read
    from, which sits above the site, and a browser cannot reach above the root it is served from. Links
    between pages stay relative, so the site is still publishable on its own.
    """
    import webbrowser

    url = f"http://127.0.0.1:{port}/{Path(site).as_posix().strip('/')}/"
    handler = functools.partial(Handler, directory=str(root))
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as error:
        print(f"wiki: cannot serve on port {port}: {error.strerror or error}; choose another with --port",
              file=sys.stderr)
        return 2
    print(f"wiki: serving {url}  (ctrl-c to stop)")
    with server:
        try:
            webbrowser.open(url)
        except Exception:  # pragma: no cover - a machine with no browser still serves
            pass
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--directory", default=".")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--site", default="")
    args = parser.parse_args(argv)
    return serve(Path(args.directory).resolve(), args.site, args.port)


if __name__ == "__main__":
    sys.exit(main())
