---
name: lgd-skill-review
displayName: 技能评测官
displayNameEn: Skill Reviewer
display_name: 技能评测官
display_name_en: Skill Reviewer
slug: lgd-skill-review
author: 诺声(Logos)@SynomosAI
copyright: SynomosAI
version: 1.1.7
license: MIT
description: "Use this skill when reviewing a skill package or auditing its claims. 技能评审/扣分依据/质量门禁. Use when reviewing, auditing or scoring any AI skill package, or when a skill was rejected and you need to know why. A dual-ruler reviewer: reports a structure score (100) and a semantics score (120) as two orthogonal verdicts instead of merging them, and flags the case when the two disagree by 20 points or more. Structure asks whether the package can be used at all (tests, declared-vs-implemented consistency, reproducibility, hygiene, discovery, licensing); semantics asks whether it is worth using (knowledge delta, procedures, anti-patterns with reasons, specification, progressive disclosure, freedom calibration, pattern fit, usability). Every finding carries a stable ID and is traceable to a specific file. Accepts evidence-based appeals: the appellant supplies a path and a check, the engine opens it and rules OVERTURNED / UPHELD, and records the ruling in appeal_log.json. Appeals never silently change a score - they turn a deduction into a verifiable dispute. Zero dependency, standard library only, offline. Triggers: review my skill, audit skill quality, why is my skill rejected, skill checklist, score this skill, improve my SKILL.md, skill package gate, appeal a score."
description_zh: "技能体检 / 评测 / 打分 / 为什么被拒 / 对评分不服 —— 对任意 AI 技能包做双制评测：结构制（100 分，量能不能用）与语义制（120 分，量值不值得用）各自出结论、绝不加权成一个数，两者背离 ≥20 分时会明确标出。每条整改项带稳定 ID、可指到具体文件；支持证据驱动的申诉（给出路径与核验方式，引擎自己打开判断），裁决推翻/维持并写入 appeal_log.json，但**不会因为申诉直接改分**——申诉的作用是把扣分变成可核验的争议点，不是让人自己给自己加分。"
description_en: "A six-dimension, evidence-based reviewer for any AI skill package: scores structure, declared-vs-implemented consistency, reproducibility, hygiene, AI discoverability and licensing on a weighted 100-point scale, emits a prioritized fix list (P0 blocking / P1 improvement) and a rerun command, closing the review -> fix -> re-review loop. Every point is traceable to a file and finding."
tags:
  - 技能评测
  - 质量门禁
  - SKILL 审查
  - 整改闭环
  - lgd-skill-review
category: developer-tools
allowed-tools: Read, Glob, Grep, Bash
display_name_zh: 技能评测官
---

# lgd-skill-review · 精简版（v1.2.0-slim）

原 175 行 / 14 个 H2 / 5 份 references → 本页 58 行 / 2 模块 / 1 份 `references/details.md`。
依据 SkillsBench（arXiv 2602.12670）：聚焦型胜全面型。

## 1 用法：只决定一件事——评谁、按哪套口径

六维计分是骨架；`--token / --multi-role / --eight` 是**附加报告，不参与计分**（这点必须说清）。

```bash
python scripts/review.py ./待评技能 --json
python scripts/review.py ./待评技能 --run --token --multi-role
python scripts/review.py ./待评技能 --eight
python scripts/review.py ./待评技能 --appeal 申诉.json
```

## 2 纪律：不可妥协（逐条满足，缺一即返工）

- **MUST** 每项扣分附证据定位（文件 + 行号或断言名），无证据不扣分。
- **MUST** 区分「计分项」与「附加报告」，不得把附加报告的结论算进分数。
- **MUST** 申诉按证据裁决，裁决结果不得修改已给出的分数。
- **MUST** 先声明口径（六维 / 公开 120 分制），不得混用两套口径比较。
- **MUST** 评审者与被评者利益分离：自评不作终审依据。
- **MUST** 证据如实呈现：不编造证据、不美化结论（faithful reporting），扣分与加分都必须可追溯。
- **NEVER** 只给分数不给证据。
- **NEVER** 拿不同口径的分数做排名。
- **NEVER** 因作者身份、关系或商业利益调整评分。
- **NEVER** 把「未通过」写成「已通过」或反向表述。

示例（输出片段，证据与分数必须成对出现）：

```text
[六维] 可复跑 16/20  证据=tests/run_golden.py 存在但未在包内声明命令
[附加] token 体检：填充语 6.2%（不计分）
[申诉] 项=可复跑｜依据=tests/README 第 3 行有命令｜裁决=扣分维持（声明位置不符规范）
```

## 3 边界与降级

- 不评商业价值、不做市场预测；只评技能包质量与可验证性。
- 无 tests 目录时：该项直接判缺，不给「待补」缓冲分。
- 跨包比较必须同口径；口径不同只出并列数据，不出排名。
- 全量规范（六维定义、扣分档、申诉流程、120 分制映射）见 `references/details.md`。
- 同系列：`summarize-pro` → `debug-pro` → 本包（评审）。

零依赖 · 零联网 · 零凭据 ｜ MIT ｜ 诺声(Logos)@SynomosAI

## Hand-off

- 被评技能需要出纪要/结论 → `summarize-pro`
- 被评技能需要排查故障 → `debug-pro`
- 被评技能是内容选题类 → `wechat-viral-topic`
