---
name: outbound-mail-gate
display_name: 外发短催门禁
display_name_en: outbound-mail-gate
slug: outbound-mail-gate
author: Xinghua Zhao
copyright: Xinghua Zhao
version: 1.0.0
license: MIT
category: productivity
description: "Use this skill before sending any follow-up, reminder or nudge email. 发信前自查/短催/追问/别把已回的人再催一次. Reads the thread the mailbox actually has and checks what the draft claims about it: relative wording such as 'this morning' when the message went out yesterday, 'did it arrive?' asked of somebody who already replied, a second contact inside 24 hours, a stated clock time that appears nowhere in the thread, or a standing claim such as state-of-the-art. Ships a zero-dependency rule engine, a CLI that exits 2 on a blocked draft so a send step can refuse, a 10-case golden set with a runner anyone can re-run, and a demo built from a real incident on 2026-11-20 in which a follow-up asked 'did it arrive?' of a correspondent whose reply had already been answered. The gate does not decide whether a message should be sent at all and cannot see tone; it only refuses claims the thread contradicts. Triggers: follow-up email, reminder email, nudge, did it arrive, chasing a reply, send before checking, mail gate."
description_zh: "发任何追问/短催/提醒邮件之前，先拿真实邮件线索核对草稿里的事实断言：把 11-19 的信说成「今早」、对已经回过的人再问「收到了吗」、24 小时内二次打扰、正文里的时刻在线索里根本不存在、以及「断崖式领先」这类站位断言，都会被拦下。零依赖规则引擎 + 退出码 2 的命令行（可直接挡在发送步骤前）+ 10 条黄金集（含反向自检：删掉一条规则必须让用例变红，证明套件不是摆设）+ 一条来自 2026-11-20 真实事故的演示。它不判断这封信该不该发，也看不见语气。"
description_en: "A pre-send gate for follow-up and reminder email. It compares a draft's claims against the thread as the mailbox records it and blocks: relative time wording ('this morning' for a message sent yesterday), 'did it arrive?' asked of someone who already replied, a second contact inside 24 hours, a clock time that appears nowhere in the thread, and standing claims. Its only criterion is faithfulness to the recorded thread: a sentence with no landing point in the sent or inbound messages cannot pass. Zero dependency, offline, a 10-case golden set with a negative self-test, and a demo from a real 2026-11-20 incident."
tags:
  - 邮件
  - 外发门禁
  - 沟通纪律
  - 可验证
  - outbound-mail-gate
discoverable_by_ai: true
languages:
  - en
  - zh-CN
updated: 2026-11-21
---

# outbound-mail-gate · 六条规则，一个退出码

## 1 它解决的问题

一封「追问」写错的代价不是被忽略，是**让对方看出来你没读他的回信**。2026-11-20 真实发生过：一封跟进邮件对已经回过完整结果的合作者问 "Did it arrive?"，并把前一天 08:20 的信写成 "this morning"。两处硬错都在正文里，发送环节一点都拦不住——因为没有任何东西拿正文去比邮箱。

这个包把那一步变成机械检查：**正文的每一句事实断言，都要能在线索里找到落点**。

## 2 用法

```bash
# 判一封草稿（exit 0 = 可发，exit 2 = 有一处与线索冲突，发送步骤应停）
python scripts/gate.py check --thread thread.json --draft draft.json
python scripts/gate.py check --thread thread.json --draft draft.json --json
python scripts/gate.py explain

# 10 条黄金集（含两条对照：诚实的正文必须放行）
python tests/run_golden.py
# 反向自检：删掉 R1 必须让 c02 变红，否则说明套件不会失败
python tests/run_golden.py --selftest

# 演示：同一线索、两封草稿（发出去的那封 / 改好的那封）
python demo/run_demo.py
```

线索与草稿都是纯 JSON，`now` 显式给出，所以同一份输入在任何机器上得到同一个裁决。

```json
{"sent":    [{"ts": "2026-11-19T08:20:52+08:00", "subject": "..."}],
 "inbound": [{"ts": "2026-11-19T10:49:21+08:00", "subject": "..."}]}
```

```json
{"now": "2026-11-20T09:20:57+08:00", "subject": "...", "body": "..."}
```

## 3 发前四步（按顺序做，不要跳）

第一步 取线索：只读导出该地址的 `SENT` / `INBOX` 头部（`Date`、`Subject`），写成 `thread.json`，时间戳带偏移。

第二步 写草稿：正文里的每一处时间、旧信指代、时刻，都先想清楚它在线索里的落点；`now` 用当前带偏移时刻。

第三步 过门禁：`python scripts/gate.py check --thread thread.json --draft draft.json`。

第四步 读裁决：`exit 0` 才进入发送步骤；`exit 2` 时逐条改正文（补绝对日期、删相对措辞、改成回信），改完重跑，不许“先发后补”。

## 4 决策树（命中哪条，走哪支）

| 情形 | 如果 | 那么 | 否则 |
|---|---|---|---|
| 对方来信比我们最后一封新 | 来信时刻 > 我方最后发出时刻 | 回信，不发催 | 才考虑跟进 |
| 正文要提旧信 | 该地址确有这封信 | 写绝对日期与时刻 | 不提旧信，直接说事 |
| 正文要问“收到了吗” | 被引用那封之后已有来信 | 改问具体事项，或直接回信 | 才可问是否收到 |
| 想 24 小时内再发 | 期间对方来信给出新理由 | 可以发，并写明新理由 | 等满 24 小时 |
| 想写站位词 | 无可复算数字支撑 | 换成命令与实测值 | 删掉这句 |


## 5 六条规则（每条都能单独指出来）

| 规则 | 拦什么 | 为什么 |
|---|---|---|
| R1 | `this morning` / `yesterday` / `今早` / `上周` / `上午 09:20` | 相对时间在收件人那里无法解析，而且已经错成事实 |
| R2 | 说“我发的那封”却没有绝对日期，或该地址从未收到过信 | 引用不存在或不可定位的旧信，等于自证没读线程 |
| R3 | 问 “Did it arrive” 而对方在被引用那封之后已经来信 | 会把已完成的往返再开一轮 |
| R4 | 24 小时内对同一地址发第二封，且中间没有来信 | 频率本身就是压力，与内容无关 |
| R5 | 正文里的 `07:41` 之类在线索里找不到 | 编造或错记时刻，是可查的硬伤 |
| R6 | 断崖 / 全面超越 / 首创 / state-of-the-art | 站位断言不可测，且会在外发时反噬 |

R0 是提示级：当对方来信比我们最后一封更新时，提醒“该回信，而不是再催”。

判定语义（每条规则的失败条件、误判与豁免、接真实邮箱的约束）见 `references/details.md`。

### 5.1 禁止清单：六条硬禁令，每条都写出原因

- **禁止把非当天的信写成“今早 / this morning”** —— 因为收件人手里就有时间戳，所以这不是口误，而是可被逐条否证的事实错误。
- **禁止对已经回过的人问“收到了吗 / Did it arrive”** —— 因为对方刚写完回信，所以这句话等于宣布你没读，会被当成没礼貌的群发。
- **禁止在 24 小时内对同一地址发第二封而无新理由** —— 因为频率本身就是压力，否则内容再好也在减分。
- **禁止写一个线索里不存在的时刻** —— 因为发送时刻在邮箱里留痕，所以编造必然被抓，会毁掉整封信的可信度。
- **禁止用“断崖 / 全面超越 / 首创 / state-of-the-art”** —— 因为不可测且不可反驳，所以一个反例就能击穿，并牵连此前所有可测结论。
- **禁止只写“上次那封”而不给日期** —— 因为读者要自己考古，否则多数人不会去考，这封信会被当成群发跳过。

## 6 自检与证据

```bash
python tests/run_golden.py            # 10/10 cases match
python tests/run_golden.py --selftest # c02 ['R1','R2','R4'] -> ['R2','R4'] when R1 is removed
python demo/run_demo.py               # 发出去的那封：4 条 BLOCK；改好的那封：PASS
```

反向自检不是装饰：它删掉一条规则，要求同一用例的结论随之变化。做不到这一点，说明套件只会打印「OK」，那它证明不了任何东西。

## 7 边界（写进合同的限制）

- **不判该不该发**：门禁只回答“正文有没有和线索打架”。必要性、语气、收件人选择都仍在人手里。
- **不判技术断言真伪**：正文里的数字（70 checks、CONSISTENT 之类）必须在发前当场跑一遍取真值，门禁看不见。
- **不能强制**：它是本地脚本，绕过它直接用 SMTP 发仍然可行；它只对“愿意被拦”的流程有用。
- **无网络、无账号、无真实地址**：全部离线性由 JSON 输入保证；演示与黄金集里的联系人是化名。
- **时区**：所有时间戳必须带偏移；不带偏移的输入视为本地时间，可能造成跨时区误判。

## 8 安全边界与降级（fail closed）
- **只读、离线**：门禁不登录邮箱、不发信、不联网；输入两个 JSON，输出结论与规则编号。包里没有真实地址、没有凭据、没有连接串。
- **凭据不入包**：真实使用时凭据由调用方在进程环境里提供，本包任何文件都不得写入授权码；演示与黄金集全是化名。
- **缺字段即拒**：`thread` / `draft` / `now` 任一缺失或时间戳无法解析 → 不猜、按冲突处理并给出原因，而不是默认放行。
- **规则异常即停**：规则引擎抛异常时退出码 3，不静默返回 PASS。
- **时区不明即报**：时间戳不带偏移时按本地时间解析并提示，跨时区场景需显式写偏移。

## 9 合规红线与承诺边界

- **红线**：不得用于批量营销、骚扰、绕过对方已明示的“不要再联系”；对方说停即永久停手；不得用来生成虚假身份或伪造往来记录。
- **不作虚假承诺**：本包不承诺“零误判”“必然拦截”“已通过安全审计”。它只声明六条可被测的规则、10 条可复跑的用例，以及一条会失败的反向自检。
- **不替代判断**：PASS 只代表“正文不与线索冲突”，不代表这封信该发、语气合适、内容正确。

## 10 与同生态技能的关系

同系列（LGD）：`summarize-pro`（纪要忠实性）、`debug-pro`（复现纪律）、`wechat-viral-topic`（选题与风控）、`lgd-skill-review`（技能审计）。本包只做一件事：**外发前的线索对账**，不重复上述任何职能。
