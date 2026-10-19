#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Package the structured-analysis artefacts for reuse by writing/review skills.

Produces out/package/ with a manifest that downstream consumers
(law-literature-review, law-paper-review) can read by key.

Usage:
  python build_data_package.py --graph out/ao/ao.claim-graph.json --out-dir out/ao
"""
import argparse
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)


def load_json(path):
    p = path if os.path.isabs(path) else os.path.join(BASE, path)
    return json.load(open(p, encoding="utf-8"))


def build(graph_path, out_dir):
    g = load_json(graph_path)
    out_dir = os.path.abspath(out_dir)
    pkg = os.path.join(out_dir, "package")
    os.makedirs(pkg, exist_ok=True)

    copies = []
    for key in ("paragraph_index", "citations"):
        src = g["source"].get(key)
        if src:
            src_abs = src if os.path.isabs(src) else os.path.join(BASE, src)
            dst = os.path.join(pkg, os.path.basename(src_abs))
            shutil.copyfile(src_abs, dst)
            copies.append(os.path.basename(dst))

    # graph itself
    graph_dst = os.path.join(pkg, g["id"] + ".claim-graph.json")
    json.dump(g, open(graph_dst, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
    copies.append(os.path.basename(graph_dst))

    # image if present
    img = os.path.join(out_dir, "visuals", g["id"] + ".png")
    if os.path.exists(img):
        shutil.copyfile(img, os.path.join(pkg, g["id"] + ".png"))
        copies.append(g["id"] + ".png")

    manifest = {
        "id": g["id"],
        "title": g["title"],
        "central_claim_id": g.get("central_claim_id"),
        "files": sorted(copies),
        "node_count": len(g["nodes"]),
        "edge_count": len(g["edges"]),
        "consumers": {
            "law-literature-review": "综述模式按 id 取回核心命题/证据/引注",
            "law-paper-review": "8 专家评审用 claim graph 作共享证据底稿",
        },
    }
    json.dump(manifest, open(os.path.join(pkg, "manifest.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=2)
    return {"status": "success", "package": pkg, "manifest": manifest}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    print(json.dumps(build(args.graph, args.out_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
