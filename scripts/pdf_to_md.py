#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF -> Markdown + paragraph index for legal article anatomy.

Usage:
  python pdf_to_md.py --pdf article.pdf --out-dir out --id laws-0055
Outputs:
  <id>.md
  <id>.paragraphs.json
  <id>.structure.json
"""
import argparse
import json
import os
import re

CJK = re.compile(r"[\u4e00-\u9fff]")
HEAD1 = re.compile(r"^[一二三四五六七八九十]+、")
HEAD2 = re.compile(r"^[（(][一二三四五六七八九十]+[）)]")


def cjk(s):
    return len(CJK.findall(s or ""))


def clean(s):
    s = (s or "").replace("\r", "").replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n+", " ", s)
    return s.strip()


def split_keywords(s):
    s = re.sub(r"^(关键词|主题词)\s*[:：]?", "", s.strip())
    out = []
    for w in re.split(r"[；;，,、\s]+", s):
        w = w.strip(" .:：;；,，、[]【】“”")
        if 2 <= len(w) <= 20 and w not in out:
            out.append(w)
    return out[:12]


def slugify(title, fallback):
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", title or fallback).strip("-")
    return s[:80] or fallback


def _is_heading(s):
    return bool(HEAD1.match(s) or HEAD2.match(s))


def _split_page(raw):
    raw = raw.replace("\r", "\n")
    lines = [l.rstrip() for l in raw.split("\n") if l.strip()]
    groups = []
    buf = []
    for raw_line in lines:
        line = clean(raw_line)
        if not line:
            continue
        indented = raw_line.startswith("\u3000")
        if buf and (indented or _is_heading(line)):
            groups.append(" ".join(buf))
            buf = []
        buf.append(line)
        joined = "".join(buf)
        if len(joined) >= 380 and re.search(r"[。！？；]$", line):
            groups.append(" ".join(buf))
            buf = []
    if buf:
        groups.append(" ".join(buf))
    return [g for g in groups if cjk(g) >= 15]


def _is_heading(s):
    return bool(HEAD1.match(s) or HEAD2.match(s))


def _split_page(raw):
    raw = raw.replace("\r", "\n")
    lines = [l.rstrip() for l in raw.split("\n") if l.strip()]
    groups = []
    buf = []
    for raw_line in lines:
        line = clean(raw_line)
        if not line:
            continue
        indented = raw_line.startswith("\u3000")
        if buf and (indented or _is_heading(line)):
            groups.append(" ".join(buf))
            buf = []
        buf.append(line)
        joined = "".join(buf)
        if len(joined) >= 380 and re.search(r"[。！？；]$", line):
            groups.append(" ".join(buf))
            buf = []
    if buf:
        groups.append(" ".join(buf))
    return [g for g in groups if cjk(g) >= 15]


def extract(pdf):
    import fitz
    doc = fitz.open(pdf)
    pages = []
    for i in range(doc.page_count):
        pages.append(_split_page(doc.load_page(i).get_text()))
    return pages


LATIN = re.compile(r"[A-Za-z]")


def _split_page_loose(raw):
    """外文/排版异常文档的兜底分段：不以中文为门槛（拉丁字母 ≥30 也算有效段）。"""
    groups = _split_page(raw)
    if groups:
        return groups
    raw = raw.replace("\r", "\n")
    lines = [l.rstrip() for l in raw.split("\n") if l.strip()]
    groups, buf = [], []
    for raw_line in lines:
        line = clean(raw_line)
        if not line:
            continue
        buf.append(line)
        joined = " ".join(buf)
        if len(joined) >= 380 and re.search(r"[.!?;:]$", line):
            groups.append(" ".join(buf))
            buf = []
    if buf:
        groups.append(" ".join(buf))
    return [g for g in groups if cjk(g) >= 15 or len(LATIN.findall(g)) >= 30]


def extract_loose(pdf):
    """兜底抽取：分段规则不适用的文档（如外文规范文本），逐页用宽松规则抽。"""
    import fitz
    doc = fitz.open(pdf)
    return [_split_page_loose(doc.load_page(i).get_text()) for i in range(doc.page_count)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out-dir", default="output")
    ap.add_argument("--id", default="")
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    pages = extract(args.pdf)
    fallback = False
    if not any(pages):
        # 主规则一段未出（如外文规范文档）：启用宽松兜底抽取
        pages = extract_loose(args.pdf)
        fallback = any(pages)
    title = args.title
    if not title:
        for items in pages:
            if items:
                title = items[0].split("\n")[0][:120]
                break
    if not title:
        title = os.path.splitext(os.path.basename(args.pdf))[0]
    doc_id = args.id or slugify(title, "article")
    os.makedirs(args.out_dir, exist_ok=True)

    paragraphs = []
    sections = []
    abstract = ""
    keywords = []
    current = ""
    for page_no, items in enumerate(pages, 1):
        for text in items:
            first = text.split("\n")[0].strip()
            if fallback:
                # 兜底模式：跳过中文标题/摘要/关键词规则，逐条直接收录
                pid = "P%04d" % (len(paragraphs) + 1)
                paragraphs.append({"pid": pid, "page": page_no, "section": current, "text": text})
                continue
            if HEAD1.match(first) or HEAD2.match(first):
                current = first
                sections.append({"heading": first, "page": page_no, "level": 1 if HEAD1.match(first) else 2})
                continue
            am = re.search(r"(内容提要|摘\s*要)\s*[:：]\s*(.*)$", text, re.S)
            if am and not abstract:
                abstract = am.group(2).strip()
                abstract = re.split(r"(关键词|主题词)\s*[:：]", abstract)[0].strip()
            km = re.search(r"(关键词|主题词)\s*[:：]\s*([^\n]{0,300})", text)
            if km and not keywords:
                raw_kw = re.split(r"[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)]", km.group(2))[0]
                keywords = [w for w in split_keywords(raw_kw) if w not in ("问题的提出", "引言")]
            if am:
                pid = "P%04d" % (len(paragraphs) + 1)
                paragraphs.append({"pid": pid, "page": page_no, "section": "摘要", "text": text})
                continue
            if cjk(text) < 15:
                continue
            pid = "P%04d" % (len(paragraphs) + 1)
            paragraphs.append({"pid": pid, "page": page_no, "section": current, "text": text})

    md = [f"# {title}", "",
          f"> 来源 PDF：{os.path.basename(args.pdf)}；页数：{len(pages)}；段落：{len(paragraphs)}"
          + ("；**兜底抽取**（主分段规则不适用，按宽松规则逐页抽取）" if fallback else ""), ""]
    if abstract:
        md += ["## 摘要", "", abstract, ""]
    if keywords:
        md += ["## 关键词", "", "；".join(keywords), ""]
    for p in paragraphs:
        if p["section"] == "摘要":
            continue
        md.append(f"<!-- {p['pid']} page {p['page']} -->")
        md.append(p["text"])
        md.append("")
    md_path = os.path.join(args.out_dir, doc_id + ".md")
    open(md_path, "w", encoding="utf-8", newline="\n").write("\n".join(md))

    para_path = os.path.join(args.out_dir, doc_id + ".paragraphs.json")
    json.dump({"id": doc_id, "title": title, "pdf": os.path.abspath(args.pdf),
               "source_type": "pdf", "extraction": "fallback_loose" if fallback else "standard",
               "pages": len(pages), "paragraph_count": len(paragraphs),
               "sections": sections, "paragraphs": paragraphs},
              open(para_path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)

    struct_path = os.path.join(args.out_dir, doc_id + ".structure.json")
    json.dump({"id": doc_id, "title": title, "pdf": os.path.abspath(args.pdf),
               "extraction": "fallback_loose" if fallback else "standard",
               "page_count": len(pages), "paragraph_count": len(paragraphs),
               "abstract": abstract, "keywords": keywords, "sections": sections},
              open(struct_path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
    print("wrote")
    print(" ", md_path)
    print(" ", para_path)
    print(" ", struct_path)


if __name__ == "__main__":
    main()
