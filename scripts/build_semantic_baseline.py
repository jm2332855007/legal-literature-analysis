#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggregate argument skeletons into the semantic baseline (rule layer).

Reads data/argument_skeletons/*.json and produces:
  - signal-lexicon.aggregated.json  (term -> count per category)
  - discipline-profiles.aggregated.json (per discipline: evidence/claim-type/notes)
  - structure-patterns.json (H1 heading patterns)

This is the "rule layer" that makes close-reading programmable.

注意：data/argument_skeletons/ 的 400 张骨架卡不随仓库发布（体积与版权考虑）；
只有需要重建语义基线时才从本地语料重新生成（build_semantic_baseline.py 需要该目录）。

Usage:
  python build_semantic_baseline.py --skeletons data/argument_skeletons --out data/semantic_baseline
"""
import argparse
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SIGNAL_CATS = ["counter_intro", "author_turn", "normative", "stance"]
EVIDENCE_TYPES = ["case", "statute", "data", "soft_law", "doctrine", "archive"]
CLAIM_TYPES = ["normative", "descriptive", "causal", "definitive", "evaluative"]

# turn conjunctions belong to author_turn, never counter_intro (classification rule)
TURN_MARKERS = {"但是", "然而", "但", "却", "然而却", "固然……却", "虽然……但"}


def normalize_signals(sig):
    """Move turn conjunctions out of counter_intro into author_turn; keep dict fields."""
    sig = dict(sig)
    moved = []
    ci = [t for t in sig.get("counter_intro", []) if t not in TURN_MARKERS]
    for t in sig.get("counter_intro", []):
        if t in TURN_MARKERS:
            moved.append(t)
    sig["counter_intro"] = ci
    at = list(sig.get("author_turn", []))
    for t in moved:
        if t not in at:
            at.append(t)
    sig["author_turn"] = at
    return sig


def is_h1(heading):
    return not re.match(r"^[（(]", heading.strip())


def load_skeletons(d):
    out = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        try:
            out.append(json.load(open(os.path.join(d, f), encoding="utf-8")))
        except Exception as e:
            print("skip", f, e)
    return out


def aggregate(skeletons):
    signal_counts = {c: collections.Counter() for c in SIGNAL_CATS}
    evidence_totals = collections.Counter()
    claim_type_counts = collections.Counter()
    h1_patterns = collections.Counter()
    disciplines = {}

    for s in skeletons:
        sig = normalize_signals(s.get("signals", {}))
        for c in SIGNAL_CATS:
            for term in sig.get(c, []):
                signal_counts[c][term] += 1
        # count evidence from the evidence[] array (reliable per-item type),
        # not the subagent-filled evidence_type_counts (prone to footnote-count noise)
        for e in s.get("evidence", []):
            t = e.get("type")
            if t:
                evidence_totals[t] += 1
        ct = s.get("central_claim_type", "")
        if ct:
            claim_type_counts[ct] += 1
        for h in s.get("structure", []):
            if is_h1(h):
                # normalize to a stem (drop leading 一二三、 / 数字、 / 结语)
                stem = re.sub(r"^[一二三四五六七八九十]+、", "", h).strip()
                h1_patterns[stem[:12]] += 1
        disc = s.get("discipline", "?")
        dp = disciplines.setdefault(disc, {
            "discipline_name": s.get("discipline_name", disc), "n": 0,
            "claim_types": collections.Counter(), "evidence": collections.Counter(),
            "semantic_notes": [],
        })
        dp["n"] += 1
        if ct:
            dp["claim_types"][ct] += 1
        for e in s.get("evidence", []):
            t = e.get("type")
            if t:
                dp["evidence"][t] += 1
        dp["semantic_notes"].append(s.get("semantic_note", ""))

    # normalize counters
    signal_out = {c: dict(sorted(signal_counts[c].items(), key=lambda kv: -kv[1]))
                  for c in SIGNAL_CATS}
    disc_out = {}
    for d, v in disciplines.items():
        disc_out[d] = {
            "discipline_name": v["discipline_name"], "n": v["n"],
            "claim_types": dict(v["claim_types"]),
            "evidence": dict(v["evidence"]),
            "semantic_notes": v["semantic_notes"],
        }
    return {
        "signal_counts": signal_out,
        "evidence_totals": dict(evidence_totals),
        "claim_type_counts": dict(claim_type_counts),
        "h1_patterns": dict(h1_patterns.most_common()),
        "disciplines": disc_out,
        "n_skeletons": len(skeletons),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skeletons", default=os.path.join(ROOT, "data", "argument_skeletons"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "semantic_baseline"))
    args = ap.parse_args()

    skeletons = load_skeletons(args.skeletons)
    agg = aggregate(skeletons)
    os.makedirs(args.out, exist_ok=True)

    out = os.path.join(args.out, "aggregated.json")
    json.dump(agg, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)

    # readable report
    md = [f"# 语义基线聚合（{agg['n_skeletons']} 篇骨架卡）", ""]
    md.append("## 命题类型分布")
    md.append("")
    for t, n in sorted(agg["claim_type_counts"].items(), key=lambda kv: -kv[1]):
        md.append(f"- {t}: {n}")
    md.append("")
    md.append("## 信号词频（top）")
    md.append("")
    for c in SIGNAL_CATS:
        md.append(f"### {c}")
        for term, n in list(agg["signal_counts"][c].items())[:15]:
            md.append(f"- {term}: {n}")
        md.append("")
    md.append("## 学科画像")
    md.append("")
    for d, v in sorted(agg["disciplines"].items()):
        md.append(f"### {v['discipline_name']}（n={v['n']}）")
        md.append(f"- 命题类型: {v['claim_types']}")
        md.append(f"- 证据: {v['evidence']}")
        md.append("")
    open(os.path.join(args.out, "report.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))

    print(json.dumps({"status": "success", "n_skeletons": agg["n_skeletons"],
                      "out": out, "report": os.path.join(args.out, "report.md")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

