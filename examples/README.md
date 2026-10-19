# examples 示例数据说明

每个 `laws-XXXX/`（及 `anquan/`、`ao-shuanghong/`）是一份完整的"单篇论文数据包"：

| 文件 | 内容 |
|---|---|
| `<id>.paragraphs.json` | 段落索引（pid / page / text），论证图 quote 的锚点来源 |
| `<id>.structure.json` | 章节结构（heading / page / level） |
| `<id>.metadata.json` | 作者/刊名/年/期/页码（部分样本有） |
| `<id>.citations.json` | 本文引注（cite_self）+ 被引者文献（references） |
| `<id>.footnotes.json` | 原文脚注定义（raw + resolved，前引已解析） |
| `<id>.claim-graph.json` | 论证图（节点 + 边 + warrant + diagnosis） |
| `visuals/<id>.png` | 论证图渲染（Mermaid，大图首选） |
| `<id>.reading/` | 阅读/复现任务包（`--reading` 生成；laws-0380 有三遍复现训练实跑填充示例） |

## 已拆论文清单（随仓库精简为 2 个示例）

- `laws-0380`（郑彧·上市公司实际控制人，**基准文，含三遍复现训练实跑填充**）
- `ao-shuanghong`（敖双红，单元测试依赖样例）

> 其余数据包未随仓库发布（含期刊全文，避免版权与体积问题）；本地保留在 `~/.dsh/skills/legal-literature-analysis/examples/`。

## 约定

- 所有路径均为**相对路径**（相对技能根目录），不含本机绝对路径，可直接移植；
- `quote` 逐字摘、`text` 是抽象命题（防泄漏铁律）；
- 反方/文献节点的 `cite_id` 指向被引者文献（`references[].id`），不挂 `cite_self`。


