#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证据自测：验证「分诊结论只来自日志，不臆造」。

用法（在技能包根目录）：
    python demo/prove_evidence.py

三组检查：
  1. 来源核对：triage 报出的每个栈帧 (file,line)、每个退出码、每个 HTTP 状态，
     都必须在日志原文里逐字找到；找不到即为臆造。
  2. 篡改跟随：把日志里某一行的行号改掉，重新分诊必须报新值、不得残留旧值。
  3. 注入可见：往日志里加一行原文不存在的栈帧，分诊必须把它读出来（证明它在读证据）。

退出码 0 = 三组全部成立。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import debughunt as bh  # noqa: E402

LOG = os.path.join(HERE, "sample_error.txt") if os.path.exists(
    os.path.join(HERE, "sample_error.txt")) else os.path.join(HERE, "sample_log.txt")


def triage(text):
    return bh.triage(text)


def main():
    base = open(LOG, encoding="utf-8").read()
    d = triage(base)

    # 1) 来源核对
    print("[1] 来源核对")
    bad = []
    for f in d["frames"]:
        pat = 'File "%s", line %d' % (f["file"], f["line"])
        if pat not in base:
            bad.append(pat)
    for code in d["exit_codes"]:
        if ("exit %s" % code) not in base and ("code %s" % code) not in base and str(code) not in base:
            bad.append("exit=%s" % code)
    for st in d["http_status"]:
        if str(st) not in base:
            bad.append("http=%s" % st)
    print("    栈帧 %d 个、退出码 %d 个、HTTP 状态 %d 个；无出处 %d 个"
          % (len(d["frames"]), len(d["exit_codes"]), len(d["http_status"]), len(bad)))
    for b in bad:
        print("    ✗ 无出处：%s" % b)

    # 2) 篡改跟随
    print("\n[2] 篡改跟随")
    ok2 = True
    if d["frames"]:
        f0 = d["frames"][0]
        old_pat = 'File "%s", line %d' % (f0["file"], f0["line"])
        new_line = f0["line"] + 10000
        new_pat = 'File "%s", line %d' % (f0["file"], new_line)
        mutated = base.replace(old_pat, new_pat, 1)
        d2 = triage(mutated)
        has_new = any(f["line"] == new_line for f in d2["frames"])
        has_old = any(f["line"] == f0["line"] for f in d2["frames"])
        ok2 = has_new and not has_old
        print("    %s -> %d : %s" % (old_pat, new_line,
              "跟随成功" if ok2 else "未跟随 ⚠（新值=%s 旧值残留=%s）" % (has_new, has_old)))
    else:
        print("    样本无栈帧，跳过（不算失败）")

    # 3) 注入可见
    print("\n[3] 注入可见")
    fake = 'Traceback (most recent call last):\n  File "injected_probe.py", line 4242, in probe\n'
    d3 = triage(base + "\n" + fake)
    ok3 = any(f["file"] == "injected_probe.py" and f["line"] == 4242 for f in d3["frames"])
    print("    注入 injected_probe.py:4242 -> %s" % ("被读出" if ok3 else "未读出 ⚠"))

    all_ok = not bad and ok2 and ok3
    print("\n结论：%s" % ("结论全部可回溯到日志（不臆造）" if all_ok else "存在无出处结论或未跟随，证明不成立"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
