# debug-pro · 排障专家

<!-- LGD-ECOSYSTEM -->
[![verifiability](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fzhaoxinghua09-cell%2Flgd-skill-review%2Fmain%2Fbench%2Fbadge.json)](https://zhaoxinghua09-cell.github.io/lgd-skill-review/benchmark.html)

**同系列 / Ecosystem** — 本包属于同一套可验证技能，共用一把尺子：
[`summarize-pro`](https://github.com/zhaoxinghua09-cell/summarize-pro) ｜ [`wechat-viral-topic`](https://github.com/zhaoxinghua09-cell/wechat-viral-topic) ｜ [`lgd-skill-review`](https://github.com/zhaoxinghua09-cell/lgd-skill-review)

- 评分口径与公开基准：https://zhaoxinghua09-cell.github.io/lgd-skill-review/rubric.html ｜ 榜单：https://zhaoxinghua09-cell.github.io/lgd-skill-review/benchmark.html
- 把自己的技能丢进来比，不用联系我们：[提交评测](https://github.com/zhaoxinghua09-cell/lgd-skill-review/issues/new?template=review-request.yml)
- 机器入口：`https://zhaoxinghua09-cell.github.io/lgd-skill-review/llms.txt` （全量语料：`llms-full.txt`）
<!-- /LGD-ECOSYSTEM -->

<!-- LGD-DIFF -->
**Every triage verdict points at a line in your log — no guessed root cause.**

分诊结论（异常类型 / 栈首帧 / 退出码）逐项标注日志出处，可逐条回原文核对；拿不出出处的结论不输出。
复现：`python demo/run_demo.py`，见 `demo/SAMPLE-IO.md` 的实际输出。
<!-- /LGD-DIFF -->


**想知道自己的技能多少分？/ Get your own skill scored:** [一键提交评测 / submit for review](https://github.com/zhaoxinghua09-cell/lgd-skill-review/issues/new?template=review-request.yml) — 静态分析、不执行你的代码。

**skills.sh 页面**: https://skills.sh/zhaoxinghua09-cell/debug-pro ｜ `npx skills add zhaoxinghua09-cell/debug-pro`


先定位再动手的排障流程：先把故障钉在某一层（输入/环境/依赖/逻辑），再最小化、验证、回归。没有日志与复现步骤就不给根因。

Triage-first debugging: locate the failing layer (input / environment / dependency / logic) before proposing any fix, then minimize, verify and regress.

## 一步安装 / Install in one line

```bash
# LobeHub 市场 / LobeHub marketplace
npx -y @lobehub/market-cli skills install zhaoxinghua09-cell-debug-pro --agent codex

# 直接从 GitHub 源安装 / install from source
npx -y skills add zhaoxinghua09-cell/debug-pro --skill debug-pro --agent codex
```

[![verify](https://github.com/zhaoxinghua09-cell/debug-pro/actions/workflows/verify.yml/badge.svg)](https://github.com/zhaoxinghua09-cell/debug-pro/actions/workflows/verify.yml)

- 市场页 / Marketplace page: https://lobehub.com/skills/zhaoxinghua09-cell-debug-pro
- 标识符 / Identifier: `zhaoxinghua09-cell-debug-pro`
- 自检 / Verify: `python tests/run_golden.py`（零依赖、离线，退出码即结论）
- 审计报告 / Audit: [`AUDIT-REPORT.md`](AUDIT-REPORT.md)（命令生成，重跑可推翻）

### 同族技能 / Same family

- [`summarize-pro`](https://github.com/zhaoxinghua09-cell/summarize-pro)
- [`wechat-viral-topic`](https://github.com/zhaoxinghua09-cell/wechat-viral-topic)
- [`lgd-skill-review`](https://github.com/zhaoxinghua09-cell/lgd-skill-review)
- [`lgd-hit-list`](https://github.com/zhaoxinghua09-cell/lgd-hit-list) — 爆款清单登记 / hit-list registry

## 快速开始 / Quick start

```bash
git clone https://github.com/zhaoxinghua09-cell/debug-pro.git
cd debug-pro
python tools/debughunt.py triage --file error.log --out ./out --json
python tools/debughunt.py envsnap --out ./out --json
python tools/debughunt.py reprocheck --file repro.md --json
python tests/run_golden.py
```

## 为什么可信 / Why it is checkable

- 黄金集 10 cases，`python tests/run_golden.py` 会真实执行并给出退出码（不靠自述）。
- 差异化点：single checkable command handed to the user for every claim。
- 零依赖、离线、零凭据：仅标准库，不发网络请求。

## AI 发现层 / AI discovery layer

- `llms.txt` — 面向 AI Agent 的能力与触发条件说明（双语）。
- `AI-INDEX.json` — 机器可读索引（schema `lgd.ai-index/1`）。
- 六维审计通过后登记于爆款清单：https://github.com/zhaoxinghua09-cell/lgd-hit-list

## 同族技能 / Family

- [summarize-pro](https://github.com/zhaoxinghua09-cell/summarize-pro) — 会议纪要专家
- [wechat-viral-topic](https://github.com/zhaoxinghua09-cell/wechat-viral-topic) — 公众号选题专家
- [lgd-skill-review](https://github.com/zhaoxinghua09-cell/lgd-skill-review) — 技能审计官

---

