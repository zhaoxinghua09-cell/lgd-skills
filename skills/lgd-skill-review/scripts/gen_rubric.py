#!/usr/bin/env python3
"""Generate docs/rubric.json straight from the engine's own constants.

Why generated rather than hand-written: a hand-written rubric drifts from the runner the
first time someone edits a weight. This imports review.py, so weights, blocking rules and
the static cap in the JSON are the ones the engine actually uses.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "review.py")
OUT = os.path.join(HERE, "..", "docs", "rubric.json")

MEANING = {
    "structure": "元数据与目录结构是否机器可读：name/version/description/author、层级深度、体积上限",
    "consistency": "SKILL.md 里声明的命令与参数，是否真的存在于源码（本体系权重最高）",
    "reproducible": "是否有 golden 集与可执行 runner，让陌生人能复跑你的结论",
    "hygiene": "无明文密钥、无真实手机号/邮箱、无本机绝对路径",
    "discoverable": "触发词、生态互链、AI-INDEX.json 或 llms.txt，让 AI 能找到入口",
    "licensing": "有独立许可文件且有声明字段",
}

# 逐条判据与分值。这是给「要修什么」用的，不是给「我们有多严」用的。
# gen_rubric 会核对每条之和是否等于引擎权重，不等就报警——防止文档与引擎漂移。
CHECKS = {
    "structure": [
        {"check": "front-matter 有 name / description / version 三项", "points": 6,
         "fix": "在 SKILL.md 头部补 `name:` `description:` `version:`"},
        {"check": "version 是 SemVer（x.y.z）", "points": 4, "fix": "把 version 写成 `1.0.0` 这种三段"},
        {"check": "没有任何文件路径层级超过 3 段", "points": 4,
         "fix": "把深层目录拍平，如 references/a/b/c.md → references/a-c.md"},
        {"check": "无 junk 文件（.pyc / .zip / __pycache__）", "points": 3, "fix": "删掉并加 .gitignore"},
        {"check": "有展示名（displayName / display_name / name）", "points": 3, "fix": "补 `displayName:`"},
    ],
    "consistency": [
        {"check": "脚本里存在 add_argument 定义（即真的声明了参数）", "points": 10,
         "fix": "给脚本加 argparse，并在 SKILL.md 写真实可用的 `--flag`"},
        {"check": "SKILL.md 声明的每个 --flag 都在脚本里实现", "points": 5,
         "fix": "要么实现它，要么从文档删掉——这一条是最常见的失分点"},
        {"check": "（替代路径，与前两项互斥）文档写位置参数且脚本真读 sys.argv", "points": 5, "alternative": True,
         "fix": "无暇加 argparse 时，至少让 `python x.py <a>` 与实现对齐（仅得部分分）"},
        {"check": "声明的子命令在脚本里存在（add_parser）", "points": 5,
         "fix": "子命令名与实现对齐，或不要宣称子命令"},
        {"check": "正文声明了「不编造 / faithful」类保真约束", "points": 5,
         "fix": "在 SKILL.md 明确写输出保真规则（不虚构、不补全缺失事实）"},
    ],
    "reproducible": [
        {"check": "存在 tests/*.json（golden 集）", "points": 6,
         "fix": "放一个最小 case 集：输入 + 期望输出，json 即可"},
        {"check": "存在可执行 runner（tests/run_*.py / test_*.py / *_test.py）", "points": 6,
         "fix": "写一个能离线跑、零依赖的 runner，打印 pass/fail"},
        {"check": "存在 demo/（首次使用者能验证）", "points": 4, "fix": "加一个能一键跑的 demo 脚本"},
        {"check": "（仅 --run 模式）runner 真实执行且退出码 0", "points": 4,
         "fix": "让测试真的能跑通；这 4 分辨不在静态 96 之内"},
    ],
    "hygiene": [
        {"check": "全仓无明文密钥 / 手机号 / 真实个人邮箱", "points": 8,
         "fix": "删掉或改为占位符；Contact/安全报告语境下的邮箱不计泄露"},
        {"check": "SKILL.md 有安全边界或降级规则声明", "points": 7,
         "fix": "加一段「边界与异常」：不做什么、失败如何降级"},
    ],
    "discoverable": [
        {"check": "tags ≥ 3 个", "points": 5, "fix": "在 front-matter 补 `tags:` 列表"},
        {"check": "有触发词段（Triggers / 触发）", "points": 4, "fix": "写清什么情况下该调用本技能"},
        {"check": "有互链段（同系列 / 生态 / 系列技能）", "points": 3,
         "fix": "指向同系列其他技能或生态入口"},
        {"check": "有 AI-INDEX.json 或 llms.txt", "points": 3,
         "fix": "加机器可读入口，让 agent 不用读全文就能定位"},
    ],
    "licensing": [
        {"check": "front-matter 有 author", "points": 2, "fix": "补 `author:`"},
        {"check": "front-matter 有 license 字段", "points": 2, "fix": "补 `license: MIT` 之类"},
        {"check": "有独立许可文件（LICENSE / LICENSE.md）", "points": 1,
         "fix": "放许可文件本体——只有字段没有文件拿不到这 1 分"},
    ],
}


def load_engine():
    spec = importlib.util.spec_from_file_location("lgd_review_engine", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lgd_review_engine"] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    m = load_engine()
    weights = dict(m.WEIGHTS)

    # 漂移闸：逐条分值之和必须等于引擎权重，否则说明文档与引擎已不一致
    drift = []
    for key, w in weights.items():
        declared = sum(c["points"] for c in CHECKS.get(key, []) if not c.get("alternative"))
        if declared != w:
            drift.append("%s: checks=%d weight=%d" % (key, declared, w))
    if drift:
        sys.stderr.write("RUBRIC DRIFT: %s\n" % "; ".join(drift))

    doc = {
        "schema_version": "1.0",
        "engine": "scripts/review.py",
        "generated_by": "scripts/gen_rubric.py",
        "note": "数值由引擎常量导出；改引擎则此文件随之改变，不接受手改。",
        "scale": {"max_static": 96, "max_with_run": 100,
                  "explanation": "静态模式上限 96；其余 4 分需被评包自带测试真实跑通"},
        "dimensions": [
            {"key": k, "weight": w, "meaning": MEANING.get(k, ""),
             "checks": CHECKS.get(k, []),
             "points_declared": sum(c["points"] for c in CHECKS.get(k, []) if not c.get("alternative")),}
            for k, w in weights.items()
        ],
        "drift_check": {"consistent": not drift, "warnings": drift},
        "blocking_rules": [
            {"key": k, "meaning": v, "effect": "命中任意一条即整包不通过，总分不作数"}
            for k, v in dict(m.BLOCKING).items()
        ],
        "sensitive_patterns": [{"pattern": p, "label": lb} for p, lb in m.SENSITIVE],
        "verdicts": ["PASS", "FAIL", "BLOCK"],
        "how_to_use": {
            "for_a_human": "python scripts/review.py <package-dir> --json",
            "for_an_agent": "读本文件拿到权重与阻断项；逐维核对；按 findings 顺序整改；整改后重跑同一引擎复评",
            "appeal": "每条扣分可申诉：提交方给路径与检查，引擎裁定 OVERTURNED / UPHELD 并记账",
        },
        # 公开说明：一条缺陷可能同时触发多条判据，扣分按判据逐条累加，不是重复计分
        "cascade_note": {
            "rule": "one defect can fail more than one check; each failed check deducts its own points",
            "example": "缺 version 同时失去「必填三项齐全 6」与「version 是 SemVer 4」，合计 10",
            "audited_by": "tests/rubric_probe.py asserts the exact delta per case; tests/point_audit.py asserts the sums",
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("written:", os.path.abspath(OUT), "| dims:", len(doc["dimensions"]),
          "| sum:", sum(weights.values()))


if __name__ == "__main__":
    main()

