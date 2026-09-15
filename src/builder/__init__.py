"""Build a wiki a person can read, from markdown a person wrote.

The tool knows nothing about whatever it documents. It is handed pages, a configuration file, and a
picture ledger, and it writes a site. What it adds beyond rendering is a set of refusals: a page that
states something and cites nothing, a heading that asks a question instead of naming its section, a page
longer than anyone will read, a picture whose subject has changed since the picture was made.
"""

__version__ = "0.3.1"
