#!/usr/bin/env python3
"""Append a before→after line to a re-review verdict.

The loop is only closed if a submitter can see the number move. So on a re-review we read the previous
bot verdict in the same thread, pull its machine-readable score, and state the delta.

Args: <issue_number> <owner/repo> <verdict_file>
"""
import json
import os
import re
import sys
import urllib.request


def comments(owner, repo, number):
    url = "https://api.github.com/repos/%s/%s/issues/%d/comments?per_page=100" % (owner, repo, number)
    h = {"User-Agent": "lgd-rereview", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def last_score(bodies):
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
        if data.get("score") is not None:
            return data
    return None


def main():
    number, slug, path = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    owner, repo = slug.split("/", 1)
    text = open(path, encoding="utf-8").read()

    m = re.search(r'```json\s*(\{.*?\})\s*```', text, re.S)
    if not m:
        print(text)
        return
    new = json.loads(m.group(1))

    try:
        prev = last_score([c.get("body", "") for c in comments(owner, repo, number)])
    except Exception as e:  # network/auth failure must not lose the verdict
        sys.stderr.write("delta skipped: %s\n" % e)
        print(text)
        return

    if not prev:
        line = "> 首次评审，无可比基线 / First review in this thread — no baseline to compare."
    else:
        before, after = prev.get("score"), new.get("score")
        try:
            delta = int(after) - int(before)
        except (TypeError, ValueError):
            delta = None
        if delta is None:
            line = "> 基线分数无法解析 / baseline score unreadable."
        else:
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
            line = ("**复评 / Re-review：%s → %s （%s%d）/ before %s, after %s**"
                    % (before, after, arrow, delta, before, after))
            if delta > 0:
                line += " — 改动已经体现在分数上 / the change shows up in the score."
            elif delta == 0:
                line += " — 分数未变：改动可能不在评分维度内，或测试仍未可跑 / unchanged: the edit may sit outside scored dimensions, or tests still do not run."
            else:
                line += " — 分数下降：新改动引入了扣分项 / the edit introduced a deduction."
            # 快照变了才谈"改动"；否则分数变化来自别处（比如我们自己的引擎修正）
            pc, nc = prev.get("target_commit"), new.get("target_commit")
            if pc and nc and pc != nc:
                line += "\n> 快照 / snapshot：`%s` → `%s`（分数变化对应这两个提交之间的差异）" % (pc, nc)
            elif pc and nc and pc == nc and delta != 0:
                line += "\n> 快照未变（`%s`）：这次分数变化**不是**提交内容造成的，应来自评审侧修正 / same snapshot — the delta did not come from the repo." % nc

    marker = "\n---\n"
    idx = text.find(marker)
    insert = "\n" + line + "\n"
    if idx == -1:
        print(text + insert)
    else:
        print(text[:idx] + insert + text[idx:])


if __name__ == "__main__":
    main()
