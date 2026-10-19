#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check a claim graph against an issues checklist (graph-vs-analysis consistency).

Why: a diagnosis graph is only useful if every problem listed in the analysis
document actually carries a diagnosis marker (and citations are correctly
attributed). Manual marking silently drifts; this gate catches drift.

Usage:
  python check_graph_issues.py --graph examples/anquan/anquan.claim-graph.json \
      --issues examples/anquan/anquan.issues.json

Exit 0 only if every expected issue is marked and every citation matches.
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--issues", required=True)
    args = ap.parse_args()

    g = json.load(open(args.graph, encoding="utf-8"))
    chk = json.load(open(args.issues, encoding="utf-8"))

    nodes = {n["id"]: n for n in g.get("nodes", [])}
    edges = {(e["from"], e["to"]): e for e in g.get("edges", [])}
    errors = []

    for it in chk.get("expected", []):
        if it["kind"] == "edge":
            e = edges.get((it["from"], it["to"]))
            if not e:
                errors.append(f"{it['id']} 缺边 {it['from']}->{it['to']}（{it['note']}）")
            elif e.get("diagnosis") not in it["diagnosis"]:
                errors.append(
                    f"{it['id']} 边 {it['from']}->{it['to']} diagnosis={e.get('diagnosis')!r}，期望 {it['diagnosis']}（{it['note']}）")
        elif it["kind"] == "node":
            n = nodes.get(it["node"])
            if not n:
                errors.append(f"{it['id']} 缺节点 {it['node']}（{it['note']}）")
            elif n.get("diagnosis") not in it["diagnosis"]:
                errors.append(
                    f"{it['id']} 节点 {it['node']} diagnosis={n.get('diagnosis')!r}，期望 {it['diagnosis']}（{it['note']}）")
        else:
            errors.append(f"{it['id']} 未知 kind {it['kind']}")

    for c in chk.get("cites", []):
        n = nodes.get(c["node"])
        if not n:
            errors.append(f"{c['node']} 缺节点，无法校验引注")
            continue
        got = (n.get("source_anchor") or {}).get("cite_id")
        if got != c["expect"]:
            errors.append(f"{c['node']} cite_id={got!r}，期望 {c['expect']!r}（{c['note']}）")

    if errors:
        print(f"FAIL {args.graph}")
        for e in errors:
            print("  -", e)
        return 1
    print(f"PASS {args.graph}: {len(chk.get('expected', []))} 处问题全部标记，引注全部正确")
    return 0


if __name__ == "__main__":
    sys.exit(main())
