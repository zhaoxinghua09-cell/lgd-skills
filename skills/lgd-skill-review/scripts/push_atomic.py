#!/usr/bin/env python3
"""Publish several files to a GitHub repo in ONE commit (atomic).

Why this exists
---------------
Writing files one by one through the Contents API produces one commit per file.
A CI run can therefore land on an intermediate tree that is genuinely broken
(it happened: url_audit.py landed before docs/leaderboard.json, so the check
correctly failed on a half-applied publish). Publishing through the git data
API - blobs -> one tree -> one commit -> one ref update - makes the same batch
either fully visible or not visible at all, so CI only ever sees a consistent
tree.

Usage
-----
    python scripts/push_atomic.py <owner/repo> <local-root> "<message>" <path>...
    python scripts/push_atomic.py <owner/repo> <local-root> "<message>" "!old/file"  # delete

Token is read from $env:GH_PAT. Nothing is printed except the resulting commit.
"""
import base64
import json
import os
import sys
import urllib.request

API = "https://api.github.com"


def _req(method, url, payload=None, token=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", "Bearer %s" % token)
    req.add_header("User-Agent", "lgd-push-atomic")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main(argv):
    if len(argv) < 4:
        sys.exit(__doc__)
    slug, root, message = argv[0], argv[1], argv[2]
    paths = argv[3:]
    token = os.environ.get("GH_PAT")
    if not token:
        sys.exit("GH_PAT is not set")

    ref = _req("GET", "%s/repos/%s/git/ref/heads/main" % (API, slug), token=token)
    parent = ref["object"]["sha"]
    parent_commit = _req("GET", "%s/repos/%s/git/commits/%s" % (API, slug, parent), token=token)
    base_tree = parent_commit["tree"]["sha"]
    print("parent: %s (tree %s)" % (parent[:10], base_tree[:10]))

    entries, changed = [], []
    for p in paths:
        wanted = p[1:] if p.startswith("!") else p
        local = os.path.join(root, wanted)
        if p.startswith("!"):
            entries.append({"path": wanted, "mode": "100644", "type": "blob", "sha": None})
            changed.append("D " + wanted)
            continue
        if not os.path.isfile(local):
            sys.exit("missing local file: %s" % local)
        with open(local, "rb") as fh:
            raw = fh.read()
        blob = _req("POST", "%s/repos/%s/git/blobs" % (API, slug),
                    {"content": base64.b64encode(raw).decode(),
                     "encoding": "base64"}, token=token)
        entries.append({"path": wanted, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        changed.append("M " + wanted)

    tree = _req("POST", "%s/repos/%s/git/trees" % (API, slug),
                {"base_tree": base_tree, "tree": entries}, token=token)
    commit = _req("POST", "%s/repos/%s/git/commits" % (API, slug),
                  {"message": message, "tree": tree["sha"], "parents": [parent]}, token=token)
    _req("PATCH", "%s/repos/%s/git/refs/heads/main" % (API, slug),
         {"sha": commit["sha"], "force": False}, token=token)

    # read back: the ref must point exactly at the new commit, with one parent.
    check = _req("GET", "%s/repos/%s/git/ref/heads/main" % (API, slug), token=token)
    if check["object"]["sha"] != commit["sha"]:
        sys.exit("ref did not move to the new commit")
    print("commit: %s" % commit["sha"])
    print("url: https://github.com/%s/commit/%s" % (slug, commit["sha"]))
    print("files (%d, one commit): %s" % (len(changed), ", ".join(changed)))


if __name__ == "__main__":
    main(sys.argv[1:])
