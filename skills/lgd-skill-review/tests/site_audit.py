# -*- coding: utf-8 -*-
"""站点审计：每个页面必须有「内容」，不能是只有标题+安装命令的 stub。

起因：gen_site 的 stub 循环曾把 benchmark / skill-review / quickfix 三个手写详情页
整页覆盖，线上榜单页连续多日零表格而没人发现。这个脚本就是那道闸。

断言分两层：
  [结构] 每页必须有实质块（h2 / 表格 / 代码块 至少各一个以上），且带 canonical 与站点导航
  [内容] 每个页面对应的关键事实必须出现在 HTML 里（数字取自 leaderboard，命令取自仓库真实脚本）
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
LB = os.path.join(ROOT, "bench", "leaderboard.json")

PAGES = ["index", "rubric", "skill-review", "quickfix", "benchmark", "compare", "guide",
         "badge", "audits", "registry", "discover"]


def read(name):
    return io.open(os.path.join(DOCS, name + ".html"), encoding="utf-8").read()


def main():
    lb = json.load(io.open(LB, encoding="utf-8"))
    s = lb["summary"]
    fails = []

    for name in PAGES:
        p = os.path.join(DOCS, name + ".html")
        if not os.path.exists(p):
            fails.append("%s.html 不存在" % name)
            continue
        t = read(name)
        h2 = len(re.findall(r"<h2", t))
        tr = len(re.findall(r"<tr>", t))
        code = len(re.findall(r"<pre><code", t))
        # 结构：不能是 stub（stub 只有 kick+h1+lead+一段正文+一个安装块）
        if not (h2 >= 1 and (tr >= 1 or code >= 1)):
            fails.append("%s 像 stub：h2=%d tr=%d code=%d" % (name, h2, tr, code))
        if "canonical" not in t:
            fails.append("%s 缺 canonical" % name)
        if "./benchmark.html" not in t or "./rubric.html" not in t:
            fails.append("%s 缺站点导航" % name)

    # 内容：数字与命令必须真的在页面上
    idx = read("index")
    for k in ("third_party_entries", "third_party_top", "gap"):
        if str(s[k]) not in idx:
            fails.append("index 未出现 %s=%s" % (k, s[k]))

    bm = read("benchmark")
    if len(re.findall(r"<tr>", bm)) < len(lb["rows"]):
        fails.append("benchmark 表格行 %d < 榜单 %d 条" % (len(re.findall(r"<tr>", bm)), len(lb["rows"])))
    if "Generated" not in bm:
        fails.append("benchmark 缺生成时间戳")

    for name, must in (("skill-review", "review.py"), ("quickfix", "quickfix.py")):
        if must not in read(name):
            fails.append("%s 未出现可运行命令 %s" % (name, must))

    # compare 页：两个目标都要点名，且六维各一行——不能只放合计
    cmpr = read("compare")
    bj = json.load(io.open(os.path.join(ROOT, "bench", "bench.json"), encoding="utf-8"))
    tp = max((r for r in bj if r["bucket"] == "third-party"), key=lambda r: r["score"])
    own = max((r for r in bj if r["bucket"] == "lgd"), key=lambda r: r["score"])
    if tp["target"] not in cmpr:
        fails.append("compare 未出现第三方最强目标 %s" % tp["target"])
    if len(re.findall(r"<tr>", cmpr)) < 8:
        fails.append("compare 表格行 %d < 8（六维 + 合计 + 表头）" % len(re.findall(r"<tr>", cmpr)))
    if str(tp["score"]) not in cmpr or str(own["score"]) not in cmpr:
        fails.append("compare 未出现两侧总分")

    # guide 页：必须是「可照抄」的，而不是解释哲学——三个代码块 + 退出码这条关键要求
    gd = read("guide")
    if len(re.findall(r"<pre><code", gd)) < 3:
        fails.append("guide 代码块 %d < 3（三步各一块）" % len(re.findall(r"<pre><code", gd)))
    for k in ("golden.json", "run_golden.py", "verify.yml", "非零退出", "data.total"):
        if k not in gd:
            fails.append("guide 未提及 %s" % k)

    # 机器出口与页面数一致
    sm = io.open(os.path.join(DOCS, "sitemap.xml"), encoding="utf-8").read()
    locs = re.findall(r"<loc>", sm)
    if len(locs) != len([n for n in PAGES if os.path.exists(os.path.join(DOCS, n + ".html"))]):
        fails.append("sitemap loc=%d 与页面数不符" % len(locs))

    rj = json.load(io.open(os.path.join(DOCS, "rubric.json"), encoding="utf-8"))
    if not rj.get("drift_check", {}).get("consistent"):
        fails.append("rubric.json drift_check 不一致")

    # llms.txt 是给机器读的入口：URL 必须能直接访问，且列全新页
    SITE = "https://zhaoxinghua09-cell.github.io/lgd-skill-review"
    lm = io.open(os.path.join(DOCS, "llms.txt"), encoding="utf-8").read()
    broken = re.findall(re.escape(SITE) + r"[A-Za-z0-9]", lm)
    if broken:
        fails.append("llms.txt 有 %d 处 URL 缺斜杠（%s）" % (len(broken), broken[0]))
    for page in ("compare.html", "guide.html", "discover.html"):
        if "%s/%s" % (SITE, page) not in lm:
            fails.append("llms.txt 未列出 %s" % page)
    if "## all pages" not in lm:
        fails.append("llms.txt 缺 all pages 段")

    for f in fails:
        print("  - " + f)
    print("ALL PASS" if not fails else "FAIL: %d 处" % len(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
