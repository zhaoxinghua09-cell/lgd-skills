#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Outbound mail gate: rules a follow-up email must pass before it is sent.

The point of the package is one sentence: before asking "did it arrive?", look
at whether it already arrived. Every rule here is stated as a check over two
plain JSON objects - the thread as the mailbox actually records it, and the
draft as written - so the rules can be tested offline with no account, no
network and no real addresses.

Thread shape:
    {"sent":    [{"ts": "2026-11-19T08:20:52+08:00", "subject": "..."}],
     "inbound": [{"ts": "2026-11-19T10:49:21+08:00", "subject": "..."}]}

Draft shape:
    {"now": "2026-11-20T09:20:57+08:00", "subject": "...", "body": "..."}

`now` is explicit so the same draft always gets the same verdict.
"""
import re
from datetime import datetime, timedelta

RULE_TITLES = {
    "R1": "no relative time wording",
    "R2": "a claimed prior message must exist and be dated",
    "R3": "must not assume silence the thread contradicts",
    "R4": "one contact per address per 24 h unless they wrote back",
    "R5": "a stated clock time must exist in the thread",
    "R6": "no standing claims",
}

RELATIVE_TIME = [
    r"\bthis morning\b", r"\bthis afternoon\b", r"\bthis evening\b",
    r"\bearlier today\b", r"\btoday\b", r"\byesterday\b", r"\btonight\b",
    r"\bjust now\b", r"\bjust sent\b", r"\blast night\b", r"\bthis week\b",
    r"\blast week\b", r"\ba few days ago\b", r"\bthe other day\b",
    "今早", "今天上午", "今天下午", "昨天", "刚才", "刚刚", "今日", "上周", "几天前",
]
RELATIVE_CN_CLOCK = r"(?:上午|下午|晚上)\s*\d{1,2}\s*[:：]\s*\d{2}"

CLAIM_PRIOR = [
    r"\bthe message i sent\b", r"\bthe note i sent\b", r"\bthe email i sent\b",
    r"\bmy (?:last|previous|earlier) (?:message|email|note)\b",
    r"我(?:上午|昨天|之前)?(?:发|寄)的(?:那封|邮件)", "那封", "上一封",
]
ASSUME_SILENT = [
    r"\bdid it arrive\b", r"\bdid you (?:get|receive)\b", r"\bdid my .{0,20}arrive\b",
    r"\bif you (?:have )?not (?:seen|received|got)\b",
    "收到了吗", "是否(?:已经)?(?:收到|看到)", "如果您已经看到但不方便",
]
BANNED_CLAIM = [r"断崖", r"全面超越", r"明显更强", r"首创", r"\bsecond to none\b",
                r"\bunmatched\b", r"\bstate[- ]of[- ]the[- ]art\b", r"\bbest[- ]in[- ]class\b"]

CLAIM_CLOCK = re.compile(r"(?<!\d)(\d{1,2})\s*[:：]\s*(\d{2})(?!\d)")
EXPLICIT_DATE = re.compile(
    r"(\d{1,2}\s*月\s*\d{1,2}\s*日)|(\d{1,2}\s*[-/]\s*\d{1,2})|"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2})|"
    r"(\d{4}-\d{2}-\d{2})")


def _parse(ts):
    return datetime.fromisoformat(ts)


def _ts(row):
    try:
        return _parse(row["ts"])
    except (KeyError, ValueError):
        return None


def _sorted(rows):
    return sorted([r for r in rows if _ts(r)], key=_ts)


def _hit(text, patterns):
    low = text.lower()
    found = []
    for p in patterns:
        target = low if p.isascii() else text
        if re.search(p, target):
            found.append(p)
    return found


def _clock_minutes(text):
    out = []
    for hh, mm in CLAIM_CLOCK.findall(text):
        if int(hh) <= 23 and int(mm) <= 59:
            out.append("%02d:%s" % (int(hh), mm))
    return out


def check(thread, draft):
    """Return findings: list of {"rule", "level" (block|warn), "message"}."""
    sent = _sorted(thread.get("sent", []))
    inbound = _sorted(thread.get("inbound", []))
    body = draft.get("body", "") or ""
    subject = draft.get("subject", "") or ""
    text = subject + "\n" + body
    now = _parse(draft["now"])
    findings = []

    def add(rule, message, level="block"):
        findings.append({"rule": rule, "level": level, "message": message})

    # R1 relative time wording
    hits = _hit(text, RELATIVE_TIME)
    cn = re.search(RELATIVE_CN_CLOCK, text)
    if hits or cn:
        why = ", ".join(sorted(set(hits))) or "上午/下午 HH:MM"
        add("R1", "relative time wording (%s); write an absolute date and time instead" % why)

    # R2 claimed prior message
    claims = _hit(text, CLAIM_PRIOR)
    if claims:
        if not sent:
            add("R2", "the body refers to an earlier message, but none was ever sent to this address")
        elif not EXPLICIT_DATE.search(text):
            last = _ts(sent[-1]).strftime("%Y-%m-%d %H:%M")
            add("R2", "the body refers to an earlier message without an absolute date; "
                      "the newest one on record is %s" % last)

    # R3 assumptions about silence
    assumes = _hit(text, ASSUME_SILENT)
    if assumes:
        last_in = _ts(inbound[-1]) if inbound else None
        clocks = _clock_minutes(text)
        referenced = []
        for stamp in clocks:
            for row in sent:
                if _ts(row).strftime("%H:%M") == stamp:
                    referenced.append(_ts(row))
        for ref in referenced:
            if last_in and last_in > ref:
                add("R3", "the body asks about the message of %s, but the correspondent wrote on %s"
                    % (ref.strftime("%Y-%m-%d %H:%M"), last_in.strftime("%Y-%m-%d %H:%M")))
                break
        else:
            if last_in and sent and last_in > _ts(sent[-1]):
                add("R3", "the body assumes no answer, but the correspondent wrote on %s, after our "
                          "last message (%s)"
                    % (last_in.strftime("%Y-%m-%d %H:%M"), _ts(sent[-1]).strftime("%Y-%m-%d %H:%M")))

    # R4 frequency
    if sent:
        last_out = _ts(sent[-1])
        hours = (now - last_out).total_seconds() / 3600.0
        replied = bool(inbound) and _ts(inbound[-1]) > last_out
        if hours < 24 and not replied:
            add("R4", "second message to the same address %.1f h after the previous one "
                      "with no reply in between (window is 24 h)" % hours)

    # R5 stated clock time must exist in the thread
    if CLAIM_CLOCK.search(text):
        real = set()
        for row in sent + inbound:
            real.add(_ts(row).strftime("%H:%M"))
        for stamp in _clock_minutes(text):
            if stamp not in real:
                add("R5", "the body states a time %s that appears nowhere in this thread, "
                          "either direction (real ones: %s)"
                    % (stamp, ", ".join(sorted(real)) or "none"))

    # R6 standing claims
    banned = _hit(text, BANNED_CLAIM)
    if banned:
        add("R6", "standing claim (%s); describe what was measured, not how it ranks"
            % ", ".join(banned))

    # advisory only
    if inbound and sent and _ts(inbound[-1]) > _ts(sent[-1]):
        add("R0", "an inbound message is newer than our last message; answering it is the "
                  "open task, not sending another reminder", level="warn")
    return findings


def verdict(findings):
    return "BLOCK" if any(f["level"] == "block" for f in findings) else "PASS"


def report(findings):
    lines = [verdict(findings)]
    for f in findings:
        lines.append("  %-4s [%s] %s" % (f["level"].upper(), f["rule"], f["message"]))
    return "\n".join(lines)
