#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract legal article metadata from converted Markdown.

Usage:
  python legal_metadata.py --md article.md --out metadata.json
"""
import argparse
import json
import os
import re

CJK = re.compile(r"[\u4e00-\u9fff]")


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def extract(md_path, pdf_path=""):
    text = open(md_path, encoding="utf-8", errors="replace").read()
    head = text[:8000]
    tail = text[-4000:]
    stem = os.path.splitext(os.path.basename(pdf_path or md_path))[0]
    pdf_head = ""
    first_page = ""
    if pdf_path and os.path.exists(pdf_path):
        try:
            import fitz
            doc = fitz.open(pdf_path)
            pages = [doc.load_page(i).get_text() for i in range(min(3, doc.page_count))]
            pdf_head = "\n".join(pages)
            first_page = pages[0] if pages else ""
        except Exception:
            pass

    title = ""
    m = re.search(r"^#\s+(.+)$", head, re.M)
    if m:
        title = clean(m.group(1))
    if not title and "_" in stem:
        title = stem.rsplit("_", 1)[0].replace("：", ":")

    author = ""
    # 1) filename suffix: 标题_作者.pdf
    if "_" in stem:
        cand = stem.rsplit("_", 1)[1].strip()
        if 2 <= len(cand) <= 4 and CJK.search(cand):
            author = cand
    # 2) first PDF page: title line, then short Chinese line
    if not author and first_page:
        lines = [clean(x) for x in first_page.splitlines() if clean(x)]
        for i, line in enumerate(lines):
            if title and title[:8] in line and i + 1 < len(lines):
                cand = re.sub(r"[∗*].*$", "", lines[i + 1]).strip()
                if 2 <= len(cand) <= 6 and CJK.search(cand):
                    author = cand
                break
    # 3) fallback
    if not author:
        m = re.search(r"([\u4e00-\u9fff]{2,4})\s*[∗*]", head)
        if m:
            author = m.group(1)

    journal = ""
    year = ""
    issue = ""
    src = first_page or head
    # header: 法学评论（双月刊）2008年第3期
    m = re.search(r"([\u4e00-\u9fff]{2,10})\s*[（(]双月刊[）)]\s*(20\d{2})\s*年\s*第\s*(\d+)\s*期", src)
    if not m:
        m = re.search(r"([\u4e00-\u9fff]{2,10})\s*(20\d{2})\s*年\s*第\s*(\d+)\s*期", src)
    if m:
        journal, year, issue = m.group(1), m.group(2), m.group(3)
    if not journal:
        m = re.search(r"(法学研究|法学评论|中国法学|比较法研究|中外法学|法学家|清华法学|政法论坛|法律科学|现代法学|环球法律评论)", src)
        if m:
            journal = m.group(1)
    if not journal:
        m = re.search(r"载《([^》\n]{2,24})》", text)
        if m:
            journal = m.group(1)

    if not year:
        m = re.search(r"(20\d{2})\s*年", src) or re.search(r"\b(20\d{2})\b", src)
        if m:
            year = m.group(1)
    if not issue:
        m = re.search(r"第\s*(\d+)\s*期", src)
        if m:
            issue = m.group(1)

    pages = ""
    m = re.search(r"(\d{2,4})\s*[-–—]\s*(\d{2,4})\s*页", head)
    if m:
        pages = [m.group(1), m.group(2)]
    else:
        m = re.search(r"第\s*(\d{1,4})\s*页", head)
        if m:
            pages = [m.group(1), m.group(1)]
    if not pages:
        pages = ["", ""]

    return {
        "title": title or "[标题未知]",
        "author": author or "[作者未知]",
        "journal": journal or "[期刊未知]",
        "year": year or "[年份未知]",
        "issue": issue,
        "page_start": pages[0],
        "page_end": pages[1],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--pdf", default="")
    ap.add_argument("--page-start", default="")
    ap.add_argument("--page-end", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    meta = extract(args.md, args.pdf)
    if args.page_start:
        meta["page_start"] = args.page_start
    if args.page_end:
        meta["page_end"] = args.page_end
    out = args.out or os.path.splitext(args.md)[0] + ".metadata.json"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(meta, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
    print(json.dumps({"status": "success", "metadata": meta, "out": out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
