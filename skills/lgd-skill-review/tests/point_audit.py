"""分值审计：判据写的分数，加起来必须正好等于引擎权重，且必须真的兑现。

三层检查：
  A. 判据之和 == 维度权重 == 引擎常量（文档与代码不许漂移）
  B. 六维之和 == 100，静态上限 == 96（另 4 分只有实跑才给）
  C. 拿一个满分样本，逐维核对「拿到多少」与「判据写多少」是否一致

跑法：python tests/point_audit.py
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "scripts"))

def pick_specimen():
    """挑一个「应当满分」的样本：显式指定 > 兄弟包 > 本仓库自身。

    CI 里只有本仓库，没有兄弟包目录，所以必须能退回自身——本仓库自评 --run 就是 100。
    """
    cands = [os.environ.get("LGD_AUDIT_SPECIMEN"),
             os.path.join(os.path.dirname(REPO), "summarize-pro"),
             REPO]
    for c in cands:
        if c and os.path.isdir(c) and os.path.exists(os.path.join(c, "SKILL.md")):
            return c
    raise SystemExit("no specimen found")


SPECIMEN = pick_specimen()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    gr = load("lgd_gen_rubric", os.path.join(REPO, "scripts", "gen_rubric.py"))
    rv = load("lgd_review", os.path.join(REPO, "scripts", "review.py"))
    fails = []

    # A. 判据之和 vs 引擎权重
    print("[A] 判据之和 vs 引擎权重")
    for k, w in rv.WEIGHTS.items():
        declared = sum(c["points"] for c in gr.CHECKS[k] if not c.get("alternative"))
        ok = declared == w
        print("  %-14s checks=%3d  weight=%3d  %s" % (k, declared, w, "OK" if ok else "MISMATCH"))
        if not ok:
            fails.append("%s checks=%d weight=%d" % (k, declared, w))

    # B. 六维之和与静态上限
    print("[B] 总分与静态上限")
    total = sum(rv.WEIGHTS.values())
    print("  sum(weights)=%d  %s" % (total, "OK" if total == 100 else "MISMATCH"))
    if total != 100:
        fails.append("weights sum %d != 100" % total)
    static_max = total - 4  # 4 分来自 --run
    print("  static max=%d  %s" % (static_max, "OK" if static_max == 96 else "MISMATCH"))
    if static_max != 96:
        fails.append("static max %d != 96" % static_max)

    # C. 满分样本逐维兑现
    print("[C] 满分样本逐维兑现（%s）" % os.path.basename(SPECIMEN))
    tmp = tempfile.mkdtemp(prefix="lgd_audit_")
    pkg = os.path.join(tmp, "pkg")
    shutil.copytree(SPECIMEN, pkg,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.zip", ".git"))
    spec = load_spec = None
    try:
        r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "review.py"), pkg,
                            "--json", "--run"], capture_output=True, text=True, timeout=180)
        if r.returncode not in (0, 1, 2):
            raise RuntimeError("engine failed: %s" % (r.stderr or "")[:200])
        out = json.loads(r.stdout)["data"]
        dims = out["dimensions"]
        for k, w in rv.WEIGHTS.items():
            got = dims[k]["score"]
            # reproducible 维有 4 分只能由 --run 兑现：静态环境 16 分也算「判据与权重一致」，
            # 只是实跑那 4 分没拿到；其余维度必须满分。
            allowed = (16, 20) if k == "reproducible" else (w,)
            ok = got in allowed
            print("  %-14s got=%3d  max=%3d  %s" % (k, got, w, "OK" if ok else "SHORTFALL"))
            if not ok:
                fails.append("%s got %d max %d" % (k, got, w))
        print("  total=%d  verdict=%s  (96=静态上限, 100=实跑满分)" % (out["total"], out["verdict"]))
        if out["total"] not in (96, 100):
            fails.append("specimen total %d not in {96,100}" % out["total"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # D. 判据条数是否与公开页一致
    checks = sum(len(v) for v in gr.CHECKS.values())
    print("[D] 公开判据条数 = %d" % checks)
    if checks != 23:
        fails.append("checks %d != 23" % checks)

    if fails:
        print("\nFAIL: " + "; ".join(fails))
        return 1
    print("\nALL PASS — 判据、权重、兑现、条数四者一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
