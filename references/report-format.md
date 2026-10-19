# 解剖报告形态规范

> 一句话（给法学读者）：Word 解剖报告的格式规范（给想改报告样式的人看）。

报告是唯一“给人读”的交付物。它由 `build_report.py` 从 claim graph 生成。

## 五块结构（固定顺序）

1. **题头**：标题 + 作者/期刊/年/期/页；
2. **引注**：`cite_self` 的法学脚注 + GB/T 7714 + `references`；
3. **论证链**：按 问题 → 前提 → 中心命题 → 证据 → 反方与文献 → 规范结论 分组；
4. **原子论证图**：PNG；
5. **节点—原文—引注对照表**：每行一个原子节点，quote + 印刷页/段落 + 脚注；
6. **边界声明**：哪些是原文、哪些是分析。

## 硬性要求

- 一个节点一行，不折叠（原子级的可视化保证）；
- 每个证据/反方/文献节点必须有一条真脚注；
- 脚注页码是**印刷页**，不是 PDF 页序；
- 图内要有读图说明与节点/warrant 表（matplotlib 版由 `render_claim_graph.py` 保证；大图改用 `mermaid_claim_graph.py` 生成的 Mermaid 图，节点/warrant 表保留在报告正文）。

## Word

`md_to_docx.py` 用 Pandoc `markdown+footnotes` 转 Word：

- 脚注是页下注（`w:footnote`）；
- 图片通过 Pandoc `--resource-path` 解析并嵌入；
- 正文已有 `[^n]` 标记时不重复注入。

## 校验点

- `word/footnotes.xml` 里有 `cite_self` 的作者/期刊；
- `word/document.xml` 里有 `footnoteReference`；
- `word/media/` 里有图。
