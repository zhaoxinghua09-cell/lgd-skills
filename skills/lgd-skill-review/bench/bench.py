#!/usr/bin/env python3
"""Build the LGD SkillBench: score public skill repos with the same static dual-ruler engine.

Read-only: each target is downloaded as a public tarball and reviewed statically.
Nothing from the target repository is executed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import intake_review as intake  # noqa: E402

REVIEW = os.path.join(ROOT, "scripts", "review.py")

# The benchmark walks large monorepos, so it raises the intake guard rails.
intake.MAX_FILES = 6000
intake.MAX_BYTES = 700 * 1024 * 1024

TARGETS = [
    ("vercel-labs", "agent-skills", "skills/react-best-practices"),
    ("mattpocock", "skills", "skills/engineering/code-review"),
    ("microsoft", "azure-skills", "skills/azure-deploy"),
    ("prisma", "skills", "prisma-cli"),
    ("leonxlnx", "taste-skill", "skills/taste-skill"),
    ("juliusbrussee", "caveman", "skills/caveman"),
    ("google", "agents-cli", "skills/google-agents-cli-adk-code"),
    ("anthropics", "skills", "skills/pdf"),
    ("anthropics", "skills", "skills/pptx"),
    ("anthropics", "skills", "skills/docx"),
    ("vercel-labs", "agent-browser", "skill-data/core"),
    ("obra", "superpowers", "skills/brainstorming"),
    ("addyosmani", "agent-skills", "skills/code-review-and-quality"),
    ("anthropics", "skills", "skills/skill-creator"),
    ("anthropics", "skills", "skills/frontend-design"),
    ("emilkowalski", "skills", "skills/apple-design"),
]

# Optional: score our own packages too. Set LGD_BENCH_OWN_DIR to the folder that
# contains them; no absolute path is ever written into bench.json.
OWN_NAMES = ["summarize-pro", "debug-pro", "wechat-viral-topic", "lgd-skill-review"]
OWN_DIR = os.environ.get("LGD_BENCH_OWN_DIR")


def score_dir(path):
    r = subprocess.run([sys.executable, REVIEW, path, "--json"], capture_output=True, text=True)
    if r.returncode not in (0, 1):
        return {"error": (r.stderr or "")[-300:]}
    d = json.loads(r.stdout)
    data = d.get("data", d)
    dims = data.get("dimensions", {}) or {}
    return {
        "score": data.get("structure_score", data.get("total")),
        "verdict": data.get("verdict"),
        "blocking": data.get("blocking", []),
        "dims": {k: (v.get("score") if isinstance(v, dict) else v) for k, v in dims.items()},
    }


def run_remote(owner, repo, hint):
    try:
        blob = intake.fetch(owner, repo)
    except Exception as e:
        return {"error": "fetch failed: %s" % e}
    tmp = tempfile.mkdtemp(prefix="bench-")
    try:
        try:
            intake.extract(blob, tmp)
            skill_dir = intake.find_skill_dir(tmp, hint)
        except SystemExit as e:
            return {"error": str(e)}
        rel = os.path.relpath(skill_dir, tmp).replace(os.sep, "/")
        out = score_dir(skill_dir)
        out["dir"] = rel
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    rows = []
    for owner, repo, hint in TARGETS:
        label = "%s/%s%s" % (owner, repo, ("@" + hint) if hint else "")
        print("... " + label, file=sys.stderr)
        res = run_remote(owner, repo, hint)
        res["target"] = label
        res["bucket"] = "third-party"
        rows.append(res)

    for name in OWN_NAMES:
        if not OWN_DIR:
            break
        row = score_dir(os.path.join(OWN_DIR, name))
        row["target"] = name
        row["bucket"] = "lgd"
        rows.append(row)

    out = os.path.join(HERE, "bench.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("written: %s (%d rows)" % (out, len(rows)))

    emit_machine_readable(rows)


def emit_machine_readable(rows):
    """给 AI 与徽章用的两份派生物：leaderboard.json（榜单）与 badge.json（shields 端点格式）。

    这两个文件不参与评分，只做「可被机器持续消费」的出口：榜单变了，徽章跟着变。
    """
    third = sorted([r for r in rows if r.get("bucket") == "third-party"], key=lambda r: -(r.get("score") or 0))
    own = sorted([r for r in rows if r.get("bucket") == "lgd"], key=lambda r: -(r.get("score") or 0))
    top_third = third[0]["score"] if third else 0
    best_own = own[0]["score"] if own else 0

    board = {
        "schema": "lgd-skillbench/leaderboard/1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "engine": "lgd-skill-review/scripts/review.py (static mode, no target code executed)",
        "scale": {"max": 100, "static_cap_note": "100 requires --run with the target's own tests"},
        "summary": {
            "third_party_entries": len(third),
            "lgd_entries": len(own),
            "third_party_top": top_third,
            "lgd_top": best_own,
            "gap": best_own - top_third,
        },
        "rows": [
            {
                "target": r.get("target"),
                "bucket": r.get("bucket"),
                "score": r.get("score"),
                "verdict": r.get("verdict"),
                "blocking": r.get("blocking", []),
            }
            for r in third + own
        ],
        "limits": [
            "measures verifiability, not usefulness or popularity",
            "low score means evidence is missing, not that the skill is bad",
            "single point-in-time snapshot; sample is not random",
        ],
    }
    lb = os.path.join(HERE, "leaderboard.json")
    with open(lb, "w", encoding="utf-8") as f:
        json.dump(board, f, ensure_ascii=False, indent=2)

    badge = {
        "schemaVersion": 1,
        "label": "verifiability",
        "message": "peers %d / LGD %d" % (top_third, best_own),
        "color": "brightgreen" if best_own - top_third >= 50 else "orange",
    }
    bb = os.path.join(HERE, "badge.json")
    with open(bb, "w", encoding="utf-8") as f:
        json.dump(badge, f, ensure_ascii=False)
    print("written: %s, %s" % (lb, bb))


if __name__ == "__main__":
    main()

