# Pipeline：PDF → MD → 元数据 → 引注 → Word

> 一句话（给法学读者）：一条命令把 PDF 变成报告和数据包的操作说明。

## 命令

```bash
python scripts/pipeline.py \
  --pdf "论文.pdf" \
  --out-dir "out/ao" \
  --id ao \
  --title "论文标题" \
  --page 92 \
  --page-start 92 --page-end 98 \
  --mode pipeline
```

## 产出

| 文件 | 内容 |
|---|---|
| `ao.md` | 标题、摘要、关键词、正文、`<!-- P0001 page 1 -->` |
| `ao.paragraphs.json` | `pid/page/section/text` |
| `ao.structure.json` | 页数、摘要、关键词、标题 |
| `ao.metadata.json` | 作者/标题/期刊/年/期/页 |
| `ao.citations.json` | GB/T 7714 + 法学脚注 |
| `ao.docx` | Word（Pandoc 页下脚注） |
| `ao.manifest.json` | 所有产物路径 |

## 分段规则

`pdf_to_md.py` 先按 `\r`/`\n` 分行，再按行聚合：

- 行首有全角缩进 → 新段；
- 标题行 → 新段；
- 当前段超过约 380 字且以句末标点结尾 → 新段。

它不是版式分析，PDF 排版差异会导致段落误差。

## 元数据

`legal_metadata.py` 从三处取：

1. MD 标题/首段；
2. PDF 文件名（`标题_作者.pdf`）；
3. PDF 前 3 页（期刊/年/期/页）。

**页范围常常不准**，尤其 CNKI 页脚/脚注混排。  
引注需要精确页时，显式传 `--page`；页范围用 `--page-start/--page-end` 覆盖，不要盲信自动值。

## Word

`md_to_docx.py` 用：

```bash
pandoc analysis.md -o analysis.docx --from=markdown+footnotes --standalone
```

需要插图时加 `--image graph.png`（python-docx 追加）。

## 常见失败

- `pandoc not found`：装 Pandoc 或改 PATH。
- 段落过少：PDF 用 `\r` 分行或没有空行；转换器会按行聚合，仍可能把脚注混入。
- 标题/作者错：先看 `structure.json`，手工修 metadata。
- 页范围错：用 `--page` 覆盖，或在 metadata 中手改。
- 扫描件：无文本层，先 OCR。
