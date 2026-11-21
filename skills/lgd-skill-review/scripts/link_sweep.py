#!/usr/bin/env python3
"""Link sweep over the published site.

Anyone can break a nav link in one commit. This checks every internal href and asset reference on every
published page and reports non-200s. External links are listed but not fetched (rate limits, and the
point here is our own surface).
"""
import os
import re
import sys
import urllib.request

BASE = "https://zhaoxinghua09-cell.github.io/lgd-skill-review"
PAGES = ["index.html", "rubric.html", "skill-review.html", "quickfix.html", "benchmark.html",
         "badge.html", "audits.html", "registry.html", "discover.html"]

HREF = re.compile(r'(?:href|src)="([^"#]+)"')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "lgd-link-sweep"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()


def main():
    bad, checked = [], 0
    for page in PAGES:
        try:
            status, body = get("%s/%s" % (BASE, page))
        except Exception as e:
            bad.append((page, "page itself", str(e)))
            continue
        if status != 200:
            bad.append((page, "page itself", "HTTP %s" % status))
            continue
        text = body.decode("utf-8", "replace")
        for ref in sorted(set(HREF.findall(text))):
            if ref.startswith(("http://", "https://")):
                if not ref.startswith(BASE):
                    continue
                ref = ref[len(BASE):]
            if ref.startswith("./"):
                ref = ref[2:]
            if not ref or ref.startswith("../"):
                continue
            checked += 1
            try:
                s, _ = get("%s/%s" % (BASE, ref))
                if s != 200:
                    bad.append((page, ref, "HTTP %s" % s))
            except Exception as e:
                bad.append((page, ref, str(e)[:60]))
    print("checked %d internal refs across %d pages" % (checked, len(PAGES)))
    if bad:
        print("BROKEN:")
        for page, ref, why in bad:
            print("  %s -> %s (%s)" % (page, ref, why))
        return 1
    print("all 200")
    return 0


if __name__ == "__main__":
    sys.exit(main())
