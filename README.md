# LGD Skills · 四个可验证的 Agent 技能

[![verifiability](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fzhaoxinghua09-cell%2Flgd-skill-review%2Fmain%2Fbench%2Fbadge.json)](https://github.com/zhaoxinghua09-cell/lgd-skill-review/tree/main/bench)

一个仓库装四个技能，每个都通过同一把尺子验收：**六维可验证性审计，静态 96 分，带测试实跑 100 分**。

```bash
npx skills add zhaoxinghua09-cell/lgd-skills
```

---

## 里面有什么 / What's inside

| 技能 | 一句话 | 什么时候用它 |
|---|---|---|
| [`summarize-pro`](skills/summarize-pro) | 会议纪要、录音转写、长文摘要 | 给我总结一下这场会 / 把这段录音转成纪要 / 把这篇长文压成要点 / meeting minutes, transcript, action items |
| [`debug-pro`](skills/debug-pro) | 报错定位、日志分析、最小复现 | 这个报错怎么修 / 帮我看看 stack trace / 为什么跑不通 / debug this error, stack trace, crash |
| [`wechat-viral-topic`](skills/wechat-viral-topic) | 公众号选题与爆款结构 | 帮我找个公众号选题 / 这篇标题怎么改 / WeChat article topic, viral headline |
| [`lgd-skill-review`](skills/lgd-skill-review) | 技能六维审计与一键整改 | 帮我评测这个技能 / 这个 SKILL.md 缺什么 / skill audit, skill review, rate my skill |

---

## 为什么值得装

**1. 分数可复算，扣分可定位。**
同一包重复评测得同一总分；每条扣分都钉在具体文件上，可以申诉。不是"我觉得挺好"，是"证据在 `references/x.md` 第 12 行"。

**2. 整改有工具，不是只给结论。**
```bash
python skills/lgd-skill-review/scripts/quickfix.py <你的技能目录>          # 只打印计划
python skills/lgd-skill-review/scripts/quickfix.py <你的技能目录> --apply  # 写入
```
补许可、生成 `AI-INDEX.json`、按源码真实参数追加 `## Commands`、清本机绝对路径——全部默认可回退、单文件改动超 30% 直接拒写。

**3. 可以把自己的仓库丢进来比。**
```bash
cd skills/lgd-skill-review/bench && python bench.py
```
公开基准每天自动刷新，结果在 [`bench/leaderboard.json`](skills/lgd-skill-review/bench/leaderboard.json)。

---

## 怎么被评测

开一个 Issue 即可，无需联系作者：
[`review-request.yml`](https://github.com/zhaoxinghua09-cell/lgd-skill-review/issues/new?template=review-request.yml)

机器人会抓公开 tarball → 静态分析（**不执行你的代码**）→ 回帖分数、六维明细、阻断项、整改顺序。

---

## 边界（写在前面）

- 量的是**可验证性**，不是内容好坏，不是流行度
- 低分不代表技能没用，只说明缺验证手段
- 静态 100 分制口径，100 需要目标自带的测试真的跑通
- 样本非随机，是公开热门仓库的一个截面

---

## 链接

- 审计引擎与基准：[`zhaoxinghua09-cell/lgd-skill-review`](https://github.com/zhaoxinghua09-cell/lgd-skill-review)
- 评测入口：[`issues/new?template=review-request.yml`](https://github.com/zhaoxinghua09-cell/lgd-skill-review/issues/new?template=review-request.yml)
- 市场页：[skills.sh](https://skills.sh/zhaoxinghua09-cell) ｜ [LobeHub](https://lobehub.com/skills/zhaoxinghua09-cell-summarize-pro)
