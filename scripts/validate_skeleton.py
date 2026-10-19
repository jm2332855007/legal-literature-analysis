#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate argument-skeleton cards (quality gate for close-reading output).

Checks: required fields, and that every id referenced by argument_chain /
evidence.supports / positions.target actually exists.

Usage:
  python validate_skeleton.py data/argument_skeletons/*.json
"""
import json
import sys

REQUIRED = ["id", "title", "author", "discipline", "structure", "problem",
            "central_claim", "central_claim_type", "premises", "evidence",
            "positions", "normative_conclusions", "argument_chain", "signals", "semantic_note"]

RELATIONS = {"supports", "attacks", "qualifies", "derives", "motivates"}
EVIDENCE_TYPES = {"case", "statute", "data", "soft_law", "doctrine", "archive"}
CLAIM_TYPES = {"normative", "descriptive", "causal", "definitive", "evaluative"}


def check(s):
    errs = []
    for k in REQUIRED:
        if k not in s:
            errs.append(f"missing field: {k}")
    if not isinstance(s.get("premises"), list) or not s.get("premises"):
        errs.append("premises empty")
    if not isinstance(s.get("evidence"), list) or not s.get("evidence"):
        errs.append("evidence empty")
    if not isinstance(s.get("positions"), list) or not s.get("positions"):
        errs.append("positions empty (need counter/literature)")
    if not isinstance(s.get("normative_conclusions"), list) or not s.get("normative_conclusions"):
        errs.append("normative_conclusions empty")

    # collect ids
    ids = {"Q1", "C1"}
    for p in s.get("premises", []):
        ids.add(p.get("id"))
    for e in s.get("evidence", []):
        ids.add(e.get("id"))
        if e.get("type") not in EVIDENCE_TYPES:
            errs.append(f"evidence {e.get('id')} bad type {e.get('type')}")
    for pos in s.get("positions", []):
        ids.add(pos.get("id"))
    for n in s.get("normative_conclusions", []):
        ids.add(n.get("id"))

    if s.get("central_claim_type") not in CLAIM_TYPES:
        errs.append(f"bad central_claim_type: {s.get('central_claim_type')}")

    for e in s.get("argument_chain", []):
        if e.get("from") not in ids or e.get("to") not in ids:
            errs.append(f"chain dangling: {e}")
        if e.get("relation") not in RELATIONS:
            errs.append(f"bad relation: {e.get('relation')}")

    for e in s.get("evidence", []):
        sup = e.get("supports", "")
        if sup and sup not in ids:
            errs.append(f"evidence {e.get('id')} supports missing id {sup}")
    for pos in s.get("positions", []):
        t = pos.get("target", "")
        if t and t not in ids:
            errs.append(f"position {pos.get('id')} target missing id {t}")
    return errs


def anchor_warnings(s):
    """WARN-level: check quote anchors are present on semantic claims.
    Missing anchors do NOT fail the card (legacy 400 cards have none),
    but flag it so rework/new cards can be held to the fidelity standard.
    """
    warns = []
    # central_claim is a plain string; anchor lives in a parallel key
    if not (s.get("central_claim_anchor") or s.get("central_claim_quote")):
        warns.append("central_claim missing anchor (source_anchor/quote)")
    for p in s.get("premises", []):
        if not (p.get("source_anchor") or p.get("quote")):
            warns.append(f"premise {p.get('id')} missing anchor")
    for pos in s.get("positions", []):
        if not (pos.get("source_anchor") or pos.get("quote")):
            warns.append(f"position {pos.get('id')} missing anchor")
    for e in s.get("evidence", []):
        if not (e.get("source_anchor") or e.get("quote")):
            warns.append(f"evidence {e.get('id')} missing anchor")
    return warns


def main():
    paths = sys.argv[1:]
    if not paths:
        print("usage: validate_skeleton.py skeleton.json [...]")
        return 2
    failed = 0
    for p in paths:
        s = json.load(open(p, encoding="utf-8"))
        errs = check(s)
        print(("PASS " if not errs else "FAIL ") + p)
        for e in errs:
            print("  -", e)
        failed += bool(errs)
        warns = anchor_warnings(s)
        if warns:
            print(f"  WARN {len(warns)} items missing anchor (first 3):")
            for w in warns[:3]:
                print("    ~", w)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
