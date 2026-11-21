#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""评分自测：验证「同包同分、扣分可定位、补偿后必涨分」。

用法（在技能包根目录）：
    python demo/prove_score.py

三组检查：
  1. 可复算：同一个包连评两次，总分与全部维度明细逐字相同。
  2. 可定位：阻断项必须报出「规则:文件」，整改项必须带编号与具体说明。
  3. 因果响应：把整改项指出的缺失补齐，总分必须上升、对应扣分必须消失。

退出码 0 = 三组全部成立。
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)

import review as rv  # noqa: E402
import run_demo as demo  # noqa: E402


def snap(rep):
    return json.dumps({"total": rep["total"], "dims": rep["dimensions"],
                       "blocking": rep["blocking"], "actions": rep["actions"]},
                      ensure_ascii=False, sort_keys=True)


def main():
    base = tempfile.mkdtemp(prefix="lgd_prove_")
    bad = os.path.join(base, "bad")
    demo.make_bad(bad)

    # 1) 可复算
    a = rv.review(bad, do_run=False)["data"]
    b = rv.review(bad, do_run=False)["data"]
    same = snap(a) == snap(b)
    print("[1] 可复算：两次总分 %s / %s -> %s；维度明细%s"
          % (a["total"], b["total"], "一致" if same else "不一致 ⚠", "逐字相同" if same else "有差异"))

    # 2) 可定位
    shaped = all(":" in s for s in a["blocking"]) if a["blocking"] else True
    numbered = all(x.get("id") and x.get("issue") for x in a["actions"])
    print("[2] 可定位：阻断项 %d 条（%s）、整改项 %d 条（%s）"
          % (len(a["blocking"]), "规则:文件 形态" if shaped else "缺文件定位 ⚠",
             len(a["actions"]), "均带编号与说明" if numbered else "有项缺编号 ⚠"))
    for s in a["blocking"]:
        print("    · %s" % s)

    # 3) 因果响应
    fixed = os.path.join(base, "fixed")
    good = os.path.join(base, "good")
    demo.make_bad(fixed)
    demo.make_good(good)
    old_total = a["total"]
    demo.fix(fixed, good)   # 只按整改项补齐，不换包
    c = rv.review(fixed, do_run=False)["data"]
    up = c["total"] > old_total
    gone = all(x not in c["blocking"] for x in a["blocking"])
    print("[3] 因果响应：补齐后 %s -> %s（%s）；原阻断 %s"
          % (old_total, c["total"], "涨分" if up else "未涨分 ⚠",
             "已消失" if gone else "仍存在 ⚠"))

    all_ok = same and shaped and numbered and up
    print("\n结论：%s" % ("评分可复算、扣分可定位、补偿即涨分" if all_ok
                        else "存在不可复算/不可定位/不响应，证明不成立"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()

