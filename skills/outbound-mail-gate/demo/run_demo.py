#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo: the same thread, two drafts - the one that went out, and the fixed one.

    python demo/run_demo.py

Names, addresses and subjects are synthetic; the timing is not. Both drafts
carry an explicit `now`, so the verdicts are the same on any machine.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import gate_rules as G  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(name):
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


thread = load("thread.json")
for name, label in (("draft_as_sent.json", "the draft that went out on 20 Nov 2026 09:20"),
                    ("draft_fixed.json", "the corrected draft, one day later")):
    draft = load(name)
    findings = G.check(thread, draft)
    print("=" * 72)
    print(label)
    print("-" * 72)
    print(G.report(findings))
print("=" * 72)
print("Note what the gate does not do: it does not decide whether the mail should be")
print("sent at all, and it cannot see tone. It only checks the claims against the thread.")
