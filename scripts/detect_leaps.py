#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detect candidate argument problems from an article (recall-oriented first pass).

Four detectors, all "candidate + reason", never a verdict:
  1. leap               — 换言/反证 标记处"跳步"（后句引入新概念、前文无引注锚点）
  2. type_leap          — 描述性前提 无规范依据 却直接 supports 规范性命题（事实→规范缺桥；需 --graph + proposition_type）
  3. no_anchor_normative — 段内有"应当/必须/不得…"但整段与上段均无 [n] 引注（证据不足嫌疑）
  4. isolated_section   — 某小节下锚定的节点全都没进任何论证边（孤立嫌疑；需 --graph）

Outputs candidates.json; each candidate carries pid, score, reasons, suggested_target
（exact pid→node，无则同小节节点 sec:，再无 unmapped）。

Backtest（--backtest issues.json）：类型匹配 + 同小节归因；detectable_by 为空 = 结构性/语义型，声明为不可召回。

Usage:
  python detect_leaps.py --paragraphs <paragraphs.json> [--graph <graph.json>] [--issues <issues.json>] [--out out.json]
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 义项 → 跳步基础分。只保留换言/反证（推论/因果太常见，误报高，已剔除）。
LEAP_SENSE = {"换言": 2, "反证": 2}
# 领域词（真正的"跨域跳步"词，如概念转译/类推比附）。换言/反证义项已剔除——
# 多篇探针显示"即/事实上/实际上/而非/而是"在已发表 CLSCI 论文上是正常学术连接词，
# precision≈0，不是跳步信号。
EXTRA_LEAP = {"转译": 3, "概念转译": 3, "类推": 2, "比附": 2, "拟制": 2}
NEW_TERM = ("命名", "称为", "所谓", "概念", "构造", "范式", "理论", "原则", "机制",
            "命题", "本文认为", "本文主张", "由此可知", "即")
NORM = re.compile(r"应当|必须|不得|不应|须|宜")
HEADING = re.compile(r"^(第[一二三四五六七八九十]+章|（[一二三四五六七八九十]+）|[一二三四五六七八九十]+、|参考文献|注释)")
CITE = re.compile(r"\[\d+\]")
STATUTE = re.compile(r"《.{2,20}》.{0,20}第.{1,6}条|第.{1,6}条")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def markers_from_senses(path):
    """换言/反证义项 → [(marker, sense, weight)]。

    多篇探针结论：换言/反证是正常学术连接词（即/事实上/实际上/而非/而是…），
    在已发表 CLSCI 论文上 precision≈0，不能当跳步信号。故这里不再从义项库取词，
    跳步信号只用 EXTRA_LEAP 领域词 + 结构检测器 type_leap。
    """
    return []


def pid_nodes(graph):
    m = {}
    for n in graph.get("nodes", []):
        pid = (n.get("source_anchor") or {}).get("paragraph_id")
        if pid:
            m.setdefault(pid, []).append(n["id"])
    return m


def sections(paras):
    sec, cur = {}, "（开头）"
    for p in paras:
        t = p.get("text", "").strip()
        if HEADING.match(t):
            cur = t[:24]
        sec[p.get("pid")] = cur
    return sec


def is_theoretical(paras):
    """引注密度 < 0.5/段 = 无脚注的理论文/笔谈。

    依据（13 篇实测）：过报的 3 篇法理/宪法笔谈短篇引注密度都是 0.00，
    规范论文引注密度 ≥ 1.45。不用法条/案例密度——实证(0162 法条0.12)、
    比较法(0301 法条0.09)、法律史(0038 法条0.00)都法条少但引注多、是规范论文。
    """
    text = "\n".join(p.get("text", "") for p in paras)
    return len(CITE.findall(text)) < 0.5 * max(len(paras), 1)


def detect(paras, graph, marker_senses):
    by_pid = {p["pid"]: p for p in paras}
    pids = [p["pid"] for p in paras]
    idx = {pid: i for i, pid in enumerate(pids)}
    secmap = sections(paras)
    out = []

    def add(detector, pid, score, reasons, marker="", sense=""):
        n = by_pid[pid]
        out.append({"detector": detector, "pid": pid, "marker": marker, "sense": sense,
                    "score": score, "reasons": reasons, "context": n["text"][:160]})

    # ---- 1. leap（换言/反证 + 领域词） ----
    for pid in pids:
        text = by_pid[pid]["text"]
        # 先收集各标记的首个命中跨度，再包含去重（"概念转译"⊃"转译"只留长的）
        raw = []
        for marker, sense, w in marker_senses:
            start = text.find(marker)
            if start >= 0:
                raw.append((start, start + len(marker), marker, sense, w))
        raw.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        kept = []
        for m in raw:
            if any(m[0] >= k[0] and m[1] <= k[1] for k in kept):
                continue
            kept.append(m)
        seen = set()
        for start, end, marker, sense, w in kept:
            if marker in seen:
                continue
            nxt = text[end] if end < len(text) else "。"
            prev = text[start - 1] if start > 0 else "。"
            tail = text[end:end + 40]
            if marker == "其实" and nxt in "现施质际中他":
                continue
            # 反证标记（而非/而是/恰恰相反）若只是范围/定义澄清、不引入新概念或引号术语 → 跳过（误报）
            if sense == "反证" and not any(t in tail for t in NEW_TERM) and "“" not in tail:
                continue
            score, reasons = w, [f"标记「{marker}」（{sense}）"]
            if nxt in "，。；：！？、）" or prev in "。！？\n":
                score += 1; reasons.append("处于句首/句读处（典型跳步姿态）")
            if any(t in tail for t in NEW_TERM):
                score += 2; reasons.append("后句引入新概念/新命题")
            if "“" in tail and "”" in tail:
                score += 1; reasons.append("后句引入带引号的新术语")
            prevtext = text[:start] + (by_pid[pids[idx[pid] - 1]]["text"] if idx[pid] > 0 else "")
            if not CITE.search(prevtext[-200:]):
                score += 1; reasons.append("前文无 [n] 引注锚点")
            add("leap", pid, score, reasons, marker, sense)
            seen.add(marker)

    # ---- 2. type_leap（诊断型描述前提 → 规范性命题，事实→规范缺桥） ----
    if graph:
        nodes = {n["id"]: n for n in graph.get("nodes", [])}
        for e in graph.get("edges", []):
            if e.get("relation") != "supports":
                continue
            a, b = nodes.get(e.get("from")), nodes.get(e.get("to"))
            if not a or not b or a.get("type") != "premise" or b.get("type") != "claim":
                continue
            at, bt = a.get("proposition_type"), b.get("proposition_type")
            if at != "descriptive" or bt not in ("normative", "definitive", "evaluative"):
                continue
            apid = (a.get("source_anchor") or {}).get("paragraph_id")
            src = by_pid.get(apid, {}).get("text", "") if apid else a.get("text", "")
            # 有法条/规范词 = 有规范依据，不算跳步（只看这些，不看引注——引注可能是被批的反方）
            if STATUTE.search(src) or re.search(r"应当|必须|须", src):
                continue
            # 诊断型标记：前提是"诊断学说/立场之失灵"，却直接推出规范性命题
            if not re.search(r"失灵|困境|质疑|分歧|争论|众说|反思|症结|缺陷|批判|检讨|困境", src):
                continue
            if apid:
                add("type_leap", apid, 6,
                    [f"诊断型描述前提 {a['id']}（失灵/困境/质疑…）无规范依据却直接支持规范性命题 {b['id']}（事实→规范缺桥）"],
                    marker=f"{a['id']}->{b['id']}")

    # ---- 3. no_anchor_normative ----
    for i, pid in enumerate(pids):
        text = by_pid[pid]["text"]
        if not NORM.search(text):
            continue
        prev_text = by_pid[pids[i - 1]]["text"] if i > 0 else ""
        if CITE.search(text) or CITE.search(prev_text):
            continue
        score, reasons = 5, ["段内有应当/必须/不得类规范句", "本段与上段均无 [n] 引注"]
        if re.search(r"评估|分级|审查|制度|义务", text):
            score += 1; reasons.append("指向具体制度/义务（却无实证支撑）")
        add("no_anchor_normative", pid, score, reasons)

    # ---- 4. isolated_section ----
    if graph:
        used = set()
        for e in graph.get("edges", []):
            used.add(e["from"]); used.add(e["to"])
        bysec = {}
        for n in graph.get("nodes", []):
            pid = (n.get("source_anchor") or {}).get("paragraph_id")
            if not pid:
                continue
            bysec.setdefault(secmap.get(pid, "?"), []).append((n["id"], pid))
        for label, items in bysec.items():
            if items and all((nid not in used) for nid, _ in items):
                add("isolated_section", items[0][1], 6,
                    [f"小节「{label}」下节点 {[n for n,_ in items]} 未进入任何论证边"])

    # ---- 排序 + 映射（exact pid → 同小节节点 sec: → unmapped） ----
    m = pid_nodes(graph) if graph else {}
    node_section = {}
    if graph:
        for n in graph.get("nodes", []):
            pid = (n.get("source_anchor") or {}).get("paragraph_id")
            if pid:
                node_section[n["id"]] = secmap.get(pid, "?")
    for c in out:
        exact = m.get(c["pid"], [])
        if exact:
            c["suggested_target"] = ",".join("node:" + t for t in exact)
        else:
            sec = secmap.get(c["pid"])
            sn = [nid for nid, s in node_section.items() if s == sec and sec not in ("（开头）", "?")]
            c["suggested_target"] = (",".join("sec:" + t for t in sn)) if sn else "unmapped"
    out.sort(key=lambda c: -c["score"])
    return out


def backtest(cands, graph, issues, paras):
    """类型匹配 + 同小节归因。detectable_by 空 = 声明不可召回。"""
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    pid_of = lambda nid: (nodes.get(nid, {}).get("source_anchor") or {}).get("paragraph_id")
    secmap = sections(paras)

    def sec_of_node(nid):
        pid = pid_of(nid)
        return secmap.get(pid, "?")

    hits, sect, misses, undetectable = [], [], [], []
    for it in issues.get("expected", []):
        allowed = it.get("detectable_by") or []
        if not allowed:
            undetectable.append({"id": it["id"], "note": it["note"]})
            continue
        nids = [it["node"]] if it["kind"] == "node" else [it["from"], it["to"]]
        t_pids = {pid_of(n) for n in nids if pid_of(n)}
        t_secs = {sec_of_node(n) for n in nids if sec_of_node(n) not in ("（开头）", "?")}
        strict = any(c["pid"] in t_pids and c["detector"] in allowed for c in cands)
        if strict:
            hits.append(it["id"]); continue
        sect_m = [c for c in cands
                  if c["detector"] in allowed and secmap.get(c["pid"]) in t_secs]
        if sect_m:
            sect.append({"id": it["id"], "cand_pid": sect_m[0]["pid"], "section": secmap.get(sect_m[0]["pid"])})
        else:
            misses.append({"id": it["id"], "note": it["note"], "pids": sorted(t_pids), "expect": allowed})
    return hits, sect, misses, undetectable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paragraphs", required=True)
    ap.add_argument("--graph", default="")
    ap.add_argument("--senses", default=os.path.join(ROOT, "assets", "discourse-marker-senses.json"))
    ap.add_argument("--issues", default="", help="issues.json for backtest")
    ap.add_argument("--out", default="")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--theoretical", default="auto", choices=["auto", "yes", "no"],
                    help="理论文/笔谈门控：auto=按引注密度自动判；yes/no 强制。理论文抑制 type_leap/no_anchor（无引注不是缺陷）")
    args = ap.parse_args()

    paras = load(args.paragraphs)
    paras = paras.get("paragraphs", paras if isinstance(paras, list) else [])
    graph = load(args.graph) if args.graph and os.path.exists(args.graph) else None
    ms = markers_from_senses(args.senses) + [(k, "领域词", v) for k, v in EXTRA_LEAP.items()]
    cands = detect(paras, graph, ms)

    # 理论文门控：无脚注的理论文/笔谈，type_leap/no_anchor 的"无引注/无法条"不是缺陷信号，抑制
    theo = args.theoretical == "yes" or (args.theoretical == "auto" and is_theoretical(paras))
    if theo:
        cite_n = len(CITE.findall("\n".join(p.get("text", "") for p in paras)))
        print(f"理论文门控生效：引注 {cite_n}/{len(paras)} 段 < 0.5/段，抑制 type_leap / no_anchor")
        cands = [c for c in cands if c["detector"] not in ("type_leap", "no_anchor_normative")]

    out = args.out or (os.path.splitext(args.paragraphs)[0] + ".candidates.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"total": len(cands), "top": args.top, "theoretical": theo,
                   "candidates": cands[:args.top],
                   "folded": len(cands) - args.top if len(cands) > args.top else 0},
                  f, ensure_ascii=False, indent=2)

    print(f"wrote {out}: total {len(cands)}, top {min(args.top, len(cands))}")
    for c in cands[:12]:
        print(f"  [{c['score']:>2}] {c['pid']} {c['detector']:<20} {c['suggested_target']:<20} {c['reasons'][0]}")

    if args.issues and graph:
        issues = load(args.issues)
        hits, sect, misses, undetectable = backtest(cands, graph, issues, paras)
        detectable = len(hits) + len(sect) + len(misses)
        print(f"\nbacktest（类型匹配 + 同小节）: 严格 {len(hits)}/{detectable}，+同小节 {len(sect)}；"
              + (f"{len(undetectable)} 处声明不可召回" if undetectable else ""))
        print("  hit:", hits)
        for s in sect:
            print(f"  同小节命中: {s['id']} 候选 {s['cand_pid']}（节「{s['section']}」）")
        for m in misses:
            print(f"  miss: {m['id']} 期望 {m['expect']} pid={m['pids']} — {m['note']}")
        for u in undetectable:
            print(f"  不可召回: {u['id']} — {u['note']}")


if __name__ == "__main__":
    main()
