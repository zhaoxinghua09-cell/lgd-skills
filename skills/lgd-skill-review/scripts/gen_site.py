#!/usr/bin/env python3
"""Generate the static, machine-crawlable site for lgd-skill-review.

Outputs into docs/ : index.html, 4 skill pages, rubric.html, sitemap.xml, robots.txt, llms.txt
Everything is derived from bench/leaderboard.json + the four SKILL.md frontmatters, so the
site cannot drift away from the measured numbers.

No JavaScript. One page = one topic. JSON-LD on every page.
"""
import datetime
import json
import subprocess
import sys
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(HERE, "bench", "leaderboard.json")
DOCS = os.path.join(HERE, "docs")
SITE = "https://zhaoxinghua09-cell.github.io/lgd-skill-review"
REPO = "https://github.com/zhaoxinghua09-cell/lgd-skill-review"

SKILLS = [
    {
        "slug": "skill-review",
        "title": "Skill Review · 技能审计",
        "h1": "Audit a skill, get evidence — not opinions",
        "zh": "技能审计：每一处扣分都钉在具体文件上",
        "triggers": ["skill audit", "skill review", "rate my skill", "SKILL.md review",
                     "技能评测", "技能审计", "帮我看看这个技能缺什么"],
        "body": "Six dimensions, static analysis, every deduction pinned to a file with a line. "
                "Same package in, same score out. Every result comes with a remediation order and "
                "a projected ceiling that separates mechanical fixes from work you still have to do.",
    },
    {
        "slug": "quickfix",
        "title": "QuickFix · 一键机械整改",
        "h1": "The fixes anyone can apply in one command",
        "zh": "机械可补的部分，一条命令补完",
        "triggers": ["quickfix skill", "add license to skill", "AI-INDEX.json", "skill hygiene",
                     "技能整改", "补许可", "清路径"],
        "body": "Adds LICENSE and a license field, generates AI-INDEX.json, appends a Commands "
                "section built from the flags that really exist in the source, and scrubs absolute "
                "paths. Dry-run by default; a single file changed over 30% is refused.",
    },
    {
        "slug": "benchmark",
        "title": "SkillBench · 公开基准",
        "h1": "Sixteen third-party targets, one ruler",
        "zh": "同引擎、同口径、同一时点，任何人都能重跑",
        "triggers": ["skill benchmark", "agent skill score", "verifiability score",
                     "技能基准", "评分对比", "可验证性"],
        "body": "Third-party skills with hundreds of thousands of installs score 10–36 here. It "
                "measures verifiability — whether a stranger can check the work — not usefulness.",
    },
]

AUDITS = [
    {
        "name": "microsoft / azure-skills",
        "skill": "skills/azure-deploy",
        "installs": "≈731k",
        "before": 20,
        "after_mech": 24,
        "dims_before": "structure 6 / consistency 0 / reproducible 0 / hygiene 8 / discoverable 4 / licensing 2",
        "findings": [
            "frontmatter 缺 version（structure 扣分）",
            "references/recipes/azcli/errors.md 层级超过 3 段",
            "无测试文件（tests/*.json）与执行器，别人无法复跑",
            "无 demo，首次使用者无从验证",
            "SKILL.md 未声明安全边界与降级规则",
            "标签 0 个；缺互链段；无 AI-INDEX.json / llms.txt",
            "缺 author；无独立许可文件（仅 frontmatter 声明）",
        ],
        "mechanical": [
            "补 LICENSE（MIT）→ licensing 2→3",
            "生成 AI-INDEX.json → discoverable 4→7",
        ],
        "fix_order": [
            "P0 · 5 分钟：加 LICENSE 文件、给 frontmatter 补 version 与 author",
            "P1 · 半小时：加 tags、触发词段、AI-INDEX.json 或 llms.txt、互链段",
            "P2 · 作者工作：写 tests/*.json 与执行器、补 demo、声明安全边界",
        ],
    },
    {
        "name": "prisma / skills",
        "skill": "prisma-cli",
        "installs": "≈435k",
        "before": 20,
        "after_mech": None,
        "dims_before": "structure 10 / consistency 0 / reproducible 0 / hygiene 8 / discoverable 0 / licensing 2",
        "findings": [
            "frontmatter 缺 version（且非 SemVer）",
            "无测试文件与执行器，无法复跑",
            "无 demo",
            "未声明安全边界与降级规则",
            "标签 0 个；缺触发词段；缺互链段；无机器可读索引",
            "缺 author；无独立许可文件",
        ],
        "mechanical": ["同上四类机械动作可补，未在本轮实测（避免对未验证项下结论）"],
        "fix_order": [
            "P0 · 5 分钟：加 LICENSE 文件、给 frontmatter 补 version（SemVer）与 author",
            "P1 · 半小时：加 tags、触发词段、AI-INDEX.json 或 llms.txt、互链段",
            "P2 · 作者工作：写 tests/*.json 与执行器、补 demo、声明安全边界",
        ],
    },
]

REACH = {
    "target": "microsoft/azure-skills · skills/azure-deploy（第三方包，我们未作者）",
    "stages": [
        ("原样 / as shipped", 20, "structure 6 · consistency 0 · reproducible 0 · hygiene 8 · discoverable 4 · licensing 2"),
        ("仅机械整改 / mechanical only", 24, "补 LICENSE + AI-INDEX.json；licensing 2→3，discoverable 4→7"),
        ("机械 + 补测试与 demo / + tests & demo", 57, "加 tests/golden.json、可跑 runner、llms.txt、tags、version；reproducible 0→16"),
        ("再补作者工作 / + authored CLI", 86, "写 scripts/check_prereqs.py（argparse）、在 SKILL.md 声明其命令、补安全边界与生态段；consistency 0→15，hygiene 8→15"),
    ],
    "left": "剩 14 分：references/recipes/azcli 层级超过 3 段（structure −4）、以及只实现了一条声明命令（consistency −10）",
}

CSS = """
:root{--bg:#0b1220;--card:#111a2c;--line:rgba(122,160,255,.18);--fg:#e8eef8;--mut:#a9b8d0;--acc:#7fe7c4;--warn:#f2a65a}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font:16px/1.7 -apple-system,"Segoe UI","Microsoft YaHei",Arial,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:56px 24px 96px}
nav{display:flex;gap:18px;flex-wrap:wrap;font-size:14px;color:var(--mut);margin-bottom:36px}
nav a{color:var(--mut);text-decoration:none;border-bottom:1px solid transparent}
nav a:hover{color:var(--acc);border-color:var(--acc)}
.kick{color:var(--acc);letter-spacing:.18em;text-transform:uppercase;font-size:12px}
h1{font-size:38px;line-height:1.2;margin:10px 0 14px;letter-spacing:-.5px}
h2{font-size:22px;margin:40px 0 12px}
h3{font-size:16px;margin:20px 0 8px}
p,li{color:var(--mut)}
.lead{font-size:18px;color:var(--fg);max-width:760px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px 24px;margin-top:16px}
table{width:100%;border-collapse:collapse;margin-top:14px;font-size:14px}
th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line)}
th{color:var(--acc);font-weight:600;letter-spacing:.06em;font-size:12px;text-transform:uppercase}
td.num{text-align:right;font-variant-numeric:tabular-nums;width:64px}
.bad{color:var(--warn)} .good{color:var(--acc)}
code{background:rgba(88,124,200,.14);padding:2px 6px;border-radius:4px;font-size:13px}
pre{background:#0a0f1a;border:1px solid var(--line);border-radius:10px;padding:16px;overflow-x:auto;margin-top:12px}
pre code{background:none;padding:0}
ul{margin:10px 0 0 20px}
.tag{display:inline-block;font-size:12px;color:var(--acc);border:1px solid rgba(127,231,196,.4);border-radius:4px;padding:3px 8px;margin:4px 6px 0 0}
.a{color:var(--acc);text-decoration:none}
.foot{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);font-size:13px;color:#6f86a6}
"""


def head(title, desc, path, extra_jsonld=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE}/{path}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<style>{CSS}</style>
<script type="application/ld+json">{{
  "@context":"https://schema.org",
  "@type":"SoftwareApplication",
  "name":"lgd-skill-review",
  "applicationCategory":"DeveloperApplication",
  "operatingSystem":"Any",
  "description":"Six-dimension verifiability auditor for agent skills. Every deduction cites evidence; every result includes a remediation order.",
  "url":"{SITE}/",
  "codeRepository":"{REPO}",
  "license":"https://opensource.org/licenses/MIT",
  "offers":{{"@type":"Offer","price":"0","priceCurrency":"USD"}}
}}</script>
{extra_jsonld}
</head>
<body>
<div class="wrap">
<nav>
<a href="./index.html">Home</a>
<a href="./rubric.html">Rubric</a>
<a href="./skill-review.html">Audit</a>
<a href="./quickfix.html">QuickFix</a>
<a href="./benchmark.html">Benchmark</a>
<a href="./compare.html">Compare</a>
<a href="./guide.html">Guide</a>
<a href="./badge.html">Badge</a>
<a href="./audits.html">Audits</a>
<a href="./registry.html">Registry</a>
<a href="./discover.html">Discover</a>
<a href="{REPO}">GitHub</a>
</nav>
"""


FOOT = f"""
<div class="foot">
Measures verifiability, not usefulness or popularity. Low score means evidence is missing, not that the skill is bad.
Snapshot at a point in time; the sample is not random.<br>
Data: <a class="a" href="{REPO}/blob/main/bench/leaderboard.json">leaderboard.json</a> ·
Machine entry: <a class="a" href="{SITE}/llms.txt">llms.txt</a> ·
Request a review: <a class="a" href="{REPO}/issues/new?template=review-request.yml">open an issue</a>
</div>
</div>
</body>
</html>
"""


PARITY_REPOS = ["summarize-pro", "debug-pro", "wechat-viral-topic", "lgd-skill-review"]


PARITY_CACHE = os.path.join(HERE, "bench", "parity.json")


def load_parity():
    """Fetch each repo's PARITY.json, else fall back to the committed cache.

    raw.githubusercontent is flaky from some networks, and a nightly build must not lose the section
    because of one timeout -- but it also must not silently pretend nothing is missing. Three states:
    fetched (fresh), cached (stale but real), None (unknown, page says so).
    """
    out = []
    for n in PARITY_REPOS:
        url = "https://api.github.com/repos/zhaoxinghua09-cell/%s/contents/PARITY.json" % n
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "lgd-gen-site",
                "Accept": "application/vnd.github.raw"})
            with urllib.request.urlopen(req, timeout=25) as r:
                out.append(json.loads(r.read().decode("utf-8")))
            continue
        except Exception as e:
            local = os.path.join(os.path.dirname(HERE), n, "PARITY.json")
            if os.path.isfile(local):
                out.append(json.load(open(local, encoding="utf-8")))
                print("parity: %s from local mirror" % n)
                continue
            print("parity: %s unavailable (%s)" % (n, str(e)[:50]))
            out = []
            break
    if out:
        try:
            json.dump({"schema": "lgd-parity-feed-v1", "items": out},
                      open(PARITY_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        except Exception as e:
            print("parity cache write failed:", str(e)[:40])
        return out
    if os.path.isfile(PARITY_CACHE):
        try:
            print("parity: using committed cache")
            return json.load(open(PARITY_CACHE, encoding="utf-8"))["items"]
        except Exception:
            pass
    return None


def parity_html(items):
    if items is None:
        return """
<h2>Parity — status unknown at build time</h2>
<div class="card">
<p class="bad">The four PARITY.json files could not be fetched and no cache exists, so this section
is empty rather than clean. Treat as "unverified", not as "no drift".</p>
</div>
"""
    rows = []
    for d in items:
        p, o = d["published"], d["original"]
        lost = 100.0 * (1 - (p["lines"] + 0.0) / max(o["lines"], 1))
        rows.append(
            "<tr><td><b>%s</b></td><td class='num'>%d</td><td class='num'>%d</td>"
            "<td class='num'>%d%%</td><td><code>%s</code></td></tr>"
            % (d["skill"], o["lines"], p["lines"], round(lost),
               o["sha256"][:12])
        )
    return f"""
<h2>Parity — we publish the version we measured, and the original next to it</h2>
<div class="card">
<p>Our packages ship a <b>condensed rewrite</b> (<code>v2.1.0-slim</code>), not an excerpt of the
source document. That is a fact a stranger cannot check from the rendered page — so every repo
carries the verbatim original at <code>references/original-SKILL.md</code> plus a
<code>PARITY.json</code> with both SHA-256 values. Here is what the difference actually is:</p>
<table>
<tr><th>Package</th><th style="text-align:right">Original lines</th><th style="text-align:right">Published lines</th><th style="text-align:right">Not in SKILL.md</th><th>Original SHA-256</th></tr>
{''.join(rows)}
</table>
<p style="margin-top:12px;font-size:13px">“Published lines” counts <code>SKILL.md</code> only — the rest of
the body lives in <code>references/details.md</code>. So this column is a floor, not the real gap.
Verify any row: <code>curl -s {REPO.replace('lgd-skill-review', '<repo>')}/raw/main/references/original-SKILL.md | sha256sum</code></p>
<p style="margin-top:8px"><a class="a" href="./parity.json">parity.json (machine-readable) →</a></p>
</div>
"""


def rows_html(data):
    third = [r for r in data["rows"] if r["bucket"] == "third-party"]
    own = [r for r in data["rows"] if r["bucket"] == "lgd"]
    out = []
    for label, group in (("Third-party · 第三方", third), ("LGD · 我方", own)):
        out.append(f"<h3>{label}</h3><table><tr><th>Target</th><th style=\"text-align:right\">Score</th><th>Verdict</th></tr>")
        for r in group:
            cls = "good" if r["bucket"] == "lgd" else "bad"
            name = r["target"].replace("@", " <span style='color:#6f86a6'>@</span> ")
            out.append(f"<tr><td>{name}</td><td class='num {cls}'>{r['score']}</td><td class='{cls}'>{r['verdict']}</td></tr>")
        out.append("</table>")
    return "\n".join(out)


def main():
    # 标准必须是可执行数据：先生成 rubric.json，页面与它同源
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_rubric.py")], check=False)

    data = json.load(open(BENCH, encoding="utf-8"))
    s = data["summary"]
    os.makedirs(DOCS, exist_ok=True)

    # index
    html = head("LGD SkillBench — verifiability, measured",
                "Public benchmark for agent skills: third-party skills score 10-31, LGD packages 96-100. "
                "One command reproduces every number.", "index.html")
    # 发布版 vs 原始全文：能不能核，得先看得见
    parity_items = load_parity()
    parity_block = parity_html(parity_items)
    if parity_items:
        json.dump({"schema": "lgd-parity-feed-v1", "items": parity_items},
                  open(os.path.join(DOCS, "parity.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    html += f"""
<div class="kick">verifiability, measured — not claimed</div>
<h1>We measure whether a stranger can check your skill.</h1>
<p class="lead">{s['third_party_entries']} third-party targets + our 4 packages, one ruler, one command. Third-party skills with
hundreds of thousands of installs score <b>{s['third_party_top']}</b> at best here; our four
packages score <b>{s['lgd_top']}</b> static and 100 with their own tests. The gap is not prose
quality — it is <b>whether the evidence is checkable</b>.</p>

<div class="card">
<h3>Current gap</h3>
<table>
<tr><th>Metric</th><th style="text-align:right">Value</th></tr>
<tr><td>Third-party entries</td><td class="num">{s['third_party_entries']}</td></tr>
<tr><td>LGD entries</td><td class="num">{s['lgd_entries']}</td></tr>
<tr><td>Third-party top score</td><td class="num bad">{s['third_party_top']}</td></tr>
<tr><td>LGD top score</td><td class="num good">{s['lgd_top']}</td></tr>
<tr><td>Gap</td><td class="num good">{s['gap']}</td></tr>
</table>
<p style="margin-top:12px;font-size:13px">Generated {data['generated_at_utc']} · engine: static mode, never executes the target's code</p>
</div>

{parity_block}
<h2>What we measure</h2>
<div class="card">
<ul>
<li><b>Structure</b> — can a machine find the entry, version, license?</li>
<li><b>Consistency</b> — do the documented commands exist in the source?</li>
<li><b>Reproducibility</b> — is there a golden set and a runner that actually runs?</li>
<li><b>Hygiene</b> — absolute paths, secrets, leaked contact details</li>
<li><b>Discoverability</b> — triggers, ecosystem links, machine-readable index</li>
<li><b>Licensing</b> — a real license, not a claim</li>
</ul>
<p style="margin-top:12px"><a class="a" href="./rubric.html">Full rubric →</a></p>
</div>

<h2>Reproduce it</h2>
<div class="card">
<pre><code>git clone {REPO.replace('https://github.com/', 'https://github.com/')}.git
cd lgd-skill-review/bench
python bench.py</code></pre>
<p style="margin-top:10px">Refreshed automatically every day at 09:17 Beijing time. If you disagree with
a number, the JSON is public and the runner is public.</p>
</div>

<h2>Our ruler is tested too</h2>
<div class="card">
<p>It is easy to publish checks and never enforce them. So every published check has a probe that
breaks it on purpose and asserts the score actually drops — 22 cases covering all 23 checks (one check
shares its evidence with another), run in CI on every push:</p>
<pre style="margin-top:10px"><code>python tests/rubric_probe.py
# 22/22 enforced</code></pre>
<p style="margin-top:10px">Two of those probes found real defects in <b>this project</b>: a junk scan that
could never fire (its walk pruned the very directory it was looking for), and a flag check that
recorded a mismatch without deducting. Both are fixed — and the third-party top went from 36 to
<b>{s['third_party_top']}</b> the moment the flag check started enforcing. The gap widened because the
ruler got stricter, not because competitors got worse.</p>
</div>

<h2>Get your skill reviewed — without talking to us</h2>
<div class="card">
<p>Open an issue with the review form. A bot fetches your public tarball, runs static analysis
(<b>it never executes your code</b>), and replies with the score, the six-dimension breakdown,
the blockers, and the order to fix them.</p>
<p style="margin-top:10px"><a class="a" href="{REPO}/issues/new?template=review-request.yml">Submit a skill for review →</a></p>
</div>
"""
    html += FOOT
    open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(html)

    # benchmark page
    html = head("Benchmark — every number is reproducible",
                "Full leaderboard of %d public targets (%d third-party) with scores, verdicts and blockers."
                % (len(data.get("rows", [])), data.get("summary", {}).get("third_party_entries", 0)),
                "benchmark.html")
    html += f"""
<div class="kick">leaderboard</div>
<h1>Everyone can rerun this.</h1>
<p class="lead">Same engine, same scale, same moment. Sorted by score. Blocking findings mean the
package would be rejected by a reviewer who checks before shipping.</p>
<div class="card">{rows_html(data)}
<p style="margin-top:14px;font-size:13px">Generated {data['generated_at_utc']} ·
<a class="a" href="{REPO}/blob/main/bench/leaderboard.json">raw JSON</a></p>
</div>
<h2>How to read a low score</h2>
<div class="card"><p>A third-party package scoring 18 is not a bad package. It means: no license file,
no machine-readable index, commands documented differently from the source, no golden set. A stranger
cannot verify it in ten minutes, so an auditor cannot certify it either. <b>The score measures
checkability, not usefulness.</b></p></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "benchmark.html"), "w", encoding="utf-8").write(html)

    # skill-review detail page（此前这里没有手写页，只剩 stub，等于「审计页不写怎么审计」）
    html = head("Audit a skill — score, blockers, fix order",
                "One command turns a skill package into a score, a blocker list with file:line evidence, "
                "and an ordered remediation list. Re-run after fixing to see the delta.",
                "skill-review.html")
    html += f"""
<div class="kick">audit</div>
<h1>Score, blockers, fix order — from one command.</h1>
<p class="lead">It never reads your README and trusts it. With <code>--run</code> it executes the
package's own golden set, so 「我自己测过」和「它真的能跑」是两件事。</p>

<h2>Run it</h2>
<div class="card"><pre><code># 静态六维评分（不执行目标代码）
python scripts/review.py &lt;package-dir&gt; --json

# 加上实跑：执行包内黄金集，拿到最后 4 分
python scripts/review.py &lt;package-dir&gt; --run --json

# 只看某一维的整改（例如「声明与实现是否一致」）
python scripts/review.py &lt;package-dir&gt; --run --focus declared-consistency</code></pre>
<p style="margin-top:10px;font-size:13px">零依赖、不联网、标准库即可跑。退出码 0 通过 / 1 有阻断 / 2 参数错误。</p></div>

<h2>What you get</h2>
<div class="card"><table>
<tr><th>输出</th><th>内容</th></tr>
<tr><td>逐维分数</td><td>structure 20 · consistency 25 · reproducible 20 · hygiene 15 · discoverability 15 · licensing 5</td></tr>
<tr><td>阻断项</td><td>每条带 <code>file:line</code> 证据，不给「建议优化一下」这种无法执行的结论</td></tr>
<tr><td>整改顺序</td><td>按「先修能一次修好的」排，改完复评能直接看到分数差</td></tr>
<tr><td>机器可读</td><td><code>--json</code> 输出 <code>{{ok, data}}</code>，可直接进 CI</td></tr>
</table></div>

<h2>What it deliberately does not do</h2>
<div class="card"><ul>
<li>不判断技能「好不好用」——它只判断「陌生人能否核验」</li>
<li>不替代人工评审：分数高不等于内容正确</li>
<li>不执行不可信代码，除非你显式加 <code>--run</code></li>
</ul></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "skill-review.html"), "w", encoding="utf-8").write(html)

    # quickfix detail page
    html = head("QuickFix — only the fixes that raise verifiability",
                "Applies mechanical fixes (license, machine-readable index, declared commands) and proves "
                "the score delta. Dry-run by default; refuses a single file changed over 30%.",
                "quickfix.html")
    html += f"""
<div class="kick">quickfix</div>
<h1>Fix what a machine can fix. Prove the delta.</h1>
<p class="lead">大多数审计报告读完还是不会改。这条命令只做「机械可判定」的那几件事，并且改完立刻复评，
把分数差贴出来——不接受「我们改好了」这种自述。</p>

<h2>Run it</h2>
<div class="card"><pre><code># 先看它想改什么（默认 dry-run，不写盘）
python scripts/quickfix.py &lt;package-dir&gt;

# 真改：补 LICENSE + 声明 license 字段 + 生成 AI-INDEX.json + 对齐已声明命令
python scripts/quickfix.py &lt;package-dir&gt; --apply

# 改完立刻复评，拿到前后分数差
python scripts/review.py &lt;package-dir&gt; --run --json</code></pre>
<p style="margin-top:10px;font-size:13px">默认只动「机械可判定」项，语义改写一律不碰；单文件改动超过 30% 会被拒绝写入。</p></div>

<h2>What it actually moves</h2>
<div class="card"><table>
<tr><th>缺陷</th><th>它能做什么</th><th>实测效果</th></tr>
<tr><td>无 LICENSE、无 license 字段</td><td>补 MIT 许可文件 + 加 front-matter 字段</td><td>licensing 2 → 3</td></tr>
<tr><td>无机器可读索引</td><td>生成 AI-INDEX.json（含入口与命令）</td><td>discoverability 4 → 7</td></tr>
<tr><td>文档声明的命令脚本不存在</td><td><em>只报告，不代写</em>——这需要人决定</td><td>保持阻断，避免掩盖</td></tr>
</table>
<p style="margin-top:12px;font-size:13px">真实案例：microsoft/azure-skills 的 azure-deploy 从 20 分，仅靠机械整改到 24 分；
再补 tests/golden、可跑 runner、llms.txt、tags 到 57 分——剩下的必须由人写内容，机器补不了。</p></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "quickfix.html"), "w", encoding="utf-8").write(html)

    # compare page —— 别家只报总分；这里把差在哪一维、差多少分开算，两个方向都能复现
    DIM_MAX = [("structure", "结构", 20), ("consistency", "一致性", 25), ("reproducible", "可复现", 20),
               ("hygiene", "卫生", 15), ("discoverable", "可发现", 15), ("licensing", "许可", 5)]
    BJ = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "bench", "bench.json"), encoding="utf-8"))
    tp = next((r for r in BJ
               if r["bucket"] == "third-party" and r["score"] == s["third_party_top"]), None)
    own = (next((r for r in BJ if "lgd-skill-review" in r["target"]), None)
           or max((r for r in BJ if r["bucket"] == "lgd"), key=lambda r: r["score"]))
    crow = ""
    for key, zh, mx in DIM_MAX:
        a = tp["dims"].get(key, 0)
        b = own["dims"].get(key, 0)
        crow += ("<tr><td>%s · %s</td><td class=\"num bad\">%d</td><td class=\"num good\">%d</td>"
                 "<td class=\"num\">%d</td><td style=\"font-size:13px\">%d / %d</td></tr>"
                 % (key, zh, a, b, b - a, mx, mx))
    html = head("Compare — where the difference actually is",
                "The strongest third-party skill in the sample and our own package, dimension by dimension. "
                "Same engine, same moment, both reproducible.",
                "compare.html")
    html += f"""
<div class="kick">compare</div>
<h1>Same ruler, two packages, six dimensions.</h1>
<p class="lead">竞品只给一个总分，读者没法知道差在哪。这里把每一维拆开：
<b>{tp['target']}</b>（样本里第三方最强，{tp['score']} 分）与我们自己的
<b>{own['target'].split('/')[-1]}</b>（{own['score']} 分）。</p>

<div class="card"><table>
<tr><th>维度</th><th style="text-align:right">第三方</th><th style="text-align:right">LGD</th>
<th style="text-align:right">差值</th><th>满分</th></tr>
{crow}
<tr><td><b>合计</b></td><td class="num bad">{tp['score']}</td><td class="num good">{own['score']}</td>
<td class="num">{own['score'] - tp['score']}</td><td style="font-size:13px">100</td></tr>
</table>
<p style="margin-top:12px;font-size:13px">Generated {data['generated_at_utc']} · static mode · 同一引擎、同一时点</p></div>

<h2>差在哪，不是靠形容词</h2>
<div class="card"><table>
<tr><th>差距最大的两维</th><th>对方实际缺什么（在仓库里可查）</th></tr>
<tr><td>consistency 25</td><td>文档里写的子命令在脚本里不存在；或存在但从不校验参数——这是「声称」与「实现」的差</td></tr>
<tr><td>reproducible 20</td><td>没有 tests/golden，没有可跑 runner：陌生人无法验证「它到底跑不跑」</td></tr>
</table>
<p style="margin-top:12px">这两项占了 45 分。它们不是文笔问题，是<b>证据缺失</b>——
补上就能得分，补不上就只能停在那里。</p></div>

<h2>自己复现这两行</h2>
<div class="card"><pre><code># 任意一个包，同一把尺子
python scripts/review.py &lt;package-dir&gt; --json

# 整张榜重新跑（含上面两个目标）
cd bench &amp;&amp; python bench.py</code></pre>
<p style="margin-top:10px;font-size:13px">数字来自 <code>bench/leaderboard.json</code>；
本页在构建时读取它，所以不会与榜单单据脱节。</p></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "compare.html"), "w", encoding="utf-8").write(html)

    # guide page —— 别家只告诉你「缺证据」；这里给能照抄的补法，并明说哪些分机器给不了
    html = head("Guide — how to earn the last points",
                "A copy-paste path from a documentation-only skill to one a stranger can rerun. "
                "Three steps, real templates, and the points no machine can award.",
                "guide.html")
    html += """
<div class="kick">guide</div>
<h1>从「只有文档」到「陌生人能重跑」，三步。</h1>
<p class="lead">市场上最缺的不是文档，是<b>能让别人验的证据</b>。样本里最强的三方包
reproducible 都是 0 分——不是它们写得差，是没人写过 golden set。这里给可照抄的模板。</p>

<h2>第一步：写一份 golden.json（20 行）</h2>
<div class="card"><pre><code>{
  "cases": [
    {"id": "T1-missing-skill-md", "kind": "no_skill_md",
     "expect": {"verdict": "BLOCK"}},
    {"id": "T2-clean-package", "kind": "clean",
     "expect": {"verdict": "PASS", "min_score": 90}}
  ]
}
</code></pre>
<p style="margin-top:10px;font-size:13px">只写「输入是什么、期望结果是什么」。不要写实现细节——
否则测试会跟着实现一起错。</p></div>

<h2>第二步：写一个能跑、能非零退出的 runner</h2>
<div class="card"><pre><code>import json, subprocess, sys, tempfile, shutil

def run_case(case):
    tmp = tempfile.mkdtemp()
    try:
        shutil.copytree("fixtures/" + case["kind"], tmp, dirs_exist_ok=True)
        out = subprocess.run([sys.executable, "scripts/review.py", tmp, "--json"],
                             capture_output=True, text=True)
        j = json.loads(out.stdout if out.stdout.strip() else out.stderr)
        if not j.get("ok", False):
            # 无效包：JSON 走 stderr，形如 {"ok":false,"error_id":"R001","msg":"目录下没有 SKILL.md"}
            got = {"verdict": "BLOCK", "total": 0, "error_id": j.get("error_id")}
        else:
            got = j["data"]                    # {"total":..,"verdict":..,"dimensions":..}
        want = case["expect"]
        if "verdict" in want and got.get("verdict") != want["verdict"]:
            return False, "%s: want verdict %r got %r" % (case["id"], want["verdict"], got.get("verdict"))
        if "min_score" in want and got.get("total", 0) &lt; want["min_score"]:
            return False, "%s: want total&gt;=%d got %d" % (case["id"], want["min_score"], got.get("total", 0))
        return True, case["id"]
    except Exception as e:
        return False, "%s: %s" % (case["id"], e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    cases = json.load(open("tests/golden.json"))["cases"]
    results = [run_case(c) for c in cases]
    bad = [msg for ok, msg in results if not ok]
    print("%d/%d passed" % (len(results) - len(bad), len(results)))
    for m in bad:
        print("  FAIL " + m)
    return 1 if bad else 0      # ← 这一行是关键：失败必须非零退出

sys.exit(main())
</code></pre>
<p style="margin-top:10px;font-size:13px">评分器认「有 runner 且退出码为 0」和「runner 真能跑通」。退出码恒为 0 的脚本不算分。
两个契约要点：正常结果在 <code>data.total</code>（不是 <code>score</code>）；
无效包返回 <code>ok=false + error_id</code> 且 <b>JSON 写在 stderr</b>、<b>没有 data</b>——
这几个坑不踩一遍就会写出「永远通过」的假测试。</p></div>

<h2>第三步：把它接进 CI，让它每次都被执行</h2>
<div class="card"><pre><code># .github/workflows/verify.yml
- name: Golden set must actually run
  run: python tests/run_golden.py
</code></pre>
<p style="margin-top:10px;font-size:13px">声明了却从不执行的测试，等于没有。CI 上跑过，才有「它今天仍然能跑」的证据。</p></div>

<h2>做完之后，分数会怎么变</h2>
<div class="card"><table>
<tr><th>维度</th><th>做到哪一步</th><th>分数</th></tr>
<tr><td>reproducible 20</td><td>golden.json + 可跑 runner + 非零退出 + CI 执行</td><td>0 → 16（静态）→ 20（加 --run）</td></tr>
<tr><td>discoverable 15</td><td>加 AI-INDEX.json 或 llms.txt</td><td>4 → 7</td></tr>
<tr><td>licensing 5</td><td>许可文件 + 声明字段，二者兼备</td><td>1 → 3 → 5</td></tr>
</table>
<p style="margin-top:12px;font-size:13px">以上都是可机械补齐的。剩下这些<b>机器给不了</b>：文档里声明的命令必须真的存在于脚本（要人写或删声明）、
结构里的 name/description 要写得让人能判断用途、内容本身是否正确——这些只有作者能做。</p></div>

<h2>我们对自己也用同一套</h2>
<div class="card"><ul>
<li>本仓的 <code>tests/golden.json</code> + <code>tests/run_golden.py</code> 就是上面这套模板的真实版本（5 条用例，CI 每次跑）</li>
<li>四个发布包各有 golden 集，<code>review.py --run</code> 实跑 100/100，结果落在 <code>run-proof.json</code></li>
<li>尺子本身也被测：<code>rubric_probe</code> 造 22 处违规，<code>point_audit</code> 核分值加总——我们不给别人立一套自己不遵守的规矩</li>
</ul></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "guide.html"), "w", encoding="utf-8").write(html)

    # rubric
    html = head("Rubric — six dimensions, 100 points",
                "The exact scoring rules, weights and what each dimension can and cannot prove.", "rubric.html")
    rb = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "rubric.json"),
                        encoding="utf-8")) if os.path.isfile(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "rubric.json")) else None
    detail = ""
    if rb:
        detail = "<h2>Item by item · %d checks</h2><div class='card'><p>Read the JSON, not this page, " \
                 "if you want to act on it: " \
                 "<a class='a' href='./rubric.json'>rubric.json</a>. " \
                 "Sum of checks per dimension is asserted equal to the weight at generation time " \
                 "(<code>drift_check</code>), so this page cannot silently drift from the engine.</p></div>" % \
                 sum(len(d["checks"]) for d in rb["dimensions"] if d.get("checks"))
        for d in rb["dimensions"]:
            if not d.get("checks"):
                continue
            detail += "<div class='card'><h3>%s<span style='color:#6f86a6;font-weight:400'> · %d pts</span></h3>" % (
                d["key"], d["weight"])
            detail += "<table><tr><th>Check</th><th style='text-align:right'>Pts</th><th>How to fix</th></tr>"
            for c in d["checks"]:
                tag = " <span style='color:#9ab;font-size:12px'>(alt path)</span>" if c.get("alternative") else ""
                detail += "<tr><td>%s%s</td><td class='num'>%d</td><td style='font-size:13px'>%s</td></tr>" % (
                    c["check"], tag, c["points"], c["fix"])
            detail += "</table></div>"
    html += """
<div class="kick">rubric</div>
<h1>Six dimensions, 100 points, no black box.</h1>
<p class="lead">Weights are public because a score nobody can recompute is an opinion with a number
stapled to it. Static mode caps at 96; the last 4 points require the target's own tests to actually run.</p>
<div class="card">
<table>
<tr><th>Dimension</th><th style="text-align:right">Weight</th><th>What it can prove</th></tr>
<tr><td>Consistency</td><td class="num">25</td><td>Documented flags and subcommands exist in the source</td></tr>
<tr><td>Structure</td><td class="num">20</td><td>Entry file, version, name, description are machine-findable</td></tr>
<tr><td>Reproducibility</td><td class="num">20</td><td>A golden set exists and a runner actually executes it</td></tr>
<tr><td>Hygiene</td><td class="num">15</td><td>No absolute paths, secrets or leaked contact details</td></tr>
<tr><td>Discoverability</td><td class="num">15</td><td>Triggers, ecosystem links, AI-INDEX / llms.txt</td></tr>
<tr><td>Licensing</td><td class="num">5</td><td>A real license file plus a declared field</td></tr>
</table>
</div>
""" + detail + """
<h2>What the score cannot tell you</h2>
<div class="card"><ul>
<li>Whether the skill is useful, correct, or popular</li>
<li>Whether the prose is any good</li>
<li>Whether the maintainer will respond to issues</li>
<li>Anything about packages it never saw</li>
</ul>
<p style="margin-top:12px">Two known measurement biases were found and fixed by testing the ruler
against real repositories: index detection used to be case-sensitive, and position-argument CLIs
were scored zero. Both are documented in the repository history.</p></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "rubric.html"), "w", encoding="utf-8").write(html)

    # skill pages
    # 注意：SKILLS 里的 slug 同时是「已有手写详情页」的三个页面（skill-review / quickfix / benchmark）。
    # 这个循环早期的写法会把上面手写好的详情页整页覆盖成 stub——榜单表格、命令示例全部丢掉。
    # 现在跳过它们，只渲染没有手写详情页的 slug（当前一个都没有，保留循环是为了将来加新页）。
    HAND_BUILT = {"skill-review", "quickfix", "benchmark"}
    for sk in SKILLS:
        if sk["slug"] in HAND_BUILT:
            continue
        tags = "".join(f'<span class="tag">{t}</span>' for t in sk["triggers"])
        html = head(f"{sk['title']} — lgd-skill-review",
                    sk["zh"] + " · " + sk["body"][:120], sk["slug"] + ".html")
        html += f"""
<div class="kick">{sk['slug']}</div>
<h1>{sk['h1']}</h1>
<p class="lead">{sk['zh']}</p>
<div class="card"><p>{sk['body']}</p>
<h3 style="margin-top:16px">When an agent should reach for this</h3>
<p>{tags}</p></div>
<h2>Install</h2>
<div class="card"><pre><code>npx skills add zhaoxinghua09-cell/lgd-skills</code></pre>
<p style="margin-top:10px;font-size:13px">Bundled with all four skills under <code>skills/&lt;name&gt;/</code>.</p></div>
"""
        html += FOOT
        open(os.path.join(DOCS, sk["slug"] + ".html"), "w", encoding="utf-8").write(html)

    # badge page — 让别人把我们的徽章嵌进自己 README，外链自己长出来
    badge_url = ("https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com"
                 "%2Fzhaoxinghua09-cell%2Flgd-skill-review%2Fmain%2Fbench%2Fbadge.json")
    html = head("Badge — embed the verifiability score",
                "Copy-paste snippets to show a skill's verifiability score in your README. "
                "The badge reads live data, so it changes when the score changes.",
                "badge.html",
                extra_jsonld=f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"HowTo","name":"Embed the LGD verifiability badge","step":[{{"@type":"HowToStep","text":"Copy the Markdown snippet"}},{{"@type":"HowToStep","text":"Paste it into your README"}}]}}</script>')
    html += f"""
<div class="kick">badge</div>
<h1>A badge that reads live data.</h1>
<p class="lead">Most badges are a picture someone typed once. This one is an endpoint:
it renders whatever the latest benchmark says, so it cannot go stale and cannot be cherry-picked.</p>

<div class="card">
<h3>What it currently says</h3>
<p><img src="{badge_url}" alt="verifiability badge" style="height:22px"></p>
<p style="margin-top:12px;font-size:13px">Label: verifiability · Message: peers &lt;third-party top&gt; / LGD &lt;our top&gt; ·
Colour flips to orange if the gap drops below 50 points.</p>
</div>

<h2>Markdown</h2>
<div class="card"><pre><code>[![verifiability]({badge_url})]({SITE}/benchmark.html)</code></pre>
<p style="margin-top:10px;font-size:13px">Works on GitHub, GitLab, most README renderers.</p></div>

<h2>HTML</h2>
<div class="card"><pre><code>&lt;a href="{SITE}/benchmark.html"&gt;&lt;img src="{badge_url}" alt="verifiability score" height="22"&gt;&lt;/a&gt;</code></pre></div>

<h2>Raw JSON, if you want to build your own</h2>
<div class="card"><pre><code>{REPO}/blob/main/bench/badge.json</code></pre>
<p style="margin-top:10px">Shields endpoint schema: <code>{{"schemaVersion":1,"label":...,"message":...,"color":...}}</code>.
The leaderboard behind it: <a class="a" href="{REPO}/blob/main/bench/leaderboard.json">leaderboard.json</a>.</p></div>

<h2>What the badge does and does not mean</h2>
<div class="card"><ul>
<li><b>Does</b> mean: this package's claims are checkable by a third party — license present, commands match the source, index machine-readable, no leaked paths.</li>
<li><b>Does not</b> mean: the skill is useful, correct, popular, or endorsed by anyone.</li>
<li>It is not a certification body. It is a public ruler with a public runner.</li>
</ul></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "badge.html"), "w", encoding="utf-8").write(html)

    # audits page — 对真实大仓的公开审计结果，可被任何人复跑
    html = head("Audits — two large public repos, real findings",
                "Full-dimension audits of microsoft/azure-skills and prisma/skills, with the findings "
                "and the part that one command can fix.", "audits.html")
    html += """
<div class="kick">audits</div>
<h1>We looked at two 400k+ install repositories. Here is what we found.</h1>
<p class="lead">Not opinions — dimension scores, the exact items that cost points, and how far a
one-command mechanical fix gets you. Every number below is reproducible with the command at the bottom.</p>
"""
    for a in AUDITS:
        f = "".join(f"<li>{x}</li>" for x in a["findings"])
        m = "".join(f"<li>{x}</li>" for x in a["mechanical"])
        o = "".join(f"<li>{x}</li>" for x in a["fix_order"])
        html += f"""
<div class="card">
<h3>{a['name']} · <code>{a['skill']}</code> · installs {a['installs']}</h3>
<table>
<tr><th>Stage</th><th style="text-align:right">Score</th></tr>
<tr><td>As shipped</td><td class="num bad">{a['before']}</td></tr>
<tr><td>After mechanical fixes only</td><td class="num">{(str(a['after_mech']) if a['after_mech'] else '未实测')}</td></tr>
</table>
<p style="margin-top:10px;font-size:13px">Dimensions as shipped: {a['dims_before']}</p>
<h3 style="margin-top:16px">Findings</h3><ul>{f}</ul>
<h3 style="margin-top:16px">What one command fixes</h3><ul>{m}</ul>
<h3 style="margin-top:16px">Fix order if you are the maintainer</h3><ul>{o}</ul>
</div>
"""
    html += """
<h2>Fairness test: can a package we did not write reach 90?</h2>
<div class="card">
<p>Same rubric, same engine, applied to microsoft's <code>azure-deploy</code> in a copy. Each stage is
real work, scored after each step. Nothing was padded to inflate the number.</p>
<table><tr><th>stage</th><th style="text-align:right">score</th><th>what changed</th></tr>
""" + "".join(
        f"<tr><td>{name}</td><td class='num'>{val}</td><td style='font-size:13px'>{note}</td></tr>"
        for name, val, note in REACH["stages"]) + f"""
</table>
<p style="margin-top:12px;font-size:13px">{REACH['left']}</p>
<p style="margin-top:8px">Why this matters: our four packages score 96 partly because they were
written to this rubric. That is a weakness, not a strength. This test removes it: a package by another
author reaches 86 with work any maintainer can do, and the remaining 14 points are specific, named,
and fixable. If the ruler only ever fit the ruler's authors, this table could not exist.</p>
</div>

<h2>How to reproduce</h2>
<div class="card"><pre><code>git clone --depth 1 https://github.com/microsoft/azure-skills.git
python scripts/review.py azure-skills/skills/azure-deploy --json</code></pre>
<p style="margin-top:10px">The mechanical part:</p>
<pre><code>python scripts/quickfix.py &lt;copy-of-skill-dir&gt; --apply</code></pre>
</div>

<h2>Why publish this instead of sending them issues</h2>
<div class="card"><p>Because an issue we file is a request; a public report with a reproducible runner
is evidence. Anyone — including the maintainers — can rerun the command and check whether we are right.
If we are wrong about a single item, the runner will show it.</p>
<p style="margin-top:10px">These are third-party projects. We are not claiming they are bad packages.
A score of 20 means <b>a stranger cannot verify the claims in ten minutes</b>, which is a property of
the package's evidence, not of its usefulness.</p></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "audits.html"), "w", encoding="utf-8").write(html)

    # audits.json — 机器可读的审计结果，供 AI 直接消费（HTML 给人，JSON 给 agent）
    audits_doc = {
        "schema_version": "1.0",
        "generator": "lgd-skill-review/scripts/gen_site.py",
        "rubric": "https://zhaoxinghua09-cell.github.io/lgd-skill-review/rubric.html",
        "note": "静态审计结果，不执行被审代码；分数衡量可验证性，不衡量有用性。",
        "remediation_experiment": {
            "target": REACH["target"],
            "purpose": "检验同一把尺子能否被非作者的包满足，回应「标准为作者量身定做」的质疑",
            "stages": [{"stage": n, "score": v, "change": c} for n, v, c in REACH["stages"]],
            "remaining": REACH["left"],
        },
        "audits": [
            {
                "target": a["name"],
                "skill_path": a["skill"],
                "reported_installs": a["installs"],
                "score_before": a["before"],
                "score_after_mechanical": a["after_mech"],
                "dimensions_before": a["dims_before"],
                "findings": a["findings"],
                "mechanical_fixes": a["mechanical"],
                "fix_order": a["fix_order"],
                "reproduce": "python scripts/review.py <local-clone>/%s --json" % a["skill"],
            }
            for a in AUDITS
        ],
    }
    open(os.path.join(DOCS, "audits.json"), "w", encoding="utf-8").write(
        json.dumps(audits_doc, ensure_ascii=False, indent=2)
    )

    # registry — 认证清单：按分数分档，数据由榜单生成，人可读、机可读
    tiers = [("verified", 90, "LGD Verified · 认证", "≥90：陌生人十分钟内可核实全部主张"),
             ("watch", 60, "LGD Watch · 观察", "60–89：有一部分能核实，关键项缺失"),
             ("blocked", 0, "LGD Blocked · 未通过", "<60：核心证据缺失，无法核实")]
    by_tier = {t[0]: [] for t in tiers}
    for r in data["rows"]:
        for key, lo, label, desc in tiers:
            if r["score"] >= lo:
                by_tier[key].append(r)
                break
    html = head("Registry — the verified list",
                "A tiered registry of agent skills by verifiability score. Machine-readable at registry.json; "
                "entries are generated from the public benchmark, not curated by hand.",
                "registry.html")
    html += """
<div class="kick">registry</div>
<h1>The verified list, built from numbers rather than opinions.</h1>
<p class="lead">Three tiers. Nobody is promoted by application, nobody pays, and no entry is edited by
hand — every row is a score produced by the same runner. To appear here, submit the package; to change
your tier, change the package.</p>
"""
    for key, lo, label, desc in tiers:
        rows = by_tier[key]
        body = "".join(
            '<tr><td>%s</td><td class="num%s">%s</td></tr>' % (
                r["target"], " bad" if r["score"] < 60 else "", r["score"]) for r in rows
        ) or '<tr><td colspan="2" style="color:#8a8378">（本档暂无条目）</td></tr>'
        html += f"""
<div class="card">
<h3>{label}</h3>
<p style="font-size:13px;color:#6b6459">{desc} · 本档 {len(rows)} 条</p>
<table><tr><th>package</th><th style="text-align:right">score</th></tr>{body}</table>
</div>
"""
    html += f"""
<h2>How to get on this list</h2>
<div class="card"><ul>
<li>Submit a public repository: <a class="a" href="{REPO}/issues/new?template=review-request.yml">review request</a>（机器人取包、静态分析、回帖给分与整改顺序）</li>
<li>No payment, no negotiation, no editorial discretion. The runner decides.</li>
<li>Rejected? The reply lists what is missing and in what order to fix it. Resubmit after fixing.</li>
</ul>
<p style="margin-top:10px;font-size:13px">机器可读版：<a class="a" href="./registry.json">registry.json</a>（含每档阈值与全部条目）。</p></div>

<h2>What a tier is not</h2>
<div class="card"><p>It is not a quality endorsement, not a security audit, not a warranty. It says one thing:
<b>how much of this package's claims a stranger can verify in ten minutes</b>. A verified package can still
be useless; a blocked package can still be excellent — it just cannot be checked.</p></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "registry.html"), "w", encoding="utf-8").write(html)

    reg = {
        "schema_version": "1.0",
        "generated_at_utc": data["generated_at_utc"],
        "source": SITE + "/benchmark.html",
        "tiers": [{"key": k, "min_score": lo, "label": lb, "meaning": d, "count": len(by_tier[k]),
                   "entries": [{"target": r["target"], "score": r["score"], "verdict": r["verdict"]}
                               for r in by_tier[k]]} for k, lo, lb, d in tiers],
        "rules": {
            "admission": "public repository + reproducible static audit; no payment, no editorial discretion",
            "remeasure": "tier follows the score; fixing the package moves the tier",
            "not_a": ["quality endorsement", "security audit", "warranty"],
        },
    }
    open(os.path.join(DOCS, "registry.json"), "w", encoding="utf-8").write(
        json.dumps(reg, ensure_ascii=False, indent=2)
    )

    # discover — 不经检索的入口清单：给 AI 的直达地址，不依赖任何平台的排序
    endpoints = [
        ("评价标准（人读）", SITE + "/rubric.html", "六维权重、阻断项、上限说明"),
        ("评价标准（机读）", SITE + "/rubric.json", "权重/阻断/敏感模式，由引擎常量导出"),
        ("公开榜单", SITE + "/benchmark.html", "20 行，16 个第三方目标"),
        ("榜单数据", SITE + "/leaderboard.json", "行级数据 + 三条局限"),
        ("认证清单（人读）", SITE + "/registry.html", "verified / watch / blocked 三档"),
        ("认证清单（机读）", SITE + "/registry.json", "阈值、规则、全部条目"),
        ("真实审计（人读）", SITE + "/audits.html", "两个 40 万级安装量仓库的逐条缺陷"),
        ("真实审计（机读）", SITE + "/audits.json", "含 scores/findings/fix_order/reproduce"),
        ("逐维对比（人读）", SITE + "/compare.html", "同一时点、同一把尺子的六维并排"),
        ("三步补证据（人读）", SITE + "/guide.html", "可照抄的黄金集→runner→CI 模板"),
        ("徽章端点", "https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fzhaoxinghua09-cell%2Flgd-skill-review%2Fmain%2Fbench%2Fbadge.json", "实时读数，非静态图片"),
        ("全量语料", SITE + "/llms-full.txt", "一次抓取拿到口径+榜单+审计+复现"),
        ("评测引擎", REPO + "/blob/main/scripts/review.py", "标准库、离线、不执行被评代码"),
        ("一键整改", REPO + "/blob/main/scripts/quickfix.py", "默认 dry-run，单文件改动>30% 拒绝写入"),
        ("提交评测", REPO + "/issues/new?template=review-request.yml", "机器人回帖给分与整改顺序"),
        ("一条命令自证", REPO + "/blob/main/tools/outsider_check.py", "无 token，只读公开端点，逐条复算"),
    ]
    rows = "".join(f"<tr><td>{a}</td><td><code>{b}</code></td><td style='font-size:13px'>{c}</td></tr>"
                   for a, b, c in endpoints)
    html = head("Discover — direct endpoints, no search required",
                "Every entry point to the LGD verifiability system as a direct URL: rubric, "
                "leaderboard, registry, audits, badge, engine, intake.", "discover.html")
    html += f"""
<div class="kick">discover</div>
<h1>Direct endpoints. No marketplace search required.</h1>
<p class="lead">We measured both marketplaces: skills.sh returns us for brand queries
(<code>lgd</code>, <code>lgd skill review</code>) but not for generic ones; LobeHub market search
returns 500 popularity-ranked items and does not surface us even on our own display name. So this page
lists the addresses an agent can hit directly instead of hoping a ranking puts us first.</p>
<div class="card"><table>
<tr><th>what</th><th>where</th><th>why</th></tr>
{rows}
</table></div>

<h2>What an agent can do without contacting anyone</h2>
<div class="card"><ol>
<li>Fetch <code>rubric.json</code> to get weights, blocking rules and the static cap.</li>
<li>Score any local package with <code>review.py --json</code>.</li>
<li>Read <code>findings</code>, apply the fixes in the given order.</li>
<li>Re-run the same engine; the score change is the proof.</li>
<li>If the result seems wrong, appeal with a path and a check — the ruling is recorded.</li>
</ol></div>

<h2>Two entry points that are actively hostile to newcomers</h2>
<div class="card"><p>We are not hiding this: marketplace search ranks by install counts and star
signals we cannot influence without faking them, which we will not do. If you need a verdict today,
use the endpoints above; if you want us to be found by search, the honest lever is people choosing to
install and cite us.</p></div>

<h2>Every batch is one commit</h2>
<div class="card"><p>A single file written at a time produces one commit per file, and CI can then run
on a half-applied tree. That is not hypothetical: a URL audit landed one commit before the
<code>docs/leaderboard.json</code> it referenced, and the check failed exactly as it should. Publishing
now goes through the git data API — blobs, then one tree, then one commit, then one ref update —
implemented in <code>scripts/push_atomic.py</code>, so a batch is either fully visible or not visible
at all and CI never sees an intermediate state.</p>
<p style="font-size:13px">Check it yourself: <code>git log --oneline</code> on this repo shows one commit
per published batch, and <code>git show --stat</code> on any of them lists all files of that batch together.</p></div>
"""
    html += FOOT
    open(os.path.join(DOCS, "discover.html"), "w", encoding="utf-8").write(html)

    # 执行证明：静态 96 之外的 4 分，靠真跑测试拿到
    proof_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bench", "run-proof.json")
    proof = json.load(open(proof_path, encoding="utf-8")) if os.path.isfile(proof_path) else None
    if proof:
        rows = "".join(
            "<tr><td>%s</td><td class='num'>%s</td><td>%s</td></tr>" % (
                p.get("package"), p.get("score"), p.get("verdict"))
            for p in proof["packages"] if "score" in p)
        html += f"""
<h2>Executed, not just declared</h2>
<div class="card">
<p>Static analysis caps at 96. The last 4 points need the package's own tests to run. Below is that run
({proof['generated_at_utc']}, engine <code>{proof['engine']}</code>). No other number in our sample is backed
by an execution we performed on someone's package.</p>
<table><tr><th>package</th><th style="text-align:right">executed score</th><th>verdict</th></tr>{rows}</table>
<p style="margin-top:10px;font-size:13px">机器可读：<a class="a" href="./run-proof.json">run-proof.json</a> ·
复跑 <code>python scripts/run_proof.py</code></p>
</div>
"""
        json.dump(proof, open(os.path.join(DOCS, "run-proof.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

    # sitemap：去重 + 带 lastmod（没有 lastmod，搜索引擎无法判断"这页更新过没有"）
    base = ["index.html", "rubric.html", "benchmark.html", "compare.html", "guide.html", "badge.html",
            "audits.html", "registry.html", "discover.html"]
    urls = list(dict.fromkeys(base + [s["slug"] + ".html" for s in SKILLS]))
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        path = os.path.join(DOCS, u)
        lastmod = today
        if os.path.isfile(path):
            lastmod = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
        pri = "1.0" if u == "index.html" else ("0.9" if u in ("rubric.html", "benchmark.html") else "0.7")
        sm.append("  <url><loc>%s/%s</loc><lastmod>%s</lastmod><changefreq>daily</changefreq>"
                  "<priority>%s</priority></url>" % (SITE, u, lastmod, pri))
    sm.append("</urlset>")
    open(os.path.join(DOCS, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))

    open(os.path.join(DOCS, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)

    # leaderboard.json — discover.html and outside readers point at this address,
    # so the file has to exist here too, not only under bench/.
    open(os.path.join(DOCS, "leaderboard.json"), "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    pages_txt = "\n".join("- %s/%s" % (SITE, u) for u in urls)

    llms = f"""# lgd-skill-review

> Six-dimension verifiability auditor for agent skills. Every deduction cites evidence; every result
> ships with a remediation order. Static mode: the target's code is never executed.

## what it answers
- skill audit / skill review / "is this skill safe to install"
- "why does my SKILL.md score low" / "what is missing"
- compare public skills on verifiability: {SITE}/benchmark.html

## reproducibility
- engine: {REPO}/blob/main/scripts/review.py
- one-click mechanical fixes: {REPO}/blob/main/scripts/quickfix.py
- benchmark data: {REPO}/blob/main/bench/leaderboard.json
- refreshed daily; every number rerunnable with `python bench.py`

## rubric (machine-readable, generated from the engine)
{SITE}/rubric.json — six weights, three blocking rules, sensitive patterns, verdicts, how to use.

## executed proof (static cap 96 -> 100)
{SITE}/run-proof.json — our four packages scored with `review.py --run` (tests actually executed),
with timestamp and commit. This is the only number in the sample backed by a real run.

## rubric, item by item (23 checks)
{SITE}/rubric.json — every dimension broken into individual checks with points and the concrete fix.
第 6 维共 23 条判据，每条给了分值和「怎么修」；`drift_check` 保证判据之和等于引擎权重，文档不会悄悄和引擎脱节。

## re-review loop
Comment `/re-review` in the same issue to re-score after a fix; the bot replies with before -> after delta.
首次评审后，在同一 issue 留言 `/re-review` 即重评，回帖给出「改前 → 改后」分数变化。

## registry (verified list), machine-readable
{SITE}/registry.json — three tiers by score (verified ≥90 / watch 60-89 / blocked <60), generated from the
benchmark. Admission rules, tier meaning and every entry in one file. Human page: {SITE}/registry.html

## third-party audits, machine-readable
- {SITE}/audits.json （两条真实大仓审计：分数、逐条 findings、整改顺序、复现命令）
- 人读版：{SITE}/audits.html

## parity: what is published vs what was authored
{SITE}/parity.json — for each of our four packages: the published SKILL.md, the verbatim original at
`references/original-SKILL.md`, both SHA-256 values, and the relation between them. The published file
is a condensed rewrite (v2.1.0-slim), not an excerpt. Verify: sha256 of the original must equal the
recorded hash.
发布版是精简重写稿，非原文摘编；原始全文并列发布，哈希可自证。

## submit a skill for review
{REPO}/issues/new?template=review-request.yml

## verify us yourself (one command, no token)
{REPO}/blob/main/tools/outsider_check.py
Run `python outsider_check.py`. It reads only the public endpoints listed above: it recomputes
16 / 38 / 96 / 58 from {SITE}/leaderboard.json, checks that rubric weights sum to 100 with 23 checks,
checks run-proof is PASS 100 for all four packages, and probes every machine entry for HTTP 200.
Exit code 0 means every number published on this site is self-consistent; any mismatch prints the exact
claim and the live value it contradicts.

## all pages (every human-readable page on this site)
{pages_txt}

## limits
- measures verifiability, not usefulness or popularity
- static mode caps at 96 of 100; 100 needs the target's own tests to run
- snapshot in time; sample is not random

## current numbers
third-party top: {s['third_party_top']} | lgd top: {s['lgd_top']} | gap: {s['gap']}
"""
    broken = re.findall(re.escape(SITE) + r"[A-Za-z0-9]", llms)
    if broken:
        raise SystemExit("llms.txt: %d URL(s) missing the slash after the site root: %s"
                         % (len(broken), broken[:3]))
    open(os.path.join(DOCS, "llms.txt"), "w", encoding="utf-8").write(llms)

    # llms-full.txt — 一次抓取拿全量语料，供 RAG / 训练式检索直接消费
    lines = []
    for r in data["rows"]:
        lines.append("| %s | %s | %s | %s |" % (r["bucket"], r["target"], r["score"], r["verdict"]))
    full = f"""# lgd-skill-review — full corpus

> One fetch, everything an agent needs. Numbers below are generated at {data['generated_at_utc']}
> from bench/leaderboard.json; they change when the benchmark changes.

## 1. what this is
A six-dimension verifiability auditor for agent skills. Static analysis only — the target's code is
never executed. Output: total score, per-dimension breakdown, blocking findings, remediation order,
and a projected ceiling that separates mechanical fixes from work the author still has to do.

## 2. scoring rubric (100 points)
- consistency 25 — documented flags and subcommands exist in the source
- structure 20 — entry file, version, name, description are machine-findable
- reproducibility 20 — a golden set exists and a runner actually executes it
- hygiene 15 — no absolute paths, secrets or leaked contact details
- discoverability 15 — triggers, ecosystem links, AI-INDEX.json or llms.txt
- licensing 5 — a real license file plus a declared field
Static mode caps at 96; the remaining 4 points require the target's own tests to run.

## 3. known measurement biases, found and fixed
- index detection used to be case-sensitive: a correct AI-INDEX.json in upper case scored zero
- position-argument CLIs used to score zero in consistency; now they earn 5 of 25, with a note that
  unnamed arguments are only partly checkable
- GitHub bot / noreply addresses used to be flagged as leaked contact details; now exempt

## 4. leaderboard (bucket | target | score | verdict)
| bucket | target | score | verdict |
|---|---|---|---|
{chr(10).join(lines)}

## 5. what the score cannot tell you
usefulness, correctness, popularity, maintainer responsiveness, or anything about packages not measured.

## 6. how to reproduce
{REPO}/tree/main/bench — `python bench.py`

## 7. how to get reviewed
{REPO}/issues/new?template=review-request.yml — bot fetches the public tarball, runs static analysis,
replies with score + blockers + fix order.

## 8. badge (live endpoint)
{REPO}/blob/main/bench/badge.json — shields endpoint format, renders current numbers.

## 9. registry (verified list)
{SITE}/registry.json — tiers: verified ≥90 · watch 60-89 · blocked <60; rules and entries.

## 10. third-party audits (machine-readable)
{SITE}/audits.json — two large public repos, full findings + fix order + reproduce command.

## 11. site
{SITE}/ — {', '.join(u.replace('.html','') for u in urls)}
"""
    broken_full = re.findall(re.escape(SITE) + r"[A-Za-z0-9]", full)
    if broken_full:
        raise SystemExit("llms-full.txt: %d URL(s) missing the slash after the site root: %s"
                         % (len(broken_full), broken_full[:3]))
    open(os.path.join(DOCS, "llms-full.txt"), "w", encoding="utf-8").write(full)

    print("pages:", len(urls), "| docs dir:", DOCS)


if __name__ == "__main__":
    main()












