#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取法学论文脚注定义（优先 content_list.json 的 page_footnote 块；回退 MD 文本）。

用法：
  python extract_footnotes.py --json paper.content_list.json [--out footnotes.json]
  python extract_footnotes.py --md paper.md [--out footnotes.json]

为什么优先 JSON：PDF→MD 转换会丢/扁平化部分脚注（如全角括号「（2）」），
而 content_list.json 保留 type=page_footnote 的结构化块，是权威来源。
"""
import argparse
import json
import os
import re

# 行首/块首标记：〔n〕 [n] 【n】 (n) （n）
DEF_RE = re.compile(r'^(?:〔|\[|【|\(|（)(\d+)(?:〕|\]|】|\)|）)\s*(.+)$')
# 前引指针：参见前引〔34〕/前引 (3)/前引[21]
QIANYIN_RE = re.compile(r'前引\s*[〔\[【（(]?\s*(\d+)\s*[〕\]】）)]?')


def extract_from_json(path):
    d = json.load(open(path, encoding='utf-8'))
    fns = {}
    for x in d:
        if x.get('type') != 'page_footnote':
            continue
        m = DEF_RE.match(x.get('text', '').strip())
        if m:
            fns[m.group(1)] = m.group(2).strip()
    return fns


def extract_from_md(md_text):
    fns = {}
    cur = None
    for line in md_text.splitlines():
        m = DEF_RE.match(line.strip())
        if m:
            fns[m.group(1)] = m.group(2).strip()
            cur = m.group(1)
        elif cur and line.strip() and not line.startswith('#') and not line.strip().startswith('<!--'):
            fns[cur] = (fns[cur] + ' ' + line.strip()).strip()
    return fns


def resolve_qianyin(num, fns, depth=0):
    """把「参见前引〔n〕，…」解析为被引脚注的完整原文（最多 4 层）。"""
    if depth > 4:
        return fns.get(num, '')
    t = fns.get(num, '')
    m = QIANYIN_RE.search(t)
    if not m:
        return t
    base_num = m.group(1)
    base = resolve_qianyin(base_num, fns, depth + 1)
    tail = t[m.end():].strip(' ，,。')
    return f"{base.rstrip('。')}{('（原文脚注%s，%s）' % (base_num, tail)) if tail else ''}。"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', default='')
    ap.add_argument('--md', default='')
    ap.add_argument('--out', default='')
    ap.add_argument('--resolve', action='store_true', help='同时输出解析前引后的完整引注')
    args = ap.parse_args()
    if args.json:
        fns = extract_from_json(args.json)
        base = args.json
    elif args.md:
        fns = extract_from_md(open(args.md, encoding='utf-8').read())
        base = args.md
    else:
        ap.error('need --json or --md')
    out = args.out or os.path.splitext(base)[0] + '.footnotes.json'
    data = {'raw': fns}
    if args.resolve:
        data['resolved'] = {k: resolve_qianyin(k, fns) for k in fns}
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f'extracted {len(fns)} footnotes -> {out}')


if __name__ == '__main__':
    main()
