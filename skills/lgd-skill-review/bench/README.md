# LGD SkillBench v0.1

**A reproducible verifiability benchmark for public agent skills.**
公开 Agent 技能的「可验证性」基准，可复算、可反驳。

> 我们不测谁更有用，我们测**别人能不能独立验证你**。

## What this is / 这是什么

同一台引擎（`scripts/review.py`，六维、零依赖、离线）、同一口径（静态模式，不执行目标仓库任何代码）、同一时点，对公开热门技能仓库打分。所有分数由 `bench/bench.py` 一条命令重现。

```bash
# 本机复现 / reproduce locally
python bench/bench.py
```

脚本只做三件事：下载公开 tarball → 定位 `SKILL.md` → 静态评审。不执行对方代码，不使用任何凭据。

## Results / 结果（2026-11-19，静态模式，上限 96）

| Target | Score / 100 | Verdict | Skill dir scored |
|---|---|---|---|
| vercel-labs/agent-skills @ `skills/react-best-practices` | 24 | FAIL | `skills/react-best-practices` |
| mattpocock/skills @ `skills/engineering/code-review` | 18 | FAIL | `skills/engineering/code-review` |
| microsoft/azure-skills @ `skills/azure-deploy` | 20 | FAIL | `.github/plugins/azure-skills/skills/azure-deploy` |
| prisma/skills @ `prisma-cli` | 20 | FAIL | `prisma-cli` |
| leonxlnx/taste-skill @ `skills/taste-skill` | 10 | **BLOCK** | `skills/taste-skill`（`secret_leak: assets/photos/photos.json`） |
| juliusbrussee/caveman @ `skills/caveman` | 18 | FAIL | `plugins/caveman/skills/caveman` |
| google/agents-cli @ `skills/google-agents-cli-adk-code` | 22 | FAIL | `skills/google-agents-cli-adk-code` |
| anthropics/skills @ `skills/pdf` | 21 | FAIL | `skills/pdf` |
| anthropics/skills @ `skills/pptx` | 36 | FAIL | `skills/pptx` |
| anthropics/skills @ `skills/docx` | 36 | FAIL | `skills/docx` |
| **LGD summarize-pro** | **96** | PASS | — |
| **LGD debug-pro** | **96** | PASS | — |
| **LGD wechat-viral-topic** | **96** | PASS | — |
| **LGD lgd-skill-review** | **96** | PASS | — |

全部目标已改为**显式指定旗舰技能路径**（不再依赖启发式自动选取）。对照上一版自动选取的结果：第三方区间仍是 10–24，分数几乎不变——说明结论对「选哪个目录」不敏感。

我方四包在 `--run` 模式下为 100/100；静态入口封顶 96（满分要求真跑测试，而入口不执行他人代码）。

## What the score means / 分数代表什么

六维：结构、一致性、可复跑、卫生、可发现性、许可。它回答的问题是「第三方能不能独立验证这个技能」，**不回答**「这个技能好不好用」「作者水平如何」。

因此：

- `pdf` 得 21 分**不代表 pdf 技能差**（它安装量约 182k）。它只是**没有提供让人独立验证的手段**：没有 tests、没有声明命令、没有机器可读索引。
- 我方 96 分**不代表**我们的文笔或实用性胜过 Anthropic。我们只是把「可验证」做进了产品里。

一个把这两件事混为一谈的人，会得出错误结论。本文档的存在就是为了防止这种误读。

## Limitations / 局限（必须一起读）

1. **目录选取已改为显式指定**：表中每个目标都标注了被评的 `@path`（旗舰技能目录），不再依赖启发式自动选取。仍可能漏掉作者心里真正的「主技能」——欢迎指出，指出即改。
2. **静态模式**：不跑测试，`可复跑` 维度按「是否存在可离线复跑的证据」静态判定，满分需 `--run`。
3. **单时点**：2026-11-19 一次快照，仓库改动后分数会变；重跑即更新。
4. **口径不可跨表比较**：本表是 100 分制静态口径；语义分（120 分制）未在此列出，不得与本表混排。
5. **样本非随机**：取的是 skills.sh 搜索返回的高安装量仓库，不构成市场总体分布。

## Why we publish it / 为什么公开

因为「我们更强」这句话没有信息量。**能被别人当场重跑的分**才有信息量。

欢迎任何人：重跑脚本推翻我们的数字、指出目录选取错误、或提交自己的仓库拿一份带整改清单的评分。

- 提评测 / submit for review: `https://github.com/zhaoxinghua09-cell/lgd-skill-review/issues/new?template=review-request.yml`
- 申诉 / appeal: 给出路径 + 检验方法，我们复核后裁定 `OVERTURNED` / `UPHELD`

## Reproduce / 复现

```bash
git clone https://github.com/zhaoxinghua09-cell/lgd-skill-review
cd lgd-skill-review
python bench/bench.py          # 只跑第三方
LGD_BENCH_OWN_DIR=/path/to/pkgs python bench/bench.py   # 连我方一起跑
```

输出 `bench/bench.json`，含每个目标的分数、结论、被评目录、阻断项与六维明细。

MIT · 诺声(Logos)@SynomosAI
