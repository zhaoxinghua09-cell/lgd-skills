# 样例输入输出（可复现）

**技能包 → 维度评分 + 判定 + 整改项**

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

## 实际输出

退出码：0

```text
=== 第一步：评一个坏包 ===
改前：16/100  BLOCK
   阻断 secret_leak:SKILL.md
   [P0] secret_leak
   [P1] [consistency] 未检出任何脚本参数声明（如无脚本可忽略）
   [P1] [reproducible] 无测试用例文件（tests/*.json）
   [P1] [reproducible] 无测试执行器（tests/run_*.py），别人无法复跑
   [P1] [reproducible] 无 demo，首次使用者无从验证
   [P1] [hygiene] SKILL.md 未声明安全边界或降级规则

=== 第二步：按整改清单修 ===
已补：display_name/display_name_en/category、SemVer、去密钥、tests、demo、ai-index、llms.txt、LICENSE

=== 第三步：复测 ===
改后：100/100  PASS

=== 第四步：对照组（一开始就合格的包） ===
对照组：100/100  PASS
   [P2] [reviewer] 建议补：评分口径公开
   [P2] [reviewer] 建议补：闭环演示

演示结论：通过：闭环成立（改前 16 → 改后 100，+84）
```

## 核对要点

- 输出中的日期、数字、人名均能在输入文件里逐字找到；找不到即为缺陷。
- 输出结构应与 SKILL.md 声明的骨架一致。
- 生成时间：2026-11-19T01:24:36
