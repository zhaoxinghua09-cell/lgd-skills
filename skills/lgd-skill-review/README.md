# lgd-skill-review · 技能审计官

<!-- LGD-ECOSYSTEM -->
[![verifiability](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fzhaoxinghua09-cell%2Flgd-skill-review%2Fmain%2Fbench%2Fbadge.json)](https://zhaoxinghua09-cell.github.io/lgd-skill-review/benchmark.html)

**同系列 / Ecosystem** — 本包属于同一套可验证技能，共用一把尺子：
[`summarize-pro`](https://github.com/zhaoxinghua09-cell/summarize-pro) ｜ [`debug-pro`](https://github.com/zhaoxinghua09-cell/debug-pro) ｜ [`wechat-viral-topic`](https://github.com/zhaoxinghua09-cell/wechat-viral-topic)

- 评分口径与公开基准：https://zhaoxinghua09-cell.github.io/lgd-skill-review/rubric.html ｜ 榜单：https://zhaoxinghua09-cell.github.io/lgd-skill-review/benchmark.html
- 把自己的技能丢进来比，不用联系我们：[提交评测](https://github.com/zhaoxinghua09-cell/lgd-skill-review/issues/new?template=review-request.yml)
- 机器入口：`https://zhaoxinghua09-cell.github.io/lgd-skill-review/llms.txt` （全量语料：`llms-full.txt`）
<!-- /LGD-ECOSYSTEM -->

[![verifiability](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fzhaoxinghua09-cell%2Flgd-skill-review%2Fmain%2Fbench%2Fbadge.json)](https://github.com/zhaoxinghua09-cell/lgd-skill-review/tree/main/bench)

<!-- LGD-DIFF -->
**Scores are reproducible and appealable — same package, same score, every deduction pinned to a file.**

评分可复算：同一包重复评测得同一总分；每条扣分定位到具体文件，并支持基于证据的申诉。
复现：`python demo/run_demo.py`（含坏包/好包对照与申诉流程）。
<!-- /LGD-DIFF -->

**skills.sh 页面**: https://skills.sh/zhaoxinghua09-cell/lgd-skill-review ｜ `npx skills add zhaoxinghua09-cell/lgd-skill-review`


Agent 技能六维审计器：每一处扣分都必须给出证据，输出分数、阻断项与整改顺序，作者或 AI 可据此整改、复评、再提高。这是我们做「权威评测」的引擎。

A six-dimension auditor for agent skills: every deduction must cite evidence, and every package gets a score, a blocker list and a remediation order — so an author (or an agent) can fix, re-run and raise the score.

## 自助评测 / Get reviewed without talking to us

Open one issue — a GitHub Action reviews your repo and posts the verdict as a comment. Static analysis only: nothing from your repository is executed.

开一个 Issue 即可：GitHub Action 抓取你的公开仓库、跑六维评审，把结论直接评论在 Issue 里。只做静态分析，不执行你仓库里的任何代码。

- 提交入口 / Submit: [Review request form](https://github.com/zhaoxinghua09-cell/lgd-skill-review/issues/new?template=review-request.yml)
- 你会拿到 / You get: 结构分 `0-100` + 语义分 `0-120` + 每条扣分定位到文件 + 编号整改清单
- 整改后再评 / Re-review: 在同一个 Issue 里重开或补一条评论，分数变化即因果证据
- 申诉 / Appeal: 带证据申诉（给出路径与检验方法），我们复核后裁定 `OVERTURNED` / `UPHELD`，不改分不静默

```bash
# 你也可以在本地先自评，再决定要不要提交
python scripts/review.py <你的技能目录> --json
```

## 一步安装 / Install in one line

```bash
# LobeHub 市场 / LobeHub marketplace
npx -y @lobehub/market-cli skills install zhaoxinghua09-cell-lgd-skill-review --agent codex

# 直接从 GitHub 源安装 / install from source
npx -y skills add zhaoxinghua09-cell/lgd-skill-review --skill lgd-skill-review --agent codex
```

[![verify](https://github.com/zhaoxinghua09-cell/lgd-skill-review/actions/workflows/verify.yml/badge.svg)](https://github.com/zhaoxinghua09-cell/lgd-skill-review/actions/workflows/verify.yml)

- 市场页 / Marketplace page: https://lobehub.com/skills/zhaoxinghua09-cell-lgd-skill-review
- 标识符 / Identifier: `zhaoxinghua09-cell-lgd-skill-review`
- 自检 / Verify: `python tests/run_golden.py`（零依赖、离线，退出码即结论）
- 审计报告 / Audit: [`AUDIT-REPORT.md`](AUDIT-REPORT.md)（命令生成，重跑可推翻）

### 同族技能 / Same family

- [`summarize-pro`](https://github.com/zhaoxinghua09-cell/summarize-pro)
- [`debug-pro`](https://github.com/zhaoxinghua09-cell/debug-pro)
- [`wechat-viral-topic`](https://github.com/zhaoxinghua09-cell/wechat-viral-topic)
- [`lgd-hit-list`](https://github.com/zhaoxinghua09-cell/lgd-hit-list) — 爆款清单登记 / hit-list registry

## 快速开始 / Quick start

```bash
git clone https://github.com/zhaoxinghua09-cell/lgd-skill-review.git
cd lgd-skill-review
python scripts/review.py <package-dir> --run
python scripts/review.py <package-dir> --run --focus declared-consistency
python tests/run_golden.py
```

## 为什么可信 / Why it is checkable

- 黄金集 5 cases，`python tests/run_golden.py` 会真实执行并给出退出码（不靠自述）。
- 差异化点：declared-CLI vs implemented-CLI consistency。
- 零依赖、离线、零凭据：仅标准库，不发网络请求。

## AI 发现层 / AI discovery layer

- `llms.txt` — 面向 AI Agent 的能力与触发条件说明（双语）。
- `AI-INDEX.json` — 机器可读索引（schema `lgd.ai-index/1`）。
- 六维审计通过后登记于爆款清单：https://github.com/zhaoxinghua09-cell/lgd-hit-list

## 同族技能 / Family

- [summarize-pro](https://github.com/zhaoxinghua09-cell/summarize-pro) — 会议纪要专家
- [debug-pro](https://github.com/zhaoxinghua09-cell/debug-pro) — 排障专家
- [wechat-viral-topic](https://github.com/zhaoxinghua09-cell/wechat-viral-topic) — 公众号选题专家

---

