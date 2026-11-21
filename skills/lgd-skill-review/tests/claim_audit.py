#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主张审查：对外材料不得出现"整体更强 / 首创 / 唯一"这类会被一次事实核查推翻的话。

为什么要有它：定位核查已经证明这个位置有人占着（SkillsBench / NVIDIA SkillEvaluator /
社区百分制），所以"首个""唯一""最强"不是措辞问题，是事实问题。这条规则必须由机器守，
不能靠写的时候记得。

两类断言
[A] 禁用词：扫描对外主张面（SKILL.md / README / llms*.txt / AI-INDEX / AUDIT-REPORT / docs 页面），
    命中即失败。规则条文里为了禁止这些词而引用它们的行（含 NEVER / 不得 / 禁止）豁免。
[B] 定位披露：docs/positioning.html 必须存在，且必须点名 SkillsBench、SkillEvaluator、
    skill-evaluator 三者，并写明 "What we do not measure"。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SURFACES = ["SKILL.md", "README.md", "llms.txt", "AI-INDEX.json", "AUDIT-REPORT.md"]
DOC_GLOBS = (".html", ".txt", ".md")

FORBIDDEN = [
    "首创", "唯一", "首个", "断崖", "领先", "最强", "最缺", "前所未有", "业界第一", "世界第一",
    "no one has", "first ever", "the only", "unmatched", "best-in-class", "world's first",
    "industry-leading", "state of the art",
]

# 为了禁止这些词而引用它们的行（规则条文），不算主张
META = re.compile(r"NEVER|不得|禁止|禁用|避免")

POSITIONING = os.path.join(ROOT, "docs", "positioning.html")
REQUIRED_NAMES = ["SkillsBench", "SkillEvaluator", "skill-evaluator"]
REQUIRED_PHRASE = "What we do not measure"


def surfaces():
    for rel in SURFACES:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            yield rel, p
    docs = os.path.join(ROOT, "docs")
    if os.path.isdir(docs):
        for name in sorted(os.listdir(docs)):
            if name.endswith(DOC_GLOBS):
                yield "docs/" + name, os.path.join(docs, name)


def main():
    fails = []
    hits = 0
    for rel, path in surfaces():
        text = io.open(path, encoding="utf-8", errors="ignore").read()
        for line_no, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if META.search(line):
                continue
            for word in FORBIDDEN:
                if word.lower() in low:
                    hits += 1
                    fails.append("%s:%d 出现禁用表述「%s」 → %s" % (rel, line_no, word, line.strip()[:90]))

    if not os.path.isfile(POSITIONING):
        fails.append("缺少 docs/positioning.html（必须公开点名已有工作）")
    else:
        pos = io.open(POSITIONING, encoding="utf-8", errors="ignore").read()
        for n in REQUIRED_NAMES:
            if n not in pos:
                fails.append("positioning.html 未点名 %s" % n)
        if REQUIRED_PHRASE not in pos:
            fails.append("positioning.html 缺「%s」段" % REQUIRED_PHRASE)

    print("surfaces=%d forbidden_hits=%d" % (len(list(surfaces())), hits))
    if fails:
        print("FAIL (%d):" % len(fails))
        for f in fails:
            print("  - " + f)
        return 1
    print("ALL PASS — 对外材料无整体更强表述，且已公开点名已有工作")
    return 0


if __name__ == "__main__":
    sys.exit(main())
