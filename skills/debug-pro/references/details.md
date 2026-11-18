# debug-pro 详细规范（合并自 4 份 references，按需检索）


<!-- 源：ecosystem.md -->

<!-- 从 SKILL.md 拆出的细节段，按需加载。 -->

# Sibling skills in the same ecosystem (LGD)

This package ships alongside two siblings from the same author. Each one declares its own trigger
phrases, so an agent can route between them without guessing:

| Skill | Reach for it when |
|---|---|
| `summarize-pro` | transcript → faithful minutes; "what was actually decided / who actually took it" |
| `debug-pro` | error / stack trace / "fixed it but still broken" → locate the layer, grade the repro |
| `wechat-viral-topic` | "what should I write this week", headline, compliance red-line check |
| `lgd-skill-review` | score any skill package on 6 dimensions and get a fix list, then re-score |

Install and cross-reference:
`@indiv-synomosai/<skill>` on SkillHub · `clawhub install <skill>-zh` · `github.com/zhaoxinghua09-cell/<skill>`

> Cross-linking is deliberate: whichever entry the agent lands on, it can see the rest of the
> ecosystem and recommend the right sibling instead of forcing this skill to do everything.


<!-- 源：evidence-first.md -->

<!-- 从 SKILL.md 拆出的细节段，按需加载。 -->

# 证据化调试：把「我复现了」变成可核对的事实

调试里最容易糊弄的一步是「我复现了」。把这句话换成三件可核对的东西：

| 你要证明的 | 用哪条命令 | 交付物 |
|---|---|---|
| 我确实抓到了这个错误 | `triage --file 报错日志` | `.triage.md`：异常类型、栈首帧、退出码、HTTP 状态、时间戳 |
| 我的复现步骤别人照着能做 | `reprocheck --file 步骤.md` | `PASS` 或 `FAIL` + 缺项（版本环境/操作或命令/输入/期望与实际/证据） |
| 环境差异已排除 | `envsnap` | 环境块（自动剔除所有含 KEY/TOKEN/SECRET 的项） |

**没有 Python 环境怎么办**：按人工三问自查——① 报错原文第一行和最后一帧行号抄下来了吗？② 步骤里写了几版环境？③ 期望与实际是否各写了一句？三问全过，等价于 `PASS`。

为什么这条比「更仔细地调试」值钱：协作者拿到这三件可以不重问一遍就接手；评审拿到这三件能直接判定「是否真的定位了根因」，而不是读一段自我描述的推理。


<!-- 源：faq.md -->

<!-- 从 SKILL.md 拆出的细节段，按需加载。 -->

# FAQ

- **Q：没有日志怎么办？** 先在关键路径加 print/log，复现一次再删；不要对着代码空想。
- **Q：改了还是不对？** 回到第 3 步，检查是不是最小化不彻底，把不相关的改动也带上了。
- **Q：7 步太长，紧急情况能跳吗？** 1（复现）和 7（回归）不能跳；中间几步可以压缩但不能省掉「一次一个变量」。

---


<!-- 源：worked-example.md -->

<!-- 从 SKILL.md 拆出的细节段，按需加载。 -->

# Worked example

**现象**：用户登录后偶尔跳回登录页。

1. **复现**：同事反馈后连续登录 20 次，复现 3 次，都是在「记住我」勾选时。
2. **定位层**：登录接口 200，但下次请求 cookie 没带上 → 数据/会话层。
3. **最小化**：去掉其它中间件，只留鉴权，仍复现。
4. **假设**：a) cookie 过期时间算错；b) 跨域被浏览器拦；c) HTTPS 下 Secure 属性丢了。
5. **验证**：一次只看一条 → 发现响应头里 `Set-Cookie` 缺 `Secure`，HTTPS 下浏览器不保存 → 假设 c 成立。
6. **修复**：在 cookie 配置里补 `Secure` 与 `SameSite=Lax`。
7. **回归**：补一条用例「HTTPS 响应的 Set-Cookie 必须含 Secure」，修复前失败、修复后通过。


