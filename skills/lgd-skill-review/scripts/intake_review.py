#!/usr/bin/env python3
"""Review-request intake: fetch a public skill repo and run the static dual-ruler review.

Safety contract
- Static only: review.py is invoked WITHOUT --run, so nothing from the target repo is executed.
- Download uses the public codeload tarball endpoint; no credentials of the submitter are used.
- Extraction rejects absolute paths and '..' traversal.
- Hard limits: 2000 files, 200 MB unpacked, single repo per issue.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

MAX_FILES = 2000
MAX_BYTES = 200 * 1024 * 1024
HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.join(HERE, "review.py")

URL_RE = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def _section_value(body, keyword):
    """Read a value from a GitHub issue-form body: '### <heading with keyword>' then the next non-empty line."""
    lines = (body or "").splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("###") and keyword.lower() in line.lower():
            for follow in lines[i + 1:]:
                v = follow.strip()
                if v and not v.startswith("###"):
                    return v
            return None
    return None


def parse_target(body):
    m = URL_RE.search(body or "")
    if not m:
        raise SystemExit("找不到 GitHub 仓库地址 / No GitHub repository URL found in the issue body")
    owner, repo = m.group(1), m.group(2).replace(".git", "")
    path = None
    # 1) 手写格式：Path: skills/x
    pm = re.search(r"Path:\s*([A-Za-z0-9_./-]+)", body or "")
    value = pm.group(1).strip().strip("/") if pm else None
    # 2) issue 表单格式：### Skill directory (optional) → 下一行
    if not value:
        value = (_section_value(body, "Skill directory") or "").strip().strip("/")
    if value and value.lower() not in ("auto", "none", "empty", "_no response_", "no response"):
        path = value
    return owner, repo, path


def fetch(owner, repo):
    url = "https://codeload.github.com/%s/%s/tar.gz/HEAD" % (owner, repo)
    req = urllib.request.Request(url, headers={"User-Agent": "lgd-review-intake"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


# ---- 稀疏抓取：最大的技能都住在巨型单仓里，整仓下载会被体积上限挡死 ----
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".tar", ".gz",
            ".woff", ".woff2", ".ttf", ".otf", ".mp4", ".mov", ".mp3", ".wav", ".psd", ".sketch"}
SPARSE_MAX_FILES = 120
SPARSE_MAX_FILE = 400 * 1024
SPARSE_MAX_DEPTH = 3


def head_commit(owner, repo):
    """Score must be tied to a snapshot, otherwise it cannot be re-checked tomorrow."""
    try:
        data = _api_json("%s/%s/commits/HEAD" % (owner, repo))
        return (data.get("sha") or "")[:12] or None
    except Exception:
        return None


def _headers(accept):
    h = {"User-Agent": "lgd-review-intake", "Accept": accept}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = "Bearer " + token
    return h


def _api(path):
    url = "https://api.github.com/repos/%s" % path
    req = urllib.request.Request(url, headers=_headers("application/vnd.github.raw"))
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _api_json(path):
    url = "https://api.github.com/repos/%s" % path
    req = urllib.request.Request(url, headers=_headers("application/vnd.github+json"))
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_sparse(owner, repo, path, dest):
    """Download only one subtree. Bounded by file count and per-file size."""
    state = {"files": 0, "skipped": 0}

    def walk(rel, depth):
        listing = _api_json("%s/%s/contents/%s" % (owner, repo, rel or ""))
        if isinstance(listing, dict):
            listing = [listing]
        for item in listing:
            if state["files"] >= SPARSE_MAX_FILES:
                state["skipped"] += 1
                continue
            kind = item.get("type")
            name = item.get("name", "")
            sub = (rel + "/" + name) if rel else name
            if kind == "dir":
                if depth >= SPARSE_MAX_DEPTH:
                    state["skipped"] += 1
                    continue
                walk(sub, depth + 1)
                continue
            if kind != "file":
                continue
            if os.path.splitext(name)[1].lower() in SKIP_EXT:
                state["skipped"] += 1
                continue
            if item.get("size", 0) > SPARSE_MAX_FILE:
                state["skipped"] += 1
                continue
            try:
                blob = _api("%s/%s/contents/%s" % (owner, repo, sub))
            except Exception:
                state["skipped"] += 1
                continue
            target = os.path.join(dest, sub)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as out:
                out.write(blob)
            state["files"] += 1

    walk(path, 0)

    # 仓库根的元数据文件（许可、索引、README、llms.txt）不在子树里，但评分只看包目录内部，
    # 所以要把它们放到包目录下——否则分数会虚假地偏低（稀疏抓取引入的假阴性）。
    root_meta = re.compile(r"^(LICEN[SC]E.*|AI-INDEX\.json|llms.*\.txt|README.*|SECURITY\.md|NOTICE.*)$", re.I)
    pkg_dir = os.path.join(dest, path)
    meta_dest = pkg_dir if os.path.isdir(pkg_dir) else dest
    try:
        root_listing = _api_json("%s/%s/contents/" % (owner, repo))
    except Exception:
        root_listing = []
    if isinstance(root_listing, dict):
        root_listing = [root_listing]
    for item in root_listing:
        name = item.get("name", "")
        if item.get("type") != "file" or not root_meta.match(name):
            continue
        if item.get("size", 0) > SPARSE_MAX_FILE:
            continue
        target = os.path.join(meta_dest, name)
        if os.path.isfile(target):
            continue
        try:
            blob = _api("%s/%s/contents/%s" % (owner, repo, name))
        except Exception:
            continue
        with open(target, "wb") as out:
            out.write(blob)
        state["files"] += 1

    if state["files"] == 0:
        raise SystemExit("稀疏抓取没取到文件 / sparse fetch returned nothing for %s" % path)
    return state


def extract(blob, dest):
    """解包前把每个成员的名字收敛成工作区内路径。

    2026-11-21 SonarCloud 报 BLOCKER（S6096 Zip Slip）：单看 `".." in name.split("/")`
    是够的，但静态分析看不到"先判断、后拼接"的因果，而且 `os.path.join` 之后没有任何
    落地校验。这里改成对最终路径做 realpath 包含性断言——即便名字被构造成绝对路径、
    或带 `..` 前缀、或大小写/分隔符变形，落点也必须仍在 dest 里。
    """
    dest_real = os.path.realpath(dest)
    count = 0
    total = 0
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        for member in tf.getmembers():
            name = member.name
            if not member.isfile():
                continue
            if name.startswith("/") or ".." in name.split("/"):
                raise SystemExit("不安全路径，已中止 / unsafe path in archive: %s" % name)
            total += member.size
            count += 1
            if count > MAX_FILES or total > MAX_BYTES:
                raise SystemExit("超出体积/文件数上限 / archive exceeds limits")
            target = os.path.realpath(os.path.join(dest, name))
            if target != dest_real and not target.startswith(dest_real + os.sep):
                raise SystemExit("解包路径越界，已中止 / archive entry escapes dest: %s" % name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with tf.extractfile(member) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)


def find_skill_dir(root, hint=None):
    if hint:
        normalized = hint.strip("/")
        for dirpath, _dirs, files in os.walk(root):
            if "SKILL.md" not in files:
                continue
            rel = os.path.relpath(dirpath, root).replace(os.sep, "/")
            if rel == normalized or rel.endswith("/" + normalized):
                return dirpath
        raise SystemExit("指定目录里没有 SKILL.md / no SKILL.md at %s" % hint)
    best = None
    for dirpath, _dirs, files in os.walk(root):
        if "SKILL.md" in files:
            depth = dirpath[len(root):].count(os.sep)
            if best is None or depth < best[0]:
                best = (depth, dirpath)
    if not best:
        raise SystemExit("仓库里找不到 SKILL.md / no SKILL.md anywhere in the repository")
    return best[1]


def render(data, owner, repo, skill_rel, commit_sha=None):
    d = data.get("data", data)
    dims = d.get("dimensions", {})
    blocking = d.get("blocking", [])
    findings = d.get("findings", []) or []
    lines = []
    lines.append("### LGD Dual-Ruler Review — `%s/%s`" % (owner, repo))
    lines.append("")
    lines.append("| 项 / Item | 值 / Value |")
    lines.append("|---|---|")
    lines.append("| Structure score / 结构分 | **%s / 100** |" % d.get("structure_score", d.get("total", "-")))
    if d.get("semantics_score") is not None:
        lines.append("| Semantics score / 语义分 | **%s / 120** |" % d.get("semantics_score"))
    lines.append("| Verdict / 结论 | **%s** |" % d.get("verdict", "-"))
    lines.append("| Skill directory | `%s` |" % skill_rel)
    if commit_sha:
        lines.append("| Snapshot / 快照 | `%s` |" % commit_sha)
    lines.append("| Mode | static only, no code executed / 仅静态，不执行代码 |")
    lines.append("")
    score = d.get("structure_score", d.get("total", 0))
    try:
        low = float(score) < 60
    except (TypeError, ValueError):
        low = False
    if low:
        lines.append("> 口径提醒 / What this score means：本引擎量的是**可验证性**（测试、声明与实现一致、可复跑、机器可读索引、许可），"
                     "**不是流行度或内容好坏**。一个装量很高的技能也可能因为缺 tests/ 与许可文件而得低分——"
                     "这说明它目前无法被第三方独立验证，不代表它不可用。")
        lines.append("")
        lines.append("> This engine measures **verifiability** — tests, declared-vs-implemented consistency, reproducibility, "
                     "a machine-readable index and licensing — **not popularity or usefulness**. A widely installed skill "
                     "can score low here simply because it ships no tests or license, which means others cannot verify it independently. "
                     "It does not mean the skill is unusable.")
        lines.append("")
    if blocking:
        lines.append("**Blocking / 阻断项**")
        for b in blocking[:12]:
            lines.append("- `%s`" % b)
        lines.append("")
    if dims:
        lines.append("**Dimensions / 各维度**")
        lines.append("")
        lines.append("| Dimension | Score |")
        lines.append("|---|---|")
        for k, v in (dims.items() if isinstance(dims, dict) else []):
            if isinstance(v, dict):
                lines.append("| %s | %s |" % (k, v.get("score", "-")))
            else:
                lines.append("| %s | %s |" % (k, v))
        lines.append("")
    if findings:
        lines.append("**Remediation list / 整改清单**")
        for f in findings[:20]:
            if isinstance(f, dict):
                lines.append("- `%s` %s — %s" % (f.get("id", "-"), f.get("title") or f.get("rule", ""), f.get("fix") or f.get("message", "")))
            else:
                lines.append("- %s" % f)
        lines.append("")

    # Gap decomposition + mechanical projection (projection, not a promise)
    if isinstance(dims, dict) and dims:
        mechanical = {"licensing": "加 LICENSE 文件 / add a LICENSE file",
                      "discoverable": "加机器可读索引 AI-INDEX.json 或 llms.txt / add a machine-readable index",
                      "consistency": "让声明的命令与脚本 argparse 一致 / align declared commands with the scripts",
                      "hygiene": "清掉绝对路径与临时文件 / scrub absolute paths and temp files"}
        rows = []
        gain = 0
        for k, v in dims.items():
            if not isinstance(v, dict):
                continue
            got, mx = v.get("score", 0), v.get("max", 0)
            gap = mx - got
            if gap <= 0:
                continue
            fix = mechanical.get(k, "需真写测试并离线跑通 / requires real tests that run offline")
            can = k in mechanical
            if can:
                gain += gap
            rows.append((k, got, mx, gap, fix, can))
        if rows:
            lines.append("**缺在哪、补什么 / Where the points went, and what closes it**")
            lines.append("")
            lines.append("| Dimension | Got | Max | Gap | What closes it | Mechanical? |")
            lines.append("|---|---|---|---|---|---|")
            for k, got, mx, gap, fix, can in rows:
                lines.append("| %s | %s | %s | %s | %s | %s |" % (k, got, mx, gap, fix, "是 / yes" if can else "否 / no"))
            lines.append("")
            try:
                base = float(d.get("structure_score", d.get("total", 0)))
            except (TypeError, ValueError):
                base = 0
            projected = min(100, int(base + gain))
            lines.append("**机械可补上限 / Projected ceiling from mechanical fixes only: %d / 100**" % projected)
            lines.append("")
            lines.append("> 这是**预测**，不是承诺：只把「加许可、加索引、对齐命令、清路径」这类确定性动作计入，"
                         "**不含写测试**。要把可复跑维度拿满，必须真的交付能离线跑通的 tests。")
            lines.append(">")
            lines.append("> This is a **projection, not a promise**: it counts only deterministic fixes (license, machine-readable index, "
                         "aligned commands, path hygiene). It **does not include writing tests** — the reproducibility dimension "
                         "only fills when real offline tests exist.")
            lines.append("")
    # 机器可读块：让 agent 直接反序列化，不用解析上面的散文
    machine = {
        "schema_version": "1.0",
        "engine": "review.py (static)",
        "repo": "%s/%s" % (owner, repo),
        "skill_path": skill_rel,
        "target_commit": commit_sha,
        "score": d.get("structure_score", d.get("total")),
        "semantics": d.get("semantics_score"),
        "verdict": d.get("verdict"),
        "blocking": blocking,
        "dimensions": {k: (v.get("score") if isinstance(v, dict) else v)
                       for k, v in (dims.items() if isinstance(dims, dict) else [])},
        "rubric": "https://zhaoxinghua09-cell.github.io/lgd-skill-review/rubric.json",
        "registry": "https://zhaoxinghua09-cell.github.io/lgd-skill-review/registry.json",
        "reproduce": "python scripts/review.py <local-clone-of-this-repo> --json",
    }
    lines.append("")
    lines.append("<details><summary>机器可读结果 / machine-readable result（供 agent 直接消费）</summary>")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(machine, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("</details>")
    lines.append("")
    lines.append("---")
    lines.append("*Static analysis only; nothing in your repository was executed. "
                 "Appeals take evidence: name a path and a check, and we open it and rule OVERTURNED / UPHELD.*")
    lines.append("*仅静态分析，未执行你仓库里的任何内容。申诉需带证据：给出路径与检验方法，我们复核后裁定 推翻 / 维持。*")
    return "\n".join(lines)


def main():
    body = sys.argv[1] if len(sys.argv) > 1 else ""
    owner, repo, hint = parse_target(body)
    tmp = tempfile.mkdtemp(prefix="lgd-intake-")
    if hint:
        # 给定了 Path：只取这个子树，巨型单仓也能评
        state = fetch_sparse(owner, repo, hint, tmp)
        sys.stderr.write("sparse: files=%d skipped=%d\n" % (state["files"], state["skipped"]))
    else:
        blob = fetch(owner, repo)
        extract(blob, tmp)
    skill_dir = find_skill_dir(tmp, hint)
    rel = os.path.relpath(skill_dir, tmp).replace(os.sep, "/")
    outer = subprocess.run([sys.executable, REVIEW, skill_dir, "--json"],
                           capture_output=True, text=True)
    if outer.returncode not in (0, 1):
        sys.stderr.write(outer.stderr)
        raise SystemExit("评审引擎执行失败 / review engine failed")
    payload = json.loads(outer.stdout)
    print(render(payload, owner, repo, rel, head_commit(owner, repo)))


if __name__ == "__main__":
    main()

