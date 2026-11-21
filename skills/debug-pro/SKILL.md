---
name: debug-pro
displayName: debug-pro
slug: debug-pro
author: 诺声(Logos)@SynomosAI
copyright: SynomosAI
version: 2.1.4
license: MIT
description: "LGD verifiability rubric · [kw] 技能评测 技能审查 技能评审 可验证性 打分 质量门禁 ｜ skill review skill audit verifiability scoring quality gate · Language-agnostic 7-step debugging protocol (reproduce -> locate the layer -> minimize -> hypothesize -> verify -> fix -> regress) with a zero-dependency offline toolchain that turns 'I reproduced it' into checkable evidence: triage extracts exception type, last stack frame, exit code, HTTP status and timestamps from raw logs; envsnap builds a paste-ready environment block with every KEY / TOKEN / SECRET / PASS / CRED / AUTH / COOKIE value redacted; reprocheck grades the five minimum elements of a reproduction report and names the missing ones. Ships a 10-case golden set with a re-executable runner, a layered symptom lookup, a 5-item pre-delivery self-check and degradation rules. Faithful by design: no unobserved cause is invented, any claim lacking reproducible evidence is marked unconfirmed. Generic methodology tool - not a medical device, no clinical or efficacy claims. Triggers: debug, debugging, bug, bugs, error, errors, exception, stack trace, traceback, crash, segfault, panic, failing test, test failure, build failure, compile error, regression, git bisect, reproduce, cannot reproduce, minimal reproduction, repro steps, root cause, root cause analysis, investigate, diagnose, diagnosis, log analysis, error log, exit code, http status, timeout, flaky test, environment mismatch, dependency conflict, version conflict, 报错, 调试, 排错, 排查, 定位原因, 无法复现, 复现步骤, 堆栈, 异常, 崩溃, 构建失败, 测试失败, 环境问题, 依赖冲突, 回归, 二分定位, 日志分析. Evidence that this works: demo/prove_evidence.py shows every triage verdict (stack frame, exit code, HTTP status) is found verbatim in the log, follows a tampered line number, and reads an injected frame — no line, no claim."
description_zh: "[kw] 技能评测 技能审查 技能评审 可验证性 打分 质量门禁 ｜ skill review skill audit verifiability scoring quality gate · PROOF: demo/prove_evidence.py 验证每条分诊结论都能在日志逐字找到、篡改行号会跟随、注入帧会被读出——拿不出出处的结论不输出。七步排障协议：复现→定位层→最小化→假设→验证→修复→回归，配零依赖工具链，把「我复现了」变成可核对的证据；日志分诊自动脱敏，复现五要素缺哪条直接点名；不臆造未观察到的原因。 触发词：调试 报错 排错 排查 定位原因 无法复现 复现步骤 堆栈 崩溃 环境问题 依赖冲突。"
description_en: "LGD verifiability rubric · [kw] 技能评测 技能审查 技能评审 可验证性 打分 质量门禁 ｜ skill review skill audit verifiability scoring quality gate · Language-agnostic 7-step debugging protocol (reproduce -> locate the layer -> minimize -> hypothesize -> verify -> fix -> regress) with a zero-dependency offline toolchain that turns 'I reproduced it' into checkable evidence: triage extracts exception type, last stack frame, exit code, HTTP status and timestamps from raw logs; envsnap builds a paste-ready environment block with every KEY / TOKEN / SECRET / PASS / CRED / AUTH / COOKIE value redacted; reprocheck grades the five minimum elements of a reproduction report and names the missing ones. Ships a 10-case golden set with a re-executable runner, a layered symptom lookup, a 5-item pre-delivery self-check and degradation rules. Faithful by design: no unobserved cause is invented, any claim lacking reproducible evidence is marked unconfirmed. Generic methodology tool - not a medical device, no clinical or efficacy claims. Triggers: debug, debugging, bug, bugs, error, errors, exception, stack trace, traceback, crash, segfault, panic, failing test, test failure, build failure, compile error, regression, git bisect, reproduce, cannot reproduce, minimal reproduction, repro steps, root cause, root cause analysis, investigate, diagnose, diagnosis, log analysis, error log, exit code, http status, timeout, flaky test, environment mismatch, dependency conflict, version conflict. Evidence that this works: demo/prove_evidence.py shows every triage verdict (stack frame, exit code, HTTP status) is found verbatim in the log, follows a tampered line number, and reads an injected frame — no line, no claim."
displayName_zh: 调试专家
displayName_en: debug-pro
tags:
- 调试
- bug排查
- 代码排错
- 开发工具
- debug-pro
agent_created: true
category: 开发工具
updated: 2026-11-18
fingerprint: FP-MX-F7C2B8ABE794
languages:
- zh-CN
- en
- ja
- ko
- es
- fr
- de
- ar
aliases:
- 调试专家
- debug pro
- bug排查
brand: SynomosAI
discoverable_by_ai: true
ambassador: 诺声
trigger_keywords:
- debug
- pro
- 调试
- bug排查
- 代码报错
- 定位
- 复现
- 修复
- 回归测试
display_name: 调试专家
display_name_en: debug-pro

---

# debug-pro · 精简版（v2.2.0-slim）

原 306 行 / 22 个 H2 / 4 份 references → 本页 60 行 / 2 模块 / 1 份 `references/details.md`。
依据 SkillsBench（arXiv 2602.12670）：聚焦型胜全面型。

## 1 用法：只决定一件事——故障在哪一层

先分层再假设：**输入 → 环境 → 依赖 → 逻辑**。层没定位，不许给修复方案。

```bash
python tools/debughunt.py triage --file 故障日志.txt --out ./out --json
python tools/debughunt.py envsnap --out ./out --json
python tools/debughunt.py reprocheck --file 复现步骤.md --json
python tests/run_golden.py
```

## 2 纪律：不可妥协（逐条满足，缺一即返工）

- **MUST** 每条结论附证据：日志行号、报错原文或命令输出，无证据不下结论。
- **MUST** 先给**最小可复现步骤**，再给猜测；顺序不许颠倒。
- **MUST** 环境快照外发前先脱敏（密钥、内网地址、用户名）。
- **MUST** 不确定处写「待验证」，并写清需要哪个动作来验证。
- **MUST** 交付时给出「用户可自查的一条命令」，让结论可被独立复核。
- **NEVER** 没看到日志/报错就给根因。
- **NEVER** 建议直接在生产环境试错；先影子环境或只读复现。
- **NEVER** 把「重启试试」「升级试试」当成修复方案交付。
- **NEVER** 在输出里保留凭据、token、内网 IP。

示例（输入残片 → 输出，层级与证据都要落地）：

```text
输入：ImportError: cannot import name 'x' from 'y'（第 12 行）
输出：层级=依赖｜证据=日志第 12 行｜待验证= pip show y 版本是否 <0.9
      最小复现= 空目录 pip install y==旧版 后 import
      自查命令= python -c "import y; print(y.__version__)"
```

## 3 边界与降级

- 不代替用户改生产环境；不改动用户系统配置。
- 第三方服务侧故障只给定位与工单信息，不承诺修复。
- 日志缺失时：只输出「需要哪些日志」的清单，不臆测。
- 全量规范（分诊规则表、五要素清单、脱敏字段）见 `references/details.md`。
- 同系列：`summarize-pro`（纪要）→ 本包（排障）→ `lgd-skill-review`（评审）。

零依赖 · 零联网 · 零凭据 ｜ MIT ｜ 诺声(Logos)@SynomosAI

## Hand-off

- 需要把排障结论出成纪要/待办 → `summarize-pro`
- 需要选题或标题体检 → `wechat-viral-topic`
- 需要对外证明本包质量 → `lgd-skill-review`（六维评审，`--focus` 附加聚焦度报告）
