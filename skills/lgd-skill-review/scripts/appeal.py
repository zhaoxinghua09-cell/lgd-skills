#!/usr/bin/env python3
"""Appeal intake: re-measure one dimension and rule on it.

Honest scope: automation only re-measures. It never judges whether the appealer's argument is good.
- dimension now full        -> OVERTURNED （扣分已消失）
- gap shrank               -> PARTIALLY ACCEPTED
- gap unchanged / grew     -> UPHELD

Args: <issue_number> <owner/repo> <dimension> <verdict_file>
"""
import json
import os
import re
import sys
import urllib.request


def comments(owner, repo, number):
    url = "https://api.github.com/repos/%s/%s/issues/%d/comments?per_page=100" % (owner, repo, number)
    h = {"User-Agent": "lgd-appeal", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def last_machine(bodies):
    for body in reversed(bodies):
        if "schema_version" not in body:
            continue
        m = re.search(r'```json\s*(\{.*?\})\s*```', body, re.S)
        if not m:
            continue
        try:
            data = json.loads(m.group(1))
        except ValueError:
            continue
        if data.get("dimensions"):
            return data
    return None


def main():
    number, slug, dim, path = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    owner, repo = slug.split("/", 1)
    text = open(path, encoding="utf-8").read()
    m = re.search(r'```json\s*(\{.*?\})\s*```', text, re.S)
    new = json.loads(m.group(1)) if m else {}
    dims_now = new.get("dimensions") or {}

    try:
        prev = last_machine([c.get("body", "") for c in comments(owner, repo, number)])
    except Exception as e:
        sys.stderr.write("appeal baseline unreadable: %s\n" % e)
        prev = None

    dim = dim.strip().lower()
    if dim not in dims_now:
        print("申诉维度不存在 / unknown dimension `%s`。可用：%s\n\n%s"
              % (dim, ", ".join(sorted(dims_now)), text))
        return

    now = dims_now.get(dim)
    before = (prev or {}).get("dimensions", {}).get(dim)

    maxes = {"structure": 20, "consistency": 25, "reproducible": 20,
             "hygiene": 15, "discoverable": 15, "licensing": 5}
    mx = maxes.get(dim, 20)

    if before is None:
        verdict = "NO-BASELINE"
        line = "该维度没有可比的旧分 / no baseline score for `%s`." % dim
    else:
        try:
            gap_before, gap_now = mx - int(before), mx - int(now)
        except (TypeError, ValueError):
            gap_before = gap_now = 0
        if gap_now <= 0:
            verdict = "OVERTURNED"
            line = "扣分已消失：%s %s/%s → %s/%s / deduction gone." % (dim, before, mx, now, mx)
        elif gap_now < gap_before:
            verdict = "PARTIALLY ACCEPTED"
            line = "缺口缩小：%s %s/%s → %s/%s / gap shrank from %d to %d." % (
                dim, before, mx, now, mx, gap_before, gap_now)
        else:
            verdict = "UPHELD"
            line = "维持原判：%s %s/%s → %s/%s（缺口 %d 未变）/ unchanged gap." % (
                dim, before, mx, now, mx, gap_now)

    block = {
        "schema_version": "1.0",
        "kind": "appeal",
        "repo": "%s/%s" % (owner, repo),
        "dimension": dim,
        "before": before,
        "after": now,
        "max": mx,
        "ruling": verdict,
        "scope_note": "自动裁定只重测该维度，不评价申诉理由；理由争议走人工复核 / the bot only re-measures; argument disputes go to human review.",
    }

    out = ["### 申诉裁定 / Appeal ruling — `%s`" % dim, "", line, ""]
    out += ["| 项 / Item | 值 / Value |", "|---|---|",
            "| 维度 / Dimension | `%s` |" % dim,
            "| 改前 → 改后 / before → after | %s → **%s** （满分 %s）|" % (before, now, mx),
            "| 裁定 / Ruling | **%s** |" % verdict, ""]
    out += ["<details><summary>机器可读 / machine-readable</summary>", "",
            "```json", json.dumps(block, ensure_ascii=False, indent=2), "```", "</details>", ""]
    out += ["---",
            "*只重测被申诉的一个维度；不评价你的理由好坏。理由层面的争议请指名文件与检验方法，"
            "由人工复核后另行裁定。*",
            "*Only the appealed dimension is re-measured. The merit of your argument is not judged here: "
            "name a file and a check, and a human rules on it.*"]
    print("\n".join(out))


if __name__ == "__main__":
    main()
