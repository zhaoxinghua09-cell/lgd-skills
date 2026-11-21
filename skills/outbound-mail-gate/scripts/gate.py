#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line for the outbound mail gate.

    python scripts/gate.py check --thread t.json --draft d.json
    python scripts/gate.py check --thread t.json --draft d.json --json
    python scripts/gate.py explain

`check` exits 0 when the draft passes and 2 when any rule blocks, so it can sit
in front of a send step and stop it. Nothing here sends mail or opens a socket.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_rules as G  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def cmd_check(args):
    thread = load(args.thread)
    draft = load(args.draft)
    findings = G.check(thread, draft)
    v = G.verdict(findings)
    if args.json:
        print(json.dumps({"verdict": v, "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print("verdict:", v)
        for f in findings:
            print("  %-5s [%s] %s" % (f["level"].upper(), f["rule"], f["message"]))
    return 0 if v == "PASS" else 2


def cmd_explain(_args):
    for rid, title in G.RULE_TITLES.items():
        print("%s  %s" % (rid, title))
    print("R0  (advisory only) an inbound message is newer than our last message")
    return 0


def main():
    ap = argparse.ArgumentParser(prog="gate")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="judge one draft against one thread")
    c.add_argument("--thread", required=True)
    c.add_argument("--draft", required=True)
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_check)
    e = sub.add_parser("explain", help="list the rules")
    e.set_defaults(func=cmd_explain)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
