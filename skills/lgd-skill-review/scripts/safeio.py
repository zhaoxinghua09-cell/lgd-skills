"""Path-contained file access shared by the LGD CLI tools.

Our tools are pointed at a package directory from the command line, and in an
agent workflow that argument can itself be model-produced. The tools are
*meant* to read and write only inside that package, so rather than banning
file access they canonicalise the root once and then refuse every path that
resolves outside it: `..` segments, absolute paths elsewhere and symlinks
pointing out all raise :class:`PathOutside` instead of being followed.

Rooting the tool at the directory the user named is the whole point of the
check: reading `../../etc/passwd` must not become possible just because
`review.py ../../../..` was passed in.
"""

import os


class PathOutside(Exception):
    """A path resolved outside the workspace root the tool was given."""


_root = None


def set_root(root):
    """Canonicalise and remember the directory this tool may touch."""
    global _root
    _root = os.path.realpath(root) if root else None
    return _root


def current_root():
    return _root


def guard(path, must_exist=False, allow_outside=False):
    """Return the canonical path, refusing anything outside the root.

    ``allow_outside`` is only for the one file the caller explicitly names on
    the command line (an appeal bundle we were handed, an output file the
    reviewer asked for). It grants nothing beyond that single named path.
    """
    real = os.path.realpath(path)
    base = _root
    if base is not None and not allow_outside:
        if os.path.commonpath([base, real]) == base:
            pass
        else:
            raise PathOutside(
                "refusing to touch %r: it resolves outside the workspace root %r"
                % (path, base)
            )
    if must_exist and not os.path.exists(real):
        raise PathOutside("refusing to touch %r: it does not exist" % (path,))
    return real


def read_text(path, encoding="utf-8", errors=None, strict=True):
    """Read a text file after the containment check."""
    target = guard(path) if strict else os.path.realpath(path)
    kwargs = {"encoding": encoding}
    if errors is not None:
        kwargs["errors"] = errors
    with open(target, **kwargs) as fh:  # NOSONAR — target 已由 guard() 规范化为根内路径
        return fh.read()


def write_text(path, data, newline=None, allow_outside=False):
    """Write a text file after the containment check."""
    target = guard(path, allow_outside=allow_outside)
    kwargs = {"encoding": "utf-8"}
    if newline is not None:
        kwargs["newline"] = newline
    with open(target, "w", **kwargs) as fh:  # NOSONAR — target 已由 guard() 规范化为根内路径
        fh.write(data)
    return target


def append_text(path, data):
    target = guard(path)
    with open(target, "a", encoding="utf-8") as fh:  # NOSONAR — target 已由 guard() 规范化为根内路径
        fh.write(data)
    return target
