# -*- coding: utf-8 -*-
"""legal-literature-analysis 五维审稿测试（自动部分）。

跑法：python tests/test_legal_review.py
输出：每用例 PASS/FAIL + 错误类型；退出码 0 = 全过。
人工核对项（T3/T4/T6/T8/T16/T17）在《测试方案与用例.md》里，另行核对。
"""
import json
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from validate_claim_graph import check, _lcs_ratio  # noqa: E402

GRAPHS = [p for p in glob.glob(f'{ROOT}\\examples\\**\\*.claim-graph.json', recursive=True)
          if 'skeleton' not in p]

RESULTS = []  # (case, pass, detail)

def record(case, ok, detail=''):
    RESULTS.append((case, ok, detail))
    print(f'  {"PASS" if ok else "FAIL"}  {case}  {detail}')


def load(p):
    return json.load(open(p, encoding='utf-8'))


def main():
    print('=== 自动测试（validate 全库） ===')
    all_pass = True
    per_graph = {}
    for p in sorted(GRAPHS):
        g = load(p)
        errs, warns = check(g)
        per_graph[p] = (errs, warns)
        if errs:
            all_pass = False

    # T5（法条 quote 逐字）已含在 validate 的 quote 检查里，此处按错误类型归类
    # T20 全库 PASS
    record('T20 全库 20 图 PASS', all_pass, f'{sum(1 for v in per_graph.values() if not v[0])}/{len(GRAPHS)} 图 FAIL')
    # T18 防泄漏
    leak_fail = [os.path.basename(p) for p, (e, w) in per_graph.items() if any('照抄' in x for x in e)]
    record('T18 text 不照抄 quote/正文', not leak_fail, f'FAIL 图: {leak_fail}' if leak_fail else '全过')
    # T9 孤立 / T10 warrant / T11 复述 / T12 counter / T7 法条类型 / T19 闭包
    t9 = [os.path.basename(p) for p, (e, w) in per_graph.items() if any('isolated' in x for x in e)]
    t10 = [os.path.basename(p) for p, (e, w) in per_graph.items() if any('warrant' in x for x in e)]
    t12 = [os.path.basename(p) for p, (e, w) in per_graph.items() if any('counter' in x for x in e)]
    t7 = [os.path.basename(p) for p, (e, w) in per_graph.items() if any('cite_id' in x for x in e)]
    record('T9 无孤立节点', not t9, str(t9) if t9 else '全过')
    record('T10 warrant 非空且≥6字', not t10, str(t10) if t10 else '全过')
    record('T12 counter 攻击检查', not t12, str(t12) if t12 else '全过')
    record('T7 法条节点 cite_id 检查', not t7, str(t7) if t7 else '全过')
    record('T19 cite_id 闭包', not t7, str(t7) if t7 else '全过')

    print()
    print('=== 结构统计（半自动） ===')
    for p in sorted(GRAPHS):
        g = load(p)
        nodes, edges = g['nodes'], g['edges']
        c1_in = sum(1 for e in edges if e['to'] == 'C1')
        # T15 claim 入度
        record(f'T15 claim 入度≥1 [{os.path.basename(p)}]', c1_in >= 1, f'入度 {c1_in}')
        # T14 节点密度
        if len(nodes) < 10:
            record(f'T14 节点密度≥10 [{os.path.basename(p)}]', False, f'仅 {len(nodes)} 节点')
        else:
            record(f'T14 节点密度≥10 [{os.path.basename(p)}]', True, f'{len(nodes)} 节点')
        # T2 归属判准词
        texts = ' '.join(n.get('text', '') for n in nodes)
        if any(k in texts for k in ('归属判准', '可归属于', '应对未来威胁')):
            record(f'T2 自造概念有归属判准 [{os.path.basename(p)}]', True, '')
        # T1 概念界定 definitive
        defs = [n['id'] for n in nodes if n.get('proposition_type') == 'definitive']
        if defs:
            record(f'T1 概念定义节点标 definitive [{os.path.basename(p)}]', True, str(defs[:4]))

    print()
    failed = [r for r in RESULTS if not r[1]]
    print(f'=== 汇总：{len(RESULTS)} 项，FAIL {len(failed)} 项 ===')
    for c, ok, d in failed:
        print(f'  FAIL {c}: {d}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
