# 骨架卡拆解 Prompt 模板（自包含 · 派 subagent 拆卡时直接引用）

> 用途：派 subagent 精读一篇法学论文、产出论证骨架卡时，把本模板全文贴进 prompt（或让 subagent 先 read 本文件）。
> 为什么自包含：七条失真铁律是 41 篇抽验（8.2% 失真）提炼的；只写"参见 fidelity-pitfalls.md"等于软建议，subagent 不会去读。所以每条铁律在此**用一句话**内嵌，不展开。

## 骨架卡 JSON 必填字段

```json
{
  "id": "laws-XXXX", "title": "", "author": "", "discipline": "", "discipline_name": "",
  "structure": ["真实H1/H2标题按顺序"],
  "problem": "一句话问题",
  "central_claim": "中心命题(一个原子命题)",
  "central_claim_type": "normative|descriptive|causal|definitive|evaluative",
  "premises": [{"id":"P1","text":"","source_anchor":"原文quote"}],
  "evidence": [{"id":"E1","type":"case|statute|data|soft_law|doctrine|archive","text":"","supports":"P1或立场id","source_anchor":"原文quote"}],
  "positions": [{"id":"L1","type":"counter_position|literature_position","stance":"通说/少数说/具名学说","text":"","target":"C1或P1","author_response":"驳斥/限定/吸收","source_anchor":"原文quote"}],
  "normative_conclusions": [{"id":"N1","text":"","source_anchor":"原文quote"}],
  "argument_chain": [{"from":"P1","to":"C1","relation":"supports|attacks|qualifies|derives|motivates"}],
  "signals": {"counter_intro":[],"author_turn":[],"normative":[],"stance":[],"evidence_type_counts":{"case":0,"statute":0,"data":0,"soft_law":0,"doctrine":0,"archive":0}},
  "semantic_note": "一句话论证范式"
}
```

## 七条失真铁律（每条一句话，拆卡时逐条自检）

1. **立场归属**：谁在说话就标谁——作者自己的主张/自我限定/让步句，不要标成"通说/少数说/具名学说"；author_response 的驳斥（明确否定）/限定（部分接受设边界）/吸收（接受承续）三值分清。
2. **证据归属**：每条 evidence 的 supports 只指向原文里它**真正**在论证的那条；引注出处别张冠李戴（脚注[3]的调研发现别标成脚注[11]的作者）。
3. **脚注不升正文**：脚注/注释里的内容，不要抬升为正文级 premise/position/evidence。
4. **引用≠证据**：顺带引用的文献/学说，不算"作为证据的条目"；evidence_type_counts 必须与 evidence 数组逐条一致。
5. **语义不压损**：条件句别压成断言（"若…则可能"别写成"应"）；多维结构别压成一维；作者**反对**的观点别写成作者主张。
6. **链关系与立场一致**：argument_chain 里 L→X 的 relation，与同条 L 的 author_response 方向要自洽（吸收≠attacks）。
7. **元数据只填能确证的**：source/卷期页码拿不准就留空，别硬填。

## 两条老铁律（保留）

- 转折词"但是/然而/但"归 author_turn，不归 counter_intro；引述标记"有观点/通说/学界/有学者"归 counter_intro。
- 读全文不凭标题猜；忠实原文不编造；structure 从原文标题提取；central_claim 是原子命题。

## 完成标准

写盘 JSON 后跑 `validate_skeleton.py`（格式+id引用 PASS）；锚点缺失会 WARN，但七条失真铁律是**语义**自检，validate 查不了，靠你逐条对照原文守。
