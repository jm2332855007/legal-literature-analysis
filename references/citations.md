# 引注规则

> 一句话（给法学读者）：引注怎么排、两套体例（法学脚注 / GB/T 7714-2025）各用在哪。

## 结构

`legal_citations.py` 输出：

```json
{
  "cite_self": {"id": "cite_self", "metadata": {...}, "gb7714": "...", "law_footnote": "...", "quote_type": "..."},
  "references": [{"id": "ref-...", "text": "...", "gb7714": "...", "law_footnote": "..."}]
}
```

- `cite_self`：本文献自身的引注（自动生成）；
- `references`：本文讨论的被引外部文献（agent 手动补，id 与 graph 节点的 `cite_id` 对应）。

## 两种输出

1. **GB/T 7714-2025 尾注**
   `作者. 标题[J]. 期刊, 年(期): 起-止页.`
2. **法学引注手册第二版脚注**
   `参见作者：《标题》，载《期刊》年第期，第页。`

## quote_type

- `direct`：直接引用 → 不加“参见”；
- `paraphrase`：转述 → 加“参见”。

## Word 脚注

`build_report.py` 为每个带 `cite_id` 的节点生成一条脚注：

- 脚注页码用**印刷页**（metadata 起始页 + PDF 页序偏移）；
- 引用外部文献时用 `references[].law_footnote`；
- `md_to_docx.py` 用 Pandoc 转成真页下注。

## 边界

- 只生成格式，不核验真实性；
- 印刷页换算依赖 `page_start`，需人工核对；
- 英文引注（Bluebook/OSCOLA 等）不在本 skill。
