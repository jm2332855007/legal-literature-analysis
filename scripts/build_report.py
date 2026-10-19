#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the single-deliverable anatomy report from a claim graph.

The report is the headline artifact. It fuses:
  - metadata + citations (cite_self / references)
  - readable argument chain (grouped by node type)
  - atomic claim-graph image
  - node -> quote -> page -> footnote table
  - boundary statement

Output is Markdown with real footnote markers [^n]; convert with md_to_docx.py.

Usage:
  python build_report.py --graph out/ao/ao.claim-graph.json --image out/ao/visuals/ao.png --out out/ao/ao.report.md
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

TYPE_CN = {
    "problem": "问题", "premise": "前提", "claim": "中心命题",
    "evidence_data": "数据证据", "evidence_case": "案例证据",
    "evidence_statute": "法条证据", "evidence_archive": "史料证据",
    "evidence_doctrine": "学说证据", "counter_position": "反方立场",
    "literature_position": "文献立场", "response": "回应",
    "normative_conclusion": "规范结论", "qualifier": "限定",
}

GROUP_ORDER = [
    ("问题", ["problem"]),
    ("前提", ["premise"]),
    ("中心命题", ["claim"]),
    ("证据", ["evidence_data", "evidence_case", "evidence_statute", "evidence_archive", "evidence_doctrine"]),
    ("反方与文献", ["counter_position", "literature_position"]),
    ("规范结论", ["normative_conclusion"]),
    ("其他", ["response", "qualifier"]),
]


def load_json(path):
    p = path if os.path.isabs(path) else os.path.join(BASE, path)
    return json.load(open(p, encoding="utf-8"))


def printed_page(page, page_offset):
    try:
        return int(page) + page_offset
    except (TypeError, ValueError):
        return page


def cite_footnote(node, citations, page_offset, quote_type="paraphrase"):
    a = node.get("source_anchor") or {}
    cid = a.get("cite_id")
    if not cid:
        return None
    if cid == "cite_self" or cid == (citations.get("cite_self") or {}).get("id"):
        meta = (citations.get("cite_self") or {}).get("metadata") or {}
        if not meta.get("author") and not meta.get("title"):
            return None  # 缺元数据时不产"空括号"脚注（防 KeyError）
        author = meta.get("author", "")
        title = meta.get("title", "")
        journal = meta.get("journal", "")
        year = meta.get("year", "")
        prefix = "参见" if quote_type == "paraphrase" else ""
        law = prefix + f"{author}：《{title}》，载《{journal}》{year}年"
        if meta.get("issue"):
            law += f"第{meta['issue']}期"
        law += f"，第{printed_page(a.get('page', ''), page_offset)}页。"
        return law
    for r in citations.get("references", []):
        if r.get("id") == cid:
            return r.get("law_footnote") or r.get("gb7714") or r.get("text")
    return None


def render_chain(nodes):
    grouped = {title: [] for title, _ in GROUP_ORDER}
    for n in nodes:
        placed = False
        for title, types in GROUP_ORDER:
            if n.get("type") in types:
                grouped[title].append(n)
                placed = True
                break
        if not placed:
            grouped.setdefault("其他", []).append(n)
    lines = []
    for title, _ in GROUP_ORDER:
        if grouped.get(title):
            lines.append(f"## {title}")
            lines.append("")
            for n in grouped[title]:
                lines.append(f"- **{n['id']}**｜{TYPE_CN.get(n['type'], n['type'])}：{n['text']}")
            lines.append("")
    return "\n".join(lines).rstrip()


def build_report(graph_path, image_path, out_path, reading_dir=""):
    g = load_json(graph_path)
    citations = load_json(g["source"]["citations"])
    paragraphs = load_json(g["source"]["paragraph_index"])

    # page offset: printed page = pdf page + offset
    page_offset = 0
    meta = (citations.get("cite_self") or {}).get("metadata", {})
    try:
        start = int(meta.get("page_start", 0))
        pages = [int(p.get("page", 0)) for p in paragraphs.get("paragraphs", []) if p.get("page")]
        min_pdf = min(pages) if pages else 1
        if start:
            page_offset = start - min_pdf
    except (TypeError, ValueError):
        page_offset = 0

    nodes = g["nodes"]
    footnotes = {}
    fn_defs = []
    next_fn = 1
    for n in nodes:
        fn = cite_footnote(n, citations, page_offset)
        if fn:
            footnotes[n["id"]] = next_fn
            fn_defs.append((next_fn, fn))
            next_fn += 1

    def marker(nid):
        i = footnotes.get(nid)
        return f"[^{i}]" if i else ""

    cite_self = citations.get("cite_self", {})

    out_dir = os.path.dirname(os.path.abspath(out_path))
    img_ref = os.path.relpath(os.path.abspath(image_path), out_dir) if image_path else ""

    L = []
    L.append(f"# {g['title']}：文献解剖报告")
    L.append("")
    L.append(f"> 作者：{meta.get('author', '')}　期刊：{meta.get('journal', '')}　"
             f"{meta.get('year', '')}年{('第' + meta['issue'] + '期') if meta.get('issue') else ''}　"
             f"页：{meta.get('page_start', '')}–{meta.get('page_end', '')}")
    L.append("")
    L.append("## 引注")
    L.append("")
    L.append(f"- 法学脚注（法律出版社《法学引注手册》体例，供页下脚注）：{cite_self.get('law_footnote', '')}")
    L.append(f"- GB/T 7714-2025（参考文献表体例）：{cite_self.get('gb7714', '')}")
    for r in citations.get("references", []):
        gb = r.get("gb7714", "")
        is_gb = any(t in gb for t in ("[M]", "[J]", "[D]", "[EB/OL]", "[C]"))
        L.append(f"- {'参考（GB/T 7714）' if is_gb else '参考（法学引注体例）'}：{gb or r.get('law_footnote') or r.get('text', '')}")
    L.append("")

    L.append(render_chain(nodes))
    L.append("")

    L.append("## 原子论证图")
    L.append("")
    if img_ref:
        L.append(f"![claim graph]({img_ref.replace(os.sep, '/')})")
    else:
        L.append("（无图）")
    L.append("")
    L.append("### 论证图说明")
    L.append("")
    L.append("- **数据范围**：图中节点取自原文中作者自述命题（Q/P/E/N/C 类）与被引第三方立场（L 类，含反方与文献）；连边均以原文表述为据，未引入原文之外的判断。")
    L.append("- **图示含义**：节点底色区分类型（问题/前提/中心命题/证据/反方与文献/规范结论）；实线=支持·根据·动机·说明·回应·例证，虚线=攻击·限定，粗线=推出·构成；红虚线为诊断标记的跳步/断裂。")
    L.append("- **编码说明**（首次出现处）：Q=问题，P=前提，E=证据，L=被引者立场（反方/文献），N=规范结论，C=中心命题；「段P0001」为原文段落锚点编号。判例名等专有名词保留原文并在节点文本中附中文描述；除类型缩写与专有名词外，图中无其他英文标注。")
    L.append("- **关系判断依据**：每条边的 warrant 即该关系的判断依据（原文表述），见节点表与 Mermaid 源码。")
    L.append("")

    L.append("## 节点—原文—引注对照表")
    L.append("")
    L.append("| 节点 | 类型 | 原子命题 | 原文(quote) | 页/段 | 引注 |")
    L.append("|---|---|---|---|---|---|")
    for n in nodes:
        a = n.get("source_anchor") or {}
        pg = printed_page(a.get("page", ""), page_offset)
        L.append(f"| {n['id']} | {TYPE_CN.get(n['type'], n['type'])} | {n['text']} | "
                 f"{a.get('quote', '')} | {pg}/{a.get('paragraph_id', '')} | {marker(n['id'])} |")
    L.append("")
    L.append("> **归属说明**：L 类（反方/文献）节点的 quote 为作者在原文中的**转述句**；引注列指向该观点归属的**被引者文献**（references），不记为作者本人观点。未见原文脚注号者标注「待核」，不得以作者引注冒充被引者出处。")
    L.append("")

    L.append("## 边界声明")
    L.append("")
    L.append("- 命题切分、类型标注与 warrant 为分析性判断；")
    L.append("- `quote` 为原文直接引用，`page/paragraph_id` 为 PDF 锚点；")
    L.append("- 脚注引注由元数据生成，真实性须人工核验；")
    L.append("- 页码为 PDF 页序或印刷页，以实际文件为准。")
    L.append("")

    # 附录：阅读/复现训练任务包（本地有 <id>.reading/ 时自动纳入）
    if reading_dir and os.path.isdir(reading_dir):
        L.append("## 附录：阅读与复现训练任务包")
        L.append("")
        L.append("> 用法：把每个 `.prompt.md` 的提示词交给模型，回答填入「输出槽」即完成一轮；复现训练按第 1→2→3 遍顺序进行。")
        L.append("")
        wanted = ["00_README.md", "03_核心贡献.prompt.md", "04_局限与未决.prompt.md",
                  "05_思维导图.prompt.md", "06_复现训练_第1遍_补结构.md",
                  "07_复现训练_第2遍_补规范依据.md", "08_复现训练_第3遍_补反方回应.md"]
        existing = set(os.listdir(reading_dir))
        for name in wanted:
            if name not in existing:
                continue
            body = open(os.path.join(reading_dir, name), encoding="utf-8").read().strip()
            if name.endswith(".prompt.md") or name.startswith("06_") or name.startswith("07_") or name.startswith("08_"):
                title = name.replace(".prompt.md", "").replace(".md", "")
            else:
                title = "任务包说明" if name == "00_README.md" else name
            L.append(f"### {title}")
            L.append("")
            L.extend(body.splitlines())
            L.append("")
        # 各章精读提示词只列清单，避免正文过长
        chapters = sorted(n for n in existing if n.startswith("02_逐章精读"))
        if chapters:
            L.append("### 逐章精读（按章拆分，见任务包目录）")
            L.append("")
            L.append("| 文件 |")
            L.append("|---|")
            for ch in chapters:
                L.append(f"| {ch} |")
            L.append("")

    if fn_defs:
        # 脚注定义不设标题（pandoc 会转成真页下脚注；加标题会在正文留一个空章节）
        for i, text in fn_defs:
            L.append(f"[^{i}]: {text}")

    open(out_path, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    return {"status": "success", "out": out_path, "footnotes": len(fn_defs), "nodes": len(nodes)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--image", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--reading-dir", default="", help="阅读/复现任务包目录（自动并入附录）")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    print(json.dumps(build_report(args.graph, args.image, args.out, args.reading_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
