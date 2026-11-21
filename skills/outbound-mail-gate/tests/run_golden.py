#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden-set runner for outbound-mail-gate.

    python tests/run_golden.py            # run all cases, exit 0 only if all match
    python tests/run_golden.py --verbose  # print every finding
    python tests/run_golden.py --selftest # control experiment: prove the suite can fail

`--selftest` removes one rule's patterns in memory and asserts that the cases
depending on it flip from BLOCK to PASS. A suite that cannot fail proves
nothing, so this check is part of the package rather than a claim about it.
Zero dependency, offline, no account.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import gate_rules as G  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load():
    with open(os.path.join(HERE, "golden.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def run_case(case):
    findings = G.check(case["thread"], case["draft"])
    verdict = G.verdict(findings)
    blocked = sorted({f["rule"] for f in findings if f["level"] == "block"})
    return verdict, blocked, findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    data = load()
    failures = 0

    if args.selftest:
        case = next(c for c in data["cases"] if c["id"] == "c02-called-it-this-morning")
        _, before, _ = run_case(case)
        original = list(G.RELATIVE_TIME)
        G.RELATIVE_TIME[:] = []
        try:
            _, after, _ = run_case(case)
        finally:
            G.RELATIVE_TIME[:] = original
        if "R1" not in before:
            print("selftest FAILED: c02 does not use R1 at all, so removing it proves nothing")
            return 1
        if "R1" in after or len(after) >= len(before):
            print("selftest FAILED: removing R1 (%s -> %s) was not detected - the harness cannot fail"
                  % (before, after))
            return 1
        print("selftest OK: c02 %s -> %s when R1 is removed - the suite can fail" % (before, after))
        return 0

    for case in data["cases"]:
        expect = case["expect"]
        v, blocked, findings = run_case(case)
        ok = v == expect["verdict"] and blocked == sorted(expect["rules"])
        print("%-38s %-5s expected %-5s -> %s" % (
            case["id"], v, expect["verdict"], "OK" if ok else "MISMATCH"))
        if not ok:
            failures += 1
            print("   expected rules: %s" % sorted(expect["rules"]))
            print("   actual rules:   %s" % blocked)
        if args.verbose:
            for f in findings:
                print("     %-5s [%s] %s" % (f["level"].upper(), f["rule"], f["message"]))
    total = len(data["cases"])
    print("\n%d/%d cases match" % (total - failures, total))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
