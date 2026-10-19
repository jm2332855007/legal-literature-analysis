#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict claim-graph gate (atomic propositions + citation anchors).

Usage:
  python validate_claim_graph.py graph.json [more.json]
Exit code 0 only if every graph passes all rules.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

CITATION_NODE_TYPES = (
    "evidence_data", "evidence_case", "evidence_statute",
    "evidence_archive", "evidence_doctrine",
    "counter_position", "literature_position",
)


def load_json(path, base=BASE):
    p = path if os.path.isabs(path) else os.path.join(base, path)
    return json.load(open(p, encoding="utf-8"))


def check(g):
    errors = []
    warnings = []
    nodes = {n.get("id"): n for n in g.get("nodes", [])}
    edges = g.get("edges", [])
    types = [n.get("type") for n in nodes.values()]
    cid = g.get("central_claim_id")

    if g.get("fully_read") is not True:
        errors.append("fully_read != true")
    if not g.get("problem") and "problem" not in types:
        errors.append("missing problem node")
    if cid not in nodes:
        errors.append("central_claim_id missing")
    elif nodes[cid].get("type") != "claim":
        errors.append("central node is not claim")
    if sum(1 for t in types if t == "premise") < 2:
        errors.append("need >=2 premise nodes")
    if not any(str(t).startswith("evidence_") for t in types):
        errors.append("need >=1 evidence_* node")
    if not any(t in ("counter_position", "literature_position") for t in types):
        errors.append("need counter_position or literature_position")
    if "normative_conclusion" not in types:
        errors.append("need normative_conclusion")
    if len(edges) < 5:
        errors.append("need >=5 edges")

    used = set()
    for e in edges:
        used.add(e.get("from")); used.add(e.get("to"))
        if e.get("from") not in nodes or e.get("to") not in nodes:
            errors.append(f"edge references missing node: {e}")
        w = e.get("warrant") or ""
        if not w:
            errors.append(f"edge lacks warrant: {e.get('from')}->{e.get('to')}")
        elif len(w.strip()) < 6:
            errors.append(f"warrant 太短（禁止只写'支持'类两字）：{e.get('from')}->{e.get('to')} = {w!r}")
        elif w.strip() == e.get("relation"):
            errors.append(f"warrant 与 relation 同名（复述关系名）：{e.get('from')}->{e.get('to')}")
        else:
            # warrant 复述/乞题：与两端节点 text 近乎相同
            f_t = nodes.get(e.get("from"), {}).get("text", "")
            t_t = nodes.get(e.get("to"), {}).get("text", "")
            if _lcs_ratio(w, f_t) >= 0.8 or _lcs_ratio(w, t_t) >= 0.8:
                errors.append(f"warrant 复述/乞题（与节点 text 重合≥80%）：{e.get('from')}->{e.get('to')}")
        if e.get("relation") not in {"supports", "attacks", "qualifies", "derives", "explains", "motivates", "constitutes", "grounds", "responds", "illustrates", "balancing", "subsumption", "analogy", "a_contrario", "a_fortiori"}:
            errors.append(f"bad relation: {e.get('relation')}")
    if set(nodes) - used:
        isolated = set(nodes) - used
        # 诊断图谱允许"有意标记为孤立"的节点存在（这是要暴露的问题）；未标注的孤立节点仍 FAIL
        bad = [nid for nid in isolated if nodes[nid].get("diagnosis") != "isolated"]
        if bad:
            errors.append(f"isolated nodes (未标注 diagnosis=isolated): {sorted(bad)}")

    # counter 必须 attack/qualify claim 或 premise；literature 可只作背景/支撑，不强制攻击
    targets = {nid for nid, n in nodes.items() if n.get("type") in ("claim", "premise")}
    ok_attack = False
    for e in edges:
        src = nodes.get(e.get("from"), {})
        if src.get("type") == "counter_position" and e.get("relation") in ("attacks", "qualifies") and e.get("to") in targets:
            ok_attack = True
    if not ok_attack:
        errors.append("no counter_position attacks or qualifies a claim/premise")

    # citation ids: evidence/counter/literature must carry a cite_id
    cit_ids = _load_cite_ids(g)
    for nid, n in nodes.items():
        if n.get("type") in CITATION_NODE_TYPES:
            cidn = (n.get("source_anchor") or {}).get("cite_id")
            if not cidn:
                errors.append(f"node {nid} ({n.get('type')}) missing source_anchor.cite_id")
            elif cit_ids is not None and cidn not in cit_ids:
                errors.append(f"node {nid} cite_id not found in citations: {cidn}")
            # 归属铁律：被引者立场（反方/文献）不得挂 cite_self，须挂被引者文献（防"张冠李戴"学术不端）
            if n.get("type") in ("counter_position", "literature_position") and cidn == "cite_self":
                errors.append(f"node {nid} ({n.get('type')}) 被引者立场错挂 cite_self——须改挂 references[].id（被引者归属）")

    # anchors + quote membership
    src_cache = {}
    for n in nodes.values():
        a = n.get("source_anchor") or {}
        if not all(k in a for k in ("page", "paragraph_id", "quote")):
            errors.append(f"node {n.get('id')} missing source_anchor")
            continue
        idx = g["source"]["paragraph_index"]
        if idx not in src_cache:
            src_cache[idx] = load_json(idx)
        match = [p for p in src_cache[idx]["paragraphs"] if p["pid"] == a["paragraph_id"]]
        if not match:
            errors.append(f"node {n.get('id')} paragraph_id not found: {a['paragraph_id']}")
        elif a["quote"] not in match[0]["text"]:
            errors.append(f"node {n.get('id')} quote not in paragraph {a['paragraph_id']}")
        elif int(a["page"]) != int(match[0]["page"]):
            errors.append(f"node {n.get('id')} page mismatch {a['page']} != {match[0]['page']}")
        # 防泄漏铁律（标准 §出处=命题+引注）：text 是抽象命题，不得近乎照抄 quote
        ratio = _lcs_ratio(n.get("text", ""), a["quote"])
        q, t = a["quote"], n.get("text", "")
        contained = (len(q) >= 8 and q in t) or (len(t) >= 8 and t in q)
        if ratio >= 0.75 or contained:
            errors.append(f"node {n.get('id')} text 近乎照抄 quote（防泄漏铁律，重合 {ratio:.0%}）")
        # 防泄漏加固：text 也不得照抄所在段落正文（即使 quote 是另一句）
        ptext = match[0]["text"]
        ratio_p = _lcs_ratio(t, ptext)
        if ratio_p >= 0.8 and ratio < 0.75:
            errors.append(f"node {n.get('id')} text 近乎照抄段落正文（与 {a['paragraph_id']} 重合 {ratio_p:.0%}，绕过 quote 检查）")
        pt = n.get("proposition_type")
        if pt and pt not in ("descriptive", "normative", "definitive", "causal", "evaluative", "interpretive", "balancing"):
            errors.append(f"node {n.get('id')} bad proposition_type: {pt}")
        stance = n.get("stance")
        if stance and stance not in ("通说", "少数说", "背景文献", "反方", "争议"):
            errors.append(f"node {n.get('id')} bad stance: {stance}")

    # supports 占比警告（supports 泛滥 = 论证没拆到位，万金油掩盖了法学论证形式）
    n_supports = sum(1 for e in edges if e.get("relation") == "supports")
    if edges and n_supports / len(edges) > 0.6:
        warnings.append(f"supports 占 {n_supports}/{len(edges)}（>60%），论证可能没拆到位——考虑用 balancing/subsumption/analogy/a_contrario/a_fortiori 替换万金油 supports")

    return errors, warnings


def _load_cite_ids(g):
    """Return the set of known cite ids, or None if citations file is absent."""
    cit_path = (g.get("source") or {}).get("citations")
    if not cit_path:
        return None
    try:
        data = load_json(cit_path)
    except Exception:
        return None
    ids = set()
    if data.get("cite_self"):
        ids.add(data["cite_self"].get("id", "cite_self"))
    for r in data.get("references", []):
        ids.add(r.get("id"))
    return ids


def _lcs_ratio(a, b):
    """text 与 quote 的最长公共子串占较短者比例（防泄漏判别）。"""
    a, b = (a or ""), (b or "")
    if not a or not b:
        return 0.0
    m, n = len(a), len(b)
    if m > n:
        a, b, m, n = b, a, n, m
    prev = [0] * (n + 1)
    best = 0
    for i in range(1, m + 1):
        cur = [0] * (n + 1)
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best / m


def main():
    paths = sys.argv[1:]
    if not paths:
        print("usage: validate_claim_graph.py graph.json [...]")
        return 2
    failed = 0
    for path in paths:
        g = json.load(open(path, encoding="utf-8"))
        errs, warns = check(g)
        print(("PASS " if not errs else "FAIL ") + path)
        for e in errs:
            print("  -", e)
        for w in warns:
            print("  ! warning:", w)
        failed += bool(errs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
