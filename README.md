# lgd-skills

Four agent skills that prefer evidence over adjectives: they refuse to invent numbers, owners or decisions, ship a runnable test set, and run offline with zero third-party dependencies, zero network calls and zero credentials.

## Install

```bash
npx skills add <owner>/lgd-skills --skill summarize-pro
npx skills add <owner>/lgd-skills --skill debug-pro
npx skills add <owner>/lgd-skills --skill wechat-viral-topic
npx skills add <owner>/lgd-skills --skill lgd-skill-review
```

## What's inside

| Skill | One line | Proof you can re-run |
|---|---|---|
| **summarize-pro** | Transcript → minutes / decisions / action items / timeline, with every figure traced back to the source | 24-case golden set, `extract --receipt` writes a SHA-256 receipt |
| **debug-pro** | Triage-first debugging: classify into input / environment / dependency / logic before proposing a fix | 10-case golden set, env snapshot redacts secrets |
| **wechat-viral-topic** | Topic selection that separates a real signal from a clickbait guess; compliance red lines before writing | 11-case golden set, title overreach check |
| **lgd-skill-review** | Six-dimension reviewer for skill packages; evidence required for every deduction, appeals ruled on evidence | 5-case golden set, `--focus` attached report |

## Why this exists

Most skill listings ask you to trust a paragraph. These four let you check instead:

- **Traceable numbers** — `citecheck` maps each output sentence back to source tokens and lists anything untraceable.
- **Verifiable artefacts** — `extract --receipt` writes a receipt binding input and output by SHA-256; change one digit and verification fails, naming the broken assertion.
- **Zero-dependency, offline** — standard library only. No API keys, no network calls. After the 2026 skill-marketplace malware incidents, "it cannot phone home" is a feature.
- **Focused documentation** — 2 modules per skill, ≤120 lines of body text. Our own reviewer scores these 100/100 with tests actually executed (`--run`).

## Verify locally

```bash
cd skills/summarize-pro && python tests/run_golden.py      # 24/24
cd skills/debug-pro && python tests/run_golden.py          # 10/10
cd skills/wechat-viral-topic && python tests/run_golden.py  # 11/11
cd skills/lgd-skill-review && python tests/run_golden.py    # 5/5
```

## Language

Chinese-first content, English-first packaging. Each skill ships `description` in both languages and handles zh-CN input natively.

## Honest limits

- These are specialised workflow skills, not general-purpose document converters.
- The golden sets are ours, small, and deterministic — they prove regression safety, not industry-wide benchmark performance.
- Install counts on any marketplace reflect who ran the install command, not quality.

## License

MIT. Author: 诺声(Logos)@SynomosAI.

---

# 中文说明

四个 Agent 技能，共同点是：**不编数字、不编责任人、不编结论**，自带可复跑用例，纯标准库、不联网、不要凭据。

- **summarize-pro**：转写 → 纪要 / 结论 / 待办 / 时间线，每个数字可回原文；`extract --receipt` 生成 SHA-256 回执，改一个数字复核即失败并指名断言。
- **debug-pro**：先分层再假设（输入/环境/依赖/逻辑），每条结论必须有日志行号证据。
- **wechat-viral-topic**：先扫信号、再过合规红线、最后体检标题，不承诺效果、不蹭灾难热点。
- **lgd-skill-review**：六维评审，每项扣分附证据；`--focus` 附加聚焦度报告，不参与计分。

自检：`python tests/run_golden.py`，退出码即结论。
