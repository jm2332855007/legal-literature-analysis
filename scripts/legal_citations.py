#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build GB/T 7714-2025 and Chinese law-review footnotes from metadata.

Output shape (single source of truth for citations):

{
  "cite_self": {"id": "cite_self", "metadata": {...}, "gb7714": "...", "law_footnote": "...", "quote_type": "..."},
  "references": [{"id": "ref-...", "text": "...", "gb7714": "...", "law_footnote": "..."}]
}

Usage:
  python legal_citations.py --metadata metadata.json --page 92 --quote-type paraphrase --out citations.json
"""
import argparse
import json
import os
import re


def build_self(meta, page="", quote_type="paraphrase"):
    author = meta.get("author", "[作者未知]")
    title = meta.get("title", "[标题未知]")
    journal = meta.get("journal", "[期刊未知]")
    year = str(meta.get("year", "") or "")
    ps = str(meta.get("page_start", "") or "")
    pe = str(meta.get("page_end", "") or "")

    # GB/T 7714-2025 · 连续出版物中的析出文献（8.5.3）：
    #   责任者，年. 题名[J]. 刊名，卷(期): 页码.
    # 例：杨洪升，2013. 四库馆私家抄校书考略[J]. 文献，(1): 56-75.
    authors = [a.strip() for a in re.split(r"[;；]", str(author)) if a.strip()]
    author_str = ", ".join(authors) if authors else "[作者未知]"
    vi = ""
    if meta.get("volume") and meta.get("issue"):
        vi = f"{meta['volume']}({meta['issue']})"
    elif meta.get("issue"):
        vi = f"({meta['issue']})"
    elif meta.get("volume"):
        vi = f"{meta['volume']}"
    pages = f"{ps}-{pe}" if ps and pe and ps != pe else ps
    pp = f": {pages}" if pages else ""
    if vi:
        gb7714 = f"{author_str}，{year}. {title}[J]. {journal}，{vi}{pp}."
    else:
        gb7714 = f"{author_str}，{year}. {title}[J]. {journal}{pp}."

    # 法学引注（法律出版社《法学引注手册》体例，供页下脚注使用）
    prefix = "参见" if quote_type == "paraphrase" else ""
    law = prefix + f"{author}：《{title}》，载《{journal}》{year}年"
    if meta.get("issue"):
        law += f"第{meta['issue']}期"
    if page:
        law += f"，第{page}页"
    elif ps:
        law += f"，第{ps}页"
        if pe and pe != ps:
            law += f"-{pe}页"
    law += "。"

    return {
        "id": "cite_self",
        "metadata": meta,
        "gb7714": gb7714,
        "law_footnote": law,
        "quote_type": quote_type,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--page", default="")
    ap.add_argument("--quote-type", default="paraphrase", choices=["direct", "paraphrase", ""])
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    meta = json.load(open(args.metadata, encoding="utf-8"))
    out = args.out or os.path.splitext(args.metadata)[0] + ".citations.json"

    # keep any hand-added references from an existing citations file
    references = []
    if os.path.exists(out):
        try:
            references = json.load(open(out, encoding="utf-8")).get("references", [])
        except Exception:
            references = []

    data = {"cite_self": build_self(meta, args.page, args.quote_type), "references": references}
    json.dump(data, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
    print(json.dumps({"status": "success", "citations": data, "out": out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
