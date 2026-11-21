#!/usr/bin/env python3
"""Record executed-test proof for the four LGD packages.

Static scoring caps at 96. The remaining 4 points require the package's own tests to actually run.
Nobody else's published number in our sample is backed by an execution we performed — this file is
the difference between "claims" and "ran it".

Output: bench/run-proof.json (score, verdict, per-dimension, timestamp, engine version, git commit
if available). Never writes absolute paths.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REVIEW = os.path.join(HERE, "review.py")
OWN_DIR = os.environ.get("LGD_BENCH_OWN_DIR") or os.path.join(ROOT, "..")
NAMES = ["summarize-pro", "debug-pro", "wechat-viral-topic", "lgd-skill-review"]
OUT = os.path.join(ROOT, "bench", "run-proof.json")


def git_commit():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True)
        return r.stdout.strip() or None
    except OSError:
        return None


def main():
    rows = []
    for name in NAMES:
        path = os.path.join(OWN_DIR, name)
        if not os.path.isdir(path):
            rows.append({"package": name, "error": "not found"})
            continue
        r = subprocess.run([sys.executable, REVIEW, path, "--json", "--run"],
                           capture_output=True, text=True)
        try:
            data = json.loads(r.stdout[r.stdout.index("{"):])["data"]
        except (ValueError, KeyError):
            rows.append({"package": name, "error": (r.stderr or "")[-200:]})
            continue
        rows.append({
            "package": name,
            "score": data.get("total"),
            "verdict": data.get("verdict"),
            "blocking": data.get("blocking", []),
            "dimensions": {k: (v.get("score") if isinstance(v, dict) else v)
                           for k, v in (data.get("dimensions") or {}).items()},
            "tests_executed": True,
        })

    doc = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine": "scripts/review.py --run",
        "commit": git_commit(),
        "note": "这些分数来自真实执行被评包自带测试，不是静态自述；静态上限 96，执行后可到 100。",
        "packages": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for row in rows:
        print("%-18s %s %s" % (row.get("package"), row.get("score"), row.get("verdict")))
    print("written:", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
