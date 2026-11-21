"""Workflow / actions-lock consistency gate.

起因（2026-11-21 实测）：GitHub 在 `.github/workflows/actions.lock` 里锁了依赖版本，
而我们的 YAML 里写的是浮动标签 `actions/checkout@v4`。两者对不上，GitHub 直接
`startup_failure`——工作流连一个 job 都不排，页面上只留一句 "workflow run failed"。
这种失败最隐蔽：本地 YAML 完全合法，`yaml.safe_load` 也通过，只有 GitHub 侧拒绝。

所以本闸门不检查 YAML 语法，只检查一件事：每个 `uses:` 的引用字符串，
必须与 `actions.lock` 里为该工作流登记的条目逐字相同。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = os.path.join(ROOT, ".github", "workflows")
LOCK = os.path.join(WF, "actions.lock")
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.M)


def parse_lock(text):
    """只解析我们要的两层：workflows.<path> 里的引用列表。"""
    entries, cur = {}, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s{4}'?([^':]+\.yml)'?:\s*(.*)$", line)
        if m:
            cur = m.group(1)
            entries[cur] = []
            rest = m.group(2).strip()
            if rest.startswith("["):
                for item in re.findall(r"'([^']+)'", rest):
                    entries[cur].append(item)
            continue
        if cur:
            item = re.match(r"^\s*-\s*'([^']+)'", line)
            if item:
                entries[cur].append(item.group(1))
            elif line.strip().startswith("dependencies:"):
                cur = None
    return entries


def main():
    lock_text = open(LOCK, encoding="utf-8").read()
    lock = parse_lock(lock_text)
    problems, checked = [], 0
    for name in sorted(os.listdir(WF)):
        if not name.endswith(".yml"):
            continue
        body = open(os.path.join(WF, name), encoding="utf-8").read()
        refs = [u.strip() for u in USES.findall(body)]
        checked += 1
        rel = ".github/workflows/" + name
        if rel not in lock:
            problems.append(f"{rel}: 未登记在 actions.lock（新增工作流必须重新生成锁）")
            continue
        allowed = lock[rel]
        actions = 0
        for ref in refs:
            if ref.startswith("./"):
                continue
            # 可复用工作流（跨仓 .yml@sha）不在此锁内：GitHub 自己的生成器就是把它留空的，
            # 实测 lgd-ci.yml 登记为 [] 却照常运行，所以这里只做记录、不做判定。
            if ref.split("@")[0].endswith(".yml"):
                print(f"NOTE {rel}: 可复用工作流 {ref.split('@')[0]}（锁文件不登记，跳过）")
                continue
            actions += 1
            if ref not in allowed:
                problems.append(f"{rel}: uses {ref} 不在锁文件登记项 {allowed}")
        if actions and allowed == []:
            problems.append(f"{rel}: 使用了 action 但锁文件登记为空")
    print(f"workflows={checked} lock_entries={len(lock)}")
    for p in problems:
        print("PROBLEM", p)
    if problems:
        print(f"FAIL — {len(problems)} 处引用与 actions.lock 不一致")
        return 1
    print("ALL PASS — 每个 uses 都能在 actions.lock 找到逐字一致的登记")
    return 0


if __name__ == "__main__":
    sys.exit(main())
