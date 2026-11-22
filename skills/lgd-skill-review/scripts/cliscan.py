"""Linear scanners shared by review.py and quickfix.py.

Both used to parse CLI declarations and front-matter keys with regular
expressions. SonarCloud flagged those patterns (python:S8786) as super-linear:
nested quantifiers like ``\\s*:\\s*(.*)`` can backtrack badly on a long line, and
front-matter is exactly where long lines live. A plain string walk is linear by
construction and easy to audit, so that is what we use here.
"""

QUOTE = '"'


def split_key(line):
    """Split a ``key: value`` front-matter line; None if it is not one.

    Keys are ``[A-Za-z0-9_-]+`` — no regex, no backtracking, no ambiguity about
    whether the space before the colon belongs to the key or the separator.
    """
    if not line or line[0] in " \t-":
        return None
    idx = line.find(":")
    if idx <= 0:
        return None
    key = line[:idx].strip()
    if not key:
        return None
    for ch in key:
        if not (ch.isascii() and (ch.isalnum() or ch in "_-")):
            return None
    return key, line[idx + 1:].strip()


def _declare(src, marker):
    """Collect the quoted token that follows ``marker(`` in ``src``."""
    out = set()
    start = src.find(marker)
    while start != -1:
        window = src[start + len(marker):start + len(marker) + 200]
        q = window.find(QUOTE)
        if q != -1:
            close = window.find(QUOTE, q + 1)
            if close > q + 1:
                out.add(window[q + 1:close])
        start = src.find(marker, start + 1)
    return out


def declared(src):
    """Return the flags (``--name``) and subcommands a script declares.

    Reads what ``add_argument("--x"`` and ``add_parser("x"`` actually say, which
    is the point: the published help must match the implementation.
    """
    flags = {"--" + f.lstrip("-") for f in _declare(src, "add_argument(")
             if f.lstrip("-").replace("-", "").isalnum()}
    subs = {s for s in _declare(src, "add_parser(") if s.replace("-", "_").isalnum()}
    return {"flags": sorted(flags), "subcommands": sorted(subs)}
