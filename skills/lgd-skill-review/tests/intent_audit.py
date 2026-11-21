# -*- coding: utf-8 -*-
"""intents 审计：routes_to 是不是真的指向包内存在的东西。

上一轮把 intents 发出去了，但 routes_to 只是一个字符串声明。
「声称能路由」和「真的路由」是两件事——这个脚本只查后者。

四层：
  [A] 结构：schema 是 v2、每条有 id/ask_en/ask_zh/routes_to、id 唯一、ask 非空
  [B] 指针可解析：routes_to 形如 `entrypoints[0]` / `verification.differentiator` 都能落到真实字段
  [C] 指针非虚假：解析到的字段值非空；若指向 entrypoints，则该命令里的脚本文件必须存在
  [D] 可达性：每条 ask 也必须在 llms.txt 里出现（纯文本爬虫只看得到 llms.txt）
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PACKS = ["summarize-pro", "debug-pro", "wechat-viral-topic", "lgd-skill-review"]


def packs_root():
    env = os.environ.get("LGD_BENCH_OWN_DIR")
    if env and os.path.isdir(env):
        return env
    parent = os.path.dirname(REPO)
    if os.path.isdir(os.path.join(parent, "summarize-pro")):
        return parent
    return parent  # CI：只有自身也在列表里时才有效


def resolve(doc, ptr):
    """把 `entrypoints[0]` / `verification.differentiator` 这类路径解析成真实值。

    支持点路径 + 段末下标，例如 `verification.differentiator`、`entrypoints[0]`。
    第一版只认单段，把合法的点路径判成「解析到空值」——审计自己先错了一次。
    """
    val = doc
    for seg in ptr.strip().split("."):
        m = re.match(r"^([A-Za-z_]+)(?:\[(\d+)\])?$", seg)
        if not m:
            return None, "无法解析的路径段 %r" % seg
        key, idx = m.group(1), m.group(2)
        if not isinstance(val, dict) or key not in val:
            return None, "字段 %s 不存在" % key
        val = val[key]
        if idx is not None:
            i = int(idx)
            if not isinstance(val, list) or i >= len(val):
                return None, "%s[%d] 越界（长度 %s）" % (
                    key, i, len(val) if isinstance(val, list) else "n/a")
            val = val[i]
    return val, None


def script_of(cmd):
    """从一条入口命令里取出脚本路径，判断它在包里是否真的存在。"""
    for tok in cmd.split():
        if tok.endswith(".py") and "/" in tok:
            return tok.lstrip("./")
    return None


def audit_pack(root, name):
    fails = []
    p = os.path.join(root, name, "AI-INDEX.json")
    if not os.path.exists(p):
        return ["%s: 无 AI-INDEX.json" % name], 0
    doc = json.load(io.open(p, encoding="utf-8"))

    # [A]
    if doc.get("schema") != "lgd.ai-index/2":
        fails.append("schema=%r 不是 lgd.ai-index/2" % doc.get("schema"))
    intents = doc.get("intents") or []
    if len(intents) < 4:
        fails.append("intents 只有 %d 条（少于 4）" % len(intents))
    ids = set()
    for it in intents:
        for k in ("id", "ask_en", "ask_zh", "routes_to"):
            if not str(it.get(k, "")).strip():
                fails.append("intent %s 缺 %s" % (it.get("id"), k))
        if it.get("id") in ids:
            fails.append("intent id 重复：%s" % it.get("id"))
        ids.add(it.get("id"))

    # [B] [C]
    for it in intents:
        val, err = resolve(doc, it.get("routes_to", ""))
        if err:
            fails.append("%s → %s: %s" % (it["id"], it["routes_to"], err))
            continue
        if not val:
            fails.append("%s → %s: 解析到空值" % (it["id"], it["routes_to"]))
            continue
        if isinstance(val, str) and val.startswith("python "):
            s = script_of(val)
            if s and not os.path.exists(os.path.join(root, name, s)):
                fails.append("%s → %s: 脚本 %s 在包内不存在" % (it["id"], it["routes_to"], s))

    # [D]
    l = os.path.join(root, name, "llms.txt")
    if os.path.exists(l):
        txt = io.open(l, encoding="utf-8").read()
        for it in intents:
            if it["ask_en"] not in txt:
                fails.append("%s: ask_en 未出现在 llms.txt" % it["id"])
        for it in intents:
            if it["ask_zh"] not in txt:
                fails.append("%s: ask_zh 未出现在 llms.txt" % it["id"])
    else:
        fails.append("%s: 无 llms.txt" % name)
    return fails, len(intents)


def main():
    root = packs_root()
    packs = [p for p in DEFAULT_PACKS if os.path.isdir(os.path.join(root, p))]
    if not packs and os.path.isdir(os.path.join(REPO, "AI-INDEX.json")):
        fails, n = audit_pack(os.path.dirname(REPO), os.path.basename(REPO))
        packs = [os.path.basename(REPO)]
        allf = fails
        print("%-18s intents=%2d  %s" % (packs[0], n, "OK" if not fails else "FAIL"))
    else:
        allf = []
        for name in packs:
            fails, n = audit_pack(root, name)
            print("%-18s intents=%2d  %s" % (name, n, "OK" if not fails else "FAIL"))
            for f in fails:
                print("    - " + f)
            allf += fails
    print()
    print("ALL PASS" if not allf else "FAIL: %d 处" % len(allf))
    return 0 if not allf else 1


if __name__ == "__main__":
    sys.exit(main())
