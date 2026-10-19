#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Candidate node-type tagging from signal-lexicon (programmatic first pass).

This does NOT decide final labels; it gives the agent candidate types +
matched signals so the human/LLM review is grounded, not from scratch.

Usage:
  python classify_nodes.py --md article.md --lexicon assets/signal-lexicon.json --out candidates.json
  python classify_nodes.py --paragraphs article.paragraphs.json --lexicon ... --out ...
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

TYPE_BY_CATEGORY = {
    "counter_intro": "counter_position",
    "author_turn": "author_turn",
    "normative": "normative_conclusion",
    "stance": "stance",
    "central_claim": "central_claim",
    "evidence_data": "evidence_data",
    "evidence_case": "evidence_case",
    "evidence_statute": "evidence_statute",
    "evidence_soft_law": "evidence_soft_law",
    "evidence_doctrine": "evidence_doctrine",
    "evidence_archive": "evidence_archive",
    "problem_marker": "problem",
}


def load_lexicon(path):
    if not path or not os.path.exists(path):
        return {}
    return json.load(open(path, encoding="utf-8"))


def paragraphs_from_md(md_path):
    text = open(md_path, encoding="utf-8").read()
    parts = re.split(r"\n\s*\n", text)
    out = []
    for i, p in enumerate(parts):
        p = p.strip()
        if not p or p.startswith("<!--"):
            continue
        out.append({"pid": f"P{i + 1:04d}", "text": p})
    return out


def paragraphs_from_json(path):
    data = json.load(open(path, encoding="utf-8"))
    return data.get("paragraphs", data if isinstance(data, list) else [])


def tag_paragraph(text, lexicon):
    hits = []
    # single category signal lists
    for cat in ["counter_intro", "author_turn", "normative", "stance"]:
        for term in lexicon.get(cat, []):
            if term and term in text:
                hits.append((cat, term))
    # central claim markers
    for term in lexicon.get("central_claim_markers", []):
        if term and term in text:
            hits.append(("central_claim", term))
    # evidence by sub-type
    for ev_type in ["data", "case", "statute", "soft_law", "doctrine", "archive"]:
        for term in lexicon.get("evidence", {}).get(ev_type, []):
            if term and term in text:
                hits.append((f"evidence_{ev_type}", term))
    # problem: interrogative
    if "？" in text or "?" in text:
        hits.append(("problem_marker", "问句"))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default="")
    ap.add_argument("--paragraphs", default="")
    ap.add_argument("--lexicon", default=os.path.join(ROOT, "assets", "signal-lexicon.json"))
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    lexicon = load_lexicon(args.lexicon)
    paras = paragraphs_from_json(args.paragraphs) if args.paragraphs else paragraphs_from_md(args.md)

    results = []
    for p in paras:
        text = p.get("text", "")
        hits = tag_paragraph(text, lexicon)
        types = sorted({TYPE_BY_CATEGORY[c] for c, _ in hits})
        results.append({
            "pid": p.get("pid", ""),
            "page": p.get("page", ""),
            "candidate_types": types,
            "hits": [{"category": c, "term": t} for c, t in hits],
            "preview": text[:120],
        })

    out = args.out or (os.path.splitext(args.md)[0] + ".candidates.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump({"lexicon": args.lexicon, "paragraphs": results}, open(out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=2)
    tagged = sum(1 for r in results if r["candidate_types"])
    print(json.dumps({"status": "success", "out": out, "paragraphs": len(results), "tagged": tagged},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
