#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backfill skeleton metadata (year/source/volume/issue/pages) from corpus index.

Usage:
  python backfill_metadata.py --corpus <corpus_md_index.json> --skeletons <dir>
"""
import argparse
import json
import os

FIELDS = ["year", "source", "volume", "issue", "pages", "discipline", "discipline_name", "author", "title"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--skeletons", required=True)
    args = ap.parse_args()

    idx = json.load(open(args.corpus, encoding="utf-8"))
    by_id = {a["id"]: a for a in idx.get("articles", [])}

    updated = 0
    for f in sorted(os.listdir(args.skeletons)):
        if not f.endswith(".json"):
            continue
        p = os.path.join(args.skeletons, f)
        s = json.load(open(p, encoding="utf-8"))
        aid = s.get("id")
        rec = by_id.get(aid)
        if not rec:
            continue
        changed = False
        for k in FIELDS:
            if not s.get(k) and rec.get(k):
                s[k] = rec[k]
                changed = True
        if changed:
            json.dump(s, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
            updated += 1
    print(json.dumps({"status": "success", "updated": updated}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
