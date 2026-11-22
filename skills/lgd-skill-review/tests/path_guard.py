#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prove the CLIs cannot be walked out of the package they were pointed at.

The threat is not exotic: in an agent workflow the "directory to review"
argument may itself be model-produced. `review.py ../..` must not turn into a
reader of files outside the package, and `quickfix.py` must not write there.
This test builds the adversarial cases and asserts they are refused.
"""
import os
import sys
import tempfile

HIRE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HIRE), "scripts")
sys.path.insert(0, SCRIPTS)

import safeio  # noqa: E402
import review  # noqa: E402

FAILS = []


def expect_refused(path, why):
    try:
        safeio.guard(path)
    except safeio.PathOutside:
        print("PASS refused  %-42s %s" % (why, path))
    else:
        FAILS.append(why)
        print("FAIL allowed  %-42s %s" % (why, path))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        pkg = os.path.join(tmp, "pkg")
        os.makedirs(os.path.join(pkg, "references"))
        secret = os.path.join(tmp, "outside.txt")
        with open(secret, "w", encoding="utf-8") as fh:
            fh.write("TOPSECRET\n")
        with open(os.path.join(pkg, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nname: demo\ndescription: demo\n---\n\n# demo\n")

        safeio.set_root(pkg)

        expect_refused(os.path.join(pkg, "..", "outside.txt"), "parent-dir sibling")
        expect_refused(os.path.join(pkg, "..", "..", "..", "etc", "passwd"), "three levels up")
        expect_refused(secret, "absolute path outside root")

        body = review.read(secret)
        if body == "":
            print("PASS review.read() refused an outside file")
        else:
            FAILS.append("review.read leaked outside content")
            print("FAIL review.read leaked outside content")

        inside = review.read(os.path.join(pkg, "SKILL.md"))
        if "demo" in inside:
            print("PASS review.read() still reads inside the package")
        else:
            FAILS.append("review.read broke inside access")
            print("FAIL review.read broke inside access")

    if FAILS:
        print("---- %d FAIL ----" % len(FAILS))
        return 1
    print("---- ALL PASS ----")
    return 0


if __name__ == "__main__":
    sys.exit(main())
