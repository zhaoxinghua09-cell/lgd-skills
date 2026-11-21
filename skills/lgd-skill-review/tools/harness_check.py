#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loadability check — "will an agent load this skill correctly?"

Why this exists: NVIDIA SkillEvaluator ships a separate Tier 1 Harness Check for exactly the
question "will my agent load the skill correctly?". Our six-dimension ruler scored documents
and evidence, but never asked whether the package survives being loaded: broken front-matter,
a reference file that does not exist, an absolute path, a name that a host will reject.

This tool is deliberately NOT part of the score. It answers one question with findings a
human can act on, and it is safe to run on any package:

    python tools/harness_check.py <package-dir> [more dirs...]

Exit 0 = loadable; 1 = at least one blocking loadability defect.
"""
import io
import json
import os
import re
import sys

NAME_MAX = 64
DESC_MAX = 1024
REQUIRED = ("name", "description")


def frontmatter(text):
    """Parse the leading --- block without a YAML dependency (same shape we publish)."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    out = {}
    key = None
    for line in block.splitlines():
        if not line.strip():
            continue
        if line.startswith((" ", "\t")) and key:
            out[key] = (out[key] + " " + line.strip()).strip()
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = m.group(2).strip().strip('"').strip("'")
    return out


def check(pkg):
    fails, notes = [], []
    skill = os.path.join(pkg, "SKILL.md")
    if not os.path.isfile(skill):
        return ["SKILL.md 不存在（agent 无法加载）"], notes
    raw = io.open(skill, encoding="utf-8", errors="strict").read()
    fm = frontmatter(raw)
    if fm is None:
        fails.append("SKILL.md 缺少以 --- 包裹的 front-matter 块")
        return fails, notes

    for k in REQUIRED:
        if not fm.get(k):
            fails.append("front-matter 缺必填字段 %s" % k)
    name = fm.get("name", "")
    if name:
        if len(name) > NAME_MAX:
            fails.append("name 长度 %d > %d（宿主会截断或拒绝）" % (len(name), NAME_MAX))
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", name):
            fails.append("name %r 不是小写字母/数字/连字符（多数宿主按此规范校验）" % name)
    desc = fm.get("description", "")
    if desc and len(desc) > DESC_MAX:
        fails.append("description 长度 %d > %d（会被截断，触发词丢失）" % (len(desc), DESC_MAX))

    # 引用文件必须真存在；绝对路径一律视为不可移植
    body = raw[raw.find("\n---", 3) + 4:]
    refs = re.findall(r"\]\(([^)]+)\)", body) + re.findall(r"`(references/[^`]+)`", body)
    missing = []
    absolute = []
    for ref in refs:
        if ref.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if re.match(r"^[A-Za-z]:[\\/]", ref) or ref.startswith("/"):
            absolute.append(ref)
            continue
        target = os.path.join(pkg, ref.replace("/", os.sep))
        if not os.path.exists(target):
            missing.append(ref)
    for r in missing:
        fails.append("正文引用的文件不存在：%s" % r)
    for r in absolute:
        fails.append("正文引用绝对路径（换机即失效）：%s" % r)

    n_files = sum(len(fs) for _, _, fs in os.walk(pkg))
    n_bytes = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(pkg) for f in fs)
    notes.append("files=%d bytes=%d" % (n_files, n_bytes))
    return fails, notes


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    total_bad = 0
    for pkg in argv:
        print("=== %s" % pkg)
        try:
            fails, notes = check(pkg)
        except UnicodeDecodeError as e:
            print("  FAIL  SKILL.md 非 UTF-8：%s" % e)
            total_bad += 1
            continue
        for n in notes:
            print("  note  %s" % n)
        if fails:
            total_bad += 1
            for f in fails:
                print("  FAIL  %s" % f)
        else:
            print("  LOADABLE — front-matter 合法、引用文件齐全、路径可移植")
    print("\n%d / %d packages loadable" % (len(argv) - total_bad, len(argv)))
    return 1 if total_bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
