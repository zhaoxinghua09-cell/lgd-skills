# 样例输入输出（可复现）

**错误日志 → 分诊结论 + 排查顺序**

本文件里的输出不是手写示例，是把命令真跑一遍得到的原文。

## 复现命令

```bash
cd <repo>
python demo/run_demo.py
```

环境：Python 3.9+，零第三方依赖。运行时不联网、不读环境变量、不调用任何模型 API。

## 输入文件

- `demo\RUN-LOG.txt`
- `demo\SAMPLE-IO.md`
- `demo\repro_steps.md`
- `demo\sample_error.txt`

## 实际输出

退出码：0

```text
=== 1) 分诊 ===
异常类型 : json.decoder.JSONDecodeError
栈首帧   : {'file': '/usr/lib/python3.11/json/__init__.py', 'line': 346, 'func': 'loads'}
退出码   : ['1', '500']
HTTP     : ['500']
时间戳   : ['2026-11-18 09:12:44.301', '2026-11-18 09:13:02.117', '2026-11-18 09:13:02.884', '2026-11-18 09:13:03.002']
结论     : PASS 关键要素齐全，可据此复现

=== 2) 合格复现步骤 ===
verdict=PASS missing=[] steps=5
结论     : PASS 五要素齐全

=== 3) 残缺复现步骤（故意删掉环境与期望） ===
verdict=FAIL missing=['版本环境', '期望与实际']
结论     : PASS 准确抓出缺项

=== 4) 环境快照脱敏 ===
已排除疑似密钥项 : 7
结论     : PASS 零泄漏（含 KEY/TOKEN/SECRET 的项全部剔除）

=== 汇总：全 PASS ===
```

## 核对要点

- 输出中的日期、数字、人名均能在输入文件里逐字找到；找不到即为缺陷。
- 输出结构应与 SKILL.md 声明的骨架一致。
- 生成时间：2026-11-19T01:24:35
