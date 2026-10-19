#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Mermaid flowchart from a strict claim graph (auto-layout, no overlap).

Why: matplotlib manual positioning overlaps once a graph grows past ~15 nodes
(fixed columns + crossing edges + text labels) — and all normative nodes were
placed at one coordinate. Mermaid's dagre layout auto-places nodes and routes
edges, so claim graphs stay readable as a 思维导图/线索图 that renders in
VS Code / Typora / GitHub / mermaid.live.

Usage:
  python mermaid_claim_graph.py --file graphs/anquan.claim-graph.json [--out out.mmd] [--md out.md]

Outputs:
  <graph>.mmd   — Mermaid source (flowchart LR)
  <graph>.md    — fenced ```mermaid block, renders in any Mermaid-capable viewer
"""
import argparse
import json
import os

TYPE_CN = {
    "problem": "问题", "premise": "前提", "claim": "中心命题",
    "evidence_data": "数据证据", "evidence_case": "案例证据",
    "evidence_statute": "法条证据", "evidence_archive": "史料证据",
    "evidence_doctrine": "学说证据", "counter_position": "反方",
    "literature_position": "文献", "response": "回应",
    "normative_conclusion": "规范结论", "qualifier": "限定",
}
REL_CN = {
    "supports": "支持", "attacks": "攻击", "qualifies": "限定",
    "derives": "推出", "explains": "说明", "motivates": "动机",
    "constitutes": "构成", "grounds": "根据", "responds": "回应",
    "illustrates": "例证", "balancing": "权衡", "subsumption": "涵摄",
    "analogy": "类推", "a_contrario": "反面论证", "a_fortiori": "当然论证",
}
ARROW = {
    "supports": "-->", "attacks": "-.->", "qualifies": "-.->",
    "derives": "==>", "explains": "-->", "motivates": "-->",
    "constitutes": "==>", "grounds": "-->", "responds": "-->",
    "illustrates": "-->", "balancing": "-.->", "subsumption": "==>",
    "analogy": "-->", "a_contrario": "-.->", "a_fortiori": "-->",
}

# 类型 → (基础类名, 基础样式)。诊断变体在基础样式后追加 stroke 覆盖，
# 每种组合单独生成 classDef，避免多类合并时 fill 被默认值冲掉。
TYPE_STYLE = {
    "problem": ("clsProblem", "fill:#f4a261,stroke:#343a40,color:#000"),
    "premise": ("clsPremise", "fill:#8ecae6,stroke:#343a40,color:#000"),
    "claim": ("clsClaim", "fill:#e63946,stroke:#343a40,color:#fff"),
    "evidence": ("clsEvidence", "fill:#95d5b2,stroke:#343a40,color:#000"),
    "counter": ("clsCounter", "fill:#cdb4db,stroke:#343a40,color:#000"),
    "norm": ("clsNorm", "fill:#ffb703,stroke:#343a40,color:#000"),
    "other": ("clsOther", "fill:#dee2e6,stroke:#343a40,color:#000"),
}
VARIANT = {
    "": ("", ""),
    "isolated": ("Isolated", ",stroke:#d00000,stroke-width:3px,stroke-dasharray:6 4"),
    "evidence_insufficient": ("EvidenceGap", ",stroke:#e85d04,stroke-width:3px"),
}
DIAG_TAG = {"isolated": "【孤立】", "evidence_insufficient": "【证据缺】"}


def esc(t):
    """Escape chars that break Mermaid labels inside double quotes."""
    t = str(t)
    for a, b in (('"', "#quot;"), ("<", "#lt;"), (">", "#gt;"), ("|", "#124;")):
        t = t.replace(a, b)
    return t


def short(t, n=40):
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[:n] + "…"


def node_label(n):
    typ = TYPE_CN.get(n["type"], n["type"])
    pid = (n.get("source_anchor") or {}).get("paragraph_id", "")
    dig = DIAG_TAG.get(n.get("diagnosis", ""), "")
    parts = [f"{n['id']} {typ}{dig}", short(n.get("text", "")), f"段{pid}" if pid else ""]
    return "<br/>".join(esc(p) for p in parts if p)


def rel_label(e):
    rel = REL_CN.get(e["relation"], e["relation"])
    if e.get("diagnosis") == "leap":
        rel += "（跳步）"
    elif e.get("diagnosis") == "gap":
        rel += "（断裂）"
    return rel


def type_key(t):
    if str(t).startswith("evidence_"):
        return "evidence"
    return {
        "problem": "problem", "premise": "premise", "claim": "claim",
        "counter_position": "counter", "literature_position": "counter",
        "normative_conclusion": "norm", "response": "other",
    }.get(t, "other")


def build(g):
    nodes = g["nodes"]
    edges = g["edges"]
    lines = ["flowchart LR"]
    used = {}  # class name -> style
    classes = {}  # node id -> class name
    for n in nodes:
        base, style = TYPE_STYLE[type_key(n["type"])]
        suf, extra = VARIANT.get(n.get("diagnosis", ""), ("", ""))
        cls = base + suf
        used[cls] = style + extra
        if n["type"] == "problem":
            lines.append(f'  {n["id"]}(["{node_label(n)}"])')
        elif n["type"] == "claim":
            lines.append(f'  {n["id"]}[["{node_label(n)}"]]')
        else:
            lines.append(f'  {n["id"]}["{node_label(n)}"]')
        classes.setdefault(n["id"], cls)
    for e in edges:
        arrow = ARROW.get(e["relation"], "-->")
        lines.append(f'  {e["from"]} {arrow}|{esc(rel_label(e))}| {e["to"]}')
    for cls, style in used.items():
        lines.append(f"  classDef {cls} {style}")
    for nid, cls in classes.items():
        lines.append(f"  class {nid} {cls}")
    for i, e in enumerate(edges):
        if e.get("diagnosis") in ("leap", "gap"):
            lines.append(f"  linkStyle {i} stroke:#d00000,stroke-width:2.5px,stroke-dasharray:6 4")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="claim-graph json")
    ap.add_argument("--out", default="", help=".mmd output path")
    ap.add_argument("--md", default="", help="optional .md with fenced mermaid block")
    args = ap.parse_args()
    g = json.load(open(args.file, encoding="utf-8"))
    mmd = build(g)
    out = args.out or (os.path.splitext(args.file)[0] + ".mmd")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(mmd + "\n")
    print("wrote", out)
    if args.md:
        title = g.get("title", g.get("id", ""))
        with open(args.md, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# {title} — 论证图谱（Mermaid）\n\n```mermaid\n{mmd}\n```\n")
        print("wrote", args.md)


if __name__ == "__main__":
    main()
