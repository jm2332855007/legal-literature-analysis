#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render strict claim graphs as PNG (graph + node/edge reference tables)."""
import argparse
import glob
import json
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
OUT = os.path.join(BASE, "visuals")

TYPE_LABEL = {
    "problem": "问题", "premise": "前提", "claim": "中心命题",
    "evidence_data": "数据证据", "evidence_case": "案例证据",
    "evidence_statute": "法条证据", "evidence_archive": "史料证据",
    "evidence_doctrine": "学说证据", "counter_position": "反方",
    "literature_position": "文献立场", "response": "回应",
    "normative_conclusion": "规范结论", "qualifier": "限定",
}
TYPE_COLOR = {
    "problem": "#f4a261", "premise": "#8ecae6", "claim": "#e63946",
    "evidence_data": "#95d5b2", "evidence_case": "#95d5b2",
    "evidence_statute": "#95d5b2", "evidence_archive": "#95d5b2",
    "evidence_doctrine": "#95d5b2", "counter_position": "#cdb4db",
    "literature_position": "#b5179e", "response": "#adb5bd",
    "normative_conclusion": "#ffb703", "qualifier": "#adb5bd",
}
REL_CN = {
    "supports": "支持", "attacks": "攻击", "qualifies": "限定",
    "derives": "推出", "explains": "解释", "motivates": "动机",
    "constitutes": "构成", "grounds": "根据", "responds": "回应",
}
REL_COLOR = {
    "supports": "#6c757d", "attacks": "#d00000", "qualifies": "#e85d04",
    "derives": "#1d3557", "explains": "#457b9d", "motivates": "#6a4c93",
    "constitutes": "#2a9d8f", "grounds": "#8d6e63", "responds": "#495057",
}


def positions(nodes):
    groups = {"problem": [], "evidence": [], "premise": [], "lit": [], "claim": [], "norm": [], "other": []}
    for n in nodes:
        t = n["type"]
        if t == "problem":
            groups["problem"].append(n)
        elif str(t).startswith("evidence_"):
            groups["evidence"].append(n)
        elif t == "premise":
            groups["premise"].append(n)
        elif t in ("counter_position", "literature_position"):
            groups["lit"].append(n)
        elif t == "claim":
            groups["claim"].append(n)
        elif t == "normative_conclusion":
            groups["norm"].append(n)
        else:
            groups["other"].append(n)
    pos = {}
    for i, n in enumerate(groups["problem"]):
        pos[n["id"]] = (0.0, 3.2)
    for i, n in enumerate(groups["evidence"]):
        pos[n["id"]] = (2.2, 1.0 + i * 1.5)
    for i, n in enumerate(groups["premise"]):
        pos[n["id"]] = (4.2, 1.2 + i * 1.3)
    for i, n in enumerate(groups["lit"]):
        pos[n["id"]] = (6.2, 7.4 - i * 1.0)
    claims = sorted(groups["claim"], key=lambda n: 0 if n["id"] == "C1" else 1)
    for i, n in enumerate(claims):
        pos[n["id"]] = (7.6, 3.2) if i == 0 else (7.6, 4.7)
    for i, n in enumerate(groups["norm"]):
        pos[n["id"]] = (9.4, 1.2 + i * 1.3)
    for i, n in enumerate(groups["other"]):
        pos[n["id"]] = (7.6, 5.6 - i * 1.0)
    return pos


def render_one(path, out_png):
    g = json.load(open(path, encoding="utf-8"))
    nodes = g["nodes"]
    edges = g["edges"]
    pos = positions(nodes)
    fig = plt.figure(figsize=(18, 14), dpi=180)
    ax = fig.add_axes([0.03, 0.33, 0.94, 0.60])
    ax.set_xlim(-1.2, 10.5)
    ax.set_ylim(0, 8.5)
    ax.axis("off")
    ax.set_title(f"{g['id']} 严格 claim graph｜{g['title']}", fontsize=15, fontweight="bold", pad=12)
    note = ("读图：Q=问题，P=前提，E=证据，L=文献/反方，C=中心命题，N=规范结论。\n"
            "边：灰实线=支持，红虚线=攻击，橙虚线=限定，深蓝=推出；节点下方附页码/段落，\n"
            "每条边成立的理由（warrant）见底部右栏。")
    ax.text(-1.15, 8.25, note, fontsize=8.2, family="Microsoft YaHei", va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f8f9fa", edgecolor="#ced4da"),
            zorder=5)

    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"])
    for e in edges:
        G.add_edge(e["from"], e["to"])

    for n in nodes:
        x, y = pos[n["id"]]
        color = TYPE_COLOR.get(n["type"], "#dee2e6")
        label = n["id"] + "\n" + TYPE_LABEL.get(n["type"], n["type"])
        diag = n.get("diagnosis", "")
        ec = "#343a40"; lw = 1.1; ls = "solid"
        if diag == "isolated":
            ec = "#d00000"; ls = "dashed"; lw = 2.2
            label += "\n[孤立]"
        elif diag == "evidence_insufficient":
            ec = "#e85d04"; lw = 2.2
            label += "\n[证据缺]"
        ax.text(x, y, label, ha="center", va="center", fontsize=10, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.45", facecolor=color, edgecolor=ec, linewidth=lw, linestyle=ls),
                zorder=6)

    # group edges by relation for line styles
    for e in edges:
        a, b = e["from"], e["to"]
        if a not in pos or b not in pos:
            continue
        rel = e["relation"]
        color = REL_COLOR.get(rel, "#6c757d")
        diag = e.get("diagnosis", "")
        ls = "solid"
        if diag in ("leap", "gap"):
            color = "#d00000"; ls = (0, (4, 2))
        ax.annotate("", xy=pos[b], xytext=pos[a],
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6, linestyle=ls,
                                    shrinkA=32, shrinkB=32,
                                    connectionstyle="arc3,rad=0"),
                    zorder=2)
        frac = 0.42
        mx = pos[a][0] + (pos[b][0] - pos[a][0]) * frac
        my = pos[a][1] + (pos[b][1] - pos[a][1]) * frac
        # small perpendicular offset so label sits beside the line, not far from it
        dx = pos[b][0] - pos[a][0]
        dy = pos[b][1] - pos[a][1]
        norm = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        off = 0.18
        rel_label = REL_CN.get(rel, rel)
        if diag == "leap":
            rel_label += "[跳步]"
        elif diag == "gap":
            rel_label += "[断裂]"
        ax.text(mx - dy / norm * off, my + dx / norm * off, rel_label,
                fontsize=8, color=color, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.10", fc="white", ec="none", alpha=0.9), zorder=4)

    # bottom left: nodes
    axn = fig.add_axes([0.02, 0.02, 0.47, 0.28])
    axn.axis("off")
    node_lines = ["【节点｜锚点】"]
    for n in nodes:
        a = n["source_anchor"]
        head = f"{n['id']} [{TYPE_LABEL.get(n['type'], n['type'])}] p{a['page']} {a['paragraph_id']}"
        if n.get("diagnosis"):
            head += f" [{n['diagnosis']}]"
        body = textwrap.fill(n["text"], 34)
        node_lines.append(head)
        node_lines.append("  " + body)
    axn.text(0, 1, "\n".join(node_lines), va="top", ha="left", fontsize=7.6, family="Microsoft YaHei",
             linespacing=1.35)

    # bottom right: edges + warrants
    axe = fig.add_axes([0.51, 0.02, 0.47, 0.28])
    axe.axis("off")
    edge_lines = ["【边｜warrant】"]
    for e in edges:
        head = f"{e['from']} → {e['to']}  [{REL_CN.get(e['relation'], e['relation'])}]"
        if e.get("diagnosis"):
            head += f" [{e['diagnosis']}]"
        body = textwrap.fill(e["warrant"], 36)
        edge_lines.append(head)
        edge_lines.append("  " + body)
    axe.text(0, 1, "\n".join(edge_lines), va="top", ha="left", fontsize=7.4, family="Microsoft YaHei",
             linespacing=1.35)

    fig.text(0.02, 0.965, "图例：橙=问题 蓝=前提 绿=证据 紫=文献/反方 红=中心命题 黄=规范结论；红虚线=攻击，橙虚线=限定，灰实线=支持",
             fontsize=8.5, family="Microsoft YaHei", color="#495057")
    fig.savefig(out_png, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="")
    ap.add_argument("--file", default="")
    ap.add_argument("--out-dir", default="", help="输出目录（默认技能内 visuals/，建议传 out 目录以保持安装目录只读）")
    args = ap.parse_args()
    out_dir = os.path.abspath(args.out_dir) if args.out_dir else OUT
    os.makedirs(out_dir, exist_ok=True)
    if args.file:
        paths = [args.file]
    elif args.id:
        paths = [os.path.join(BASE, "graphs", args.id + ".json")]
    else:
        paths = sorted(glob.glob(os.path.join(BASE, "graphs", "laws-*.json")))
    for p in paths:
        g = json.load(open(p, encoding="utf-8"))
        render_one(p, os.path.join(out_dir, g["id"] + ".png"))


if __name__ == "__main__":
    main()
