"""URL audit for every machine-readable file the site generator and packages emit.

Why this exists: two rounds in a row, link checks passed while llms.txt pointed at
`.../lgd-skill-reviewrubric.json` (missing slash) and a package glued a URL to a full-width
comma. Both are invisible to "does the page have content" assertions, and both only bite
the machine reader. So the rule here is: every URL we publish must be parseable and
resolvable, whether or not anyone clicks it.

Checks, all static (no network):
  1. no site-root URL is immediately followed by another character (missing slash)
  2. no URL is immediately followed by CJK punctuation or CJK characters (glued link)
  3. every URL on our own site maps to a file that exists in docs/
  4. no URL contains whitespace or stray quotes
Exit code 1 if anything fails.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(HERE, "docs")
SITE = "https://zhaoxinghua09-cell.github.io/lgd-skill-review"
RAW = "https://raw.githubusercontent.com/zhaoxinghua09-cell/lgd-skill-review/main"
URL_RE = re.compile(r"https?://[A-Za-z0-9\-._~:/?#@!$&'()*+,;=%]+")
CJK = re.compile(r"[，。、；：！？（）【】《》「」…—·]|[^\x00-\x7F]")


def _trim(url):
    """Drop markdown/bracket punctuation that belongs to the surrounding prose, not the URL."""
    pairs = {")": "(", "]": "[", "}": "{"}
    while url and url[-1] in pairs and url.count(url[-1]) > url.count(pairs[url[-1]]):
        url = url[:-1]
    while url and url[-1] in ",;":
        url = url[:-1]
    return url


def collect(path, text):
    """Yield (url, problem) for every suspicious URL occurrence in text."""
    for m in URL_RE.finditer(text):
        raw = m.group(0)
        url = _trim(raw)
        after = text[m.start() + len(url):m.start() + len(url) + 1]
        if after and CJK.match(after):
            yield url, "URL glued to CJK text/punctuation: ...%s%s" % (url[-24:], after)
        if url.startswith(SITE) and not url.startswith(SITE + "/") and url != SITE:
            yield url, "site-root URL without a slash: ...%s" % url[-30:]
        for ch in ('"', "'", "<", ">", "`"):
            if ch in url:
                yield url, "URL contains stray character %r" % ch
                break


def local_path(url):
    if url == SITE or url == SITE + "/":
        return os.path.join(DOCS, "index.html")
    if not url.startswith(SITE + "/"):
        return None
    rel = url[len(SITE) + 1:]
    rel = rel.split("#")[0].split("?")[0]
    if not rel or rel.endswith("/"):
        rel = (rel + "index.html").lstrip("/")
    return os.path.join(DOCS, rel)


def main():
    fails = []
    targets = []
    for root, _, files in os.walk(DOCS):
        for f in files:
            if f.endswith((".html", ".json", ".txt", ".xml")) and f != "llms-full.txt.old":
                targets.append(os.path.join(root, f))
    # package-level machine files
    for pkg in ("summarize-pro", "debug-pro", "wechat-viral-topic", "lgd-skill-review"):
        p = os.path.join(os.path.dirname(HERE), pkg)
        for f in ("llms.txt", "AI-INDEX.json", "README.md"):
            fp = os.path.join(p, f)
            if os.path.isfile(fp):
                targets.append(fp)

    checked = 0
    for fp in targets:
        text = io.open(fp, encoding="utf-8", errors="replace").read()
        for url, problem in collect(fp, text):
            checked += 1
            fails.append("%s: %s  [%s]" % (os.path.basename(fp), problem, url))
        # resolvability of our own site URLs
        for m in URL_RE.finditer(text):
            lp = local_path(_trim(m.group(0)))
            if lp is not None and not os.path.isfile(lp):
                fails.append("%s: site URL has no file behind it: %s" % (os.path.basename(fp), _trim(m.group(0))))

    print("files=%d  problems=%d" % (len(targets), len(fails)))
    for f in fails[:25]:
        print("  - " + f)
    print("ALL PASS" if not fails else "FAIL")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
