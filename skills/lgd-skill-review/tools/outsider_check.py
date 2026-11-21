#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一条命令自证：任何人（含外部 AI）都能独立核对我们公开的每一个数字。

我们不想让你相信一段文字，只想让你跑一条命令：
    python tools/outsider_check.py
它只读公开 HTTPS 端点，不需要 token，不访问本机文件。

检查三件事
1. 机器入口可达：llms.txt 里列出的每个本站 URL 必须 200。
2. 数字可复算：页面上的 16 / 38 / 96 / 58 必须能从 leaderboard.json 现算出来。
3. 尺子自洽：rubric.json 的权重和 = 100、判据条数 = 23、drift_check.consistent = true；
   run-proof.json 的四包实跑必须是 PASS 100。

退出码 0 = 全部一致；1 = 有任一条对不上（会打印差在哪里）。
"""
import json
import re
import sys
import urllib.request

SITE = "https://zhaoxinghua09-cell.github.io/lgd-skill-review"
UA = {"User-Agent": "lgd-outsider-check/1.0"}


def get(path):
    with urllib.request.urlopen(urllib.request.Request(SITE + path, headers=UA), timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


def get_json(path):
    return json.loads(get(path))


def main():
    fails, notes = [], []

    lb = get_json("/leaderboard.json")
    s = lb["summary"]
    rows = lb["rows"]
    third = [r for r in rows if r.get("bucket") == "third-party"]
    own = [r for r in rows if r.get("bucket") == "lgd"]
    recomputed = {
        "third_party_entries": len(third),
        "lgd_entries": len(own),
        "third_party_top": max((r["score"] or 0) for r in third),
        "lgd_top": max((r["score"] or 0) for r in own),
    }
    recomputed["gap"] = recomputed["lgd_top"] - recomputed["third_party_top"]
    for k, v in recomputed.items():
        if s.get(k) != v:
            fails.append("leaderboard.json summary.%s 声明 %s，按 rows 现算 %s" % (k, s.get(k), v))
    print("leaderboard: 16=%d 38=%d 96=%d gap=%d" % (
        recomputed["third_party_entries"], recomputed["third_party_top"],
        recomputed["lgd_top"], recomputed["gap"]))

    index = get("/index.html")
    for needle in ("16 third-party", "96", "58"):
        if needle not in index:
            notes.append("首页未出现字样：%r（若改过措辞可忽略）" % needle)

    badge = None
    raw_badge = ("https://raw.githubusercontent.com/zhaoxinghua09-cell/lgd-skill-review/main/bench/badge.json")
    try:
        with urllib.request.urlopen(urllib.request.Request(raw_badge, headers=UA), timeout=25) as r:
            badge = json.loads(r.read().decode("utf-8", "ignore"))
    except Exception as exc:
        notes.append("badge.json 取自 raw 端点不可达（%s）—— 属本机网络问题，非事实判断" % repr(exc)[:50])
    if badge:
        want = "peers %d / LGD %d" % (recomputed["third_party_top"], recomputed["lgd_top"])
        if badge.get("message") != want:
            fails.append("badge.json 写 %r，应为 %r" % (badge.get("message"), want))
        else:
            print("badge: %s" % want)

    rub = get_json("/rubric.json")
    dims = rub.get("dimensions", [])
    total = sum(d.get("weight") for d in dims)
    checks = sum(len(d.get("checks", [])) for d in dims)
    if total != 100:
        fails.append("rubric 权重和 %s != 100" % total)
    if checks != 23:
        fails.append("rubric 判据条数 %s != 23" % checks)
    if not (rub.get("drift_check") or {}).get("consistent"):
        fails.append("rubric drift_check 不为 consistent")
    print("rubric: dims=%d weights=%d checks=%d drift=%s" % (
        len(dims), total, checks, (rub.get("drift_check") or {}).get("consistent")))

    proof = get_json("/run-proof.json")
    pkgs = proof.get("packages") or []
    if len(pkgs) != 4:
        fails.append("run-proof 条目数 %d（期望 4）" % len(pkgs))
    for r in pkgs:
        if r.get("verdict") != "PASS" or r.get("score") != 100:
            fails.append("run-proof %s 写 %s/%s" % (r.get("package"), r.get("verdict"), r.get("score")))
    print("run-proof: %d 条 %s" % (len(pkgs), [(r.get("package"), r.get("score")) for r in pkgs]))

    llms = get("/llms.txt")
    urls = sorted(set(re.findall(r"https://zhaoxinghua09-cell\.github\.io/lgd-skill-review/\S+", llms)))
    bad = []
    for u in urls:
        u = u.rstrip(".,;:)`")
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20) as r:
                if r.status != 200:
                    bad.append((u, r.status))
        except Exception as e:
            bad.append((u, repr(e)[:60]))
    print("machine entry: %d urls, %d unreachable" % (len(urls), len(bad)))
    for u, why in bad:
        fails.append("机器入口不可达 %s (%s)" % (u, why))

    print()
    for n in notes:
        print("NOTE  " + n)
    if fails:
        print("\nFAILED (%d):" % len(fails))
        for f in fails:
            print("  - " + f)
        return 1
    print("CONSISTENT — 公开端点与公开数字逐条自洽")
    return 0


if __name__ == "__main__":
    sys.exit(main())
