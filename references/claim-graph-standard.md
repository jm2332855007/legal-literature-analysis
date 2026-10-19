# 严格 claim graph 标准

> 一句话（给法学读者）：论证图怎么画、什么算合格（拆图前必读）。

> 一张图服务四个用途：解剖（人读）、诊断（断口暴露）、防泄漏复现（抽象 text 供下游重写）、风格基准评分（论证结构输入）。schema 统一，用途差异由可选字段承载（diagnosis / proposition_type）；拆解一律**完整优先**。

## 必须满足

1. `fully_read=true`；
2. 1 个 `problem`；
3. 1 个 `claim` 作为 C1；
4. ≥2 个 `premise`；
5. ≥1 个 `evidence_*`；
6. ≥1 个 `counter_position` 或 `literature_position`；
7. ≥1 个 `normative_conclusion`；
8. 每节点 `source_anchor`（page + paragraph_id + quote）；
9. 每条边 `warrant`；
10. `counter_position` 至少一条 `attacks`/`qualifies` 指向 claim 或 premise；`literature_position` 可只作背景/支撑（supports 或无攻击边），不强制攻击——通说梳理不是反方，别硬扭；
11. 无孤立节点；
12. `source.citations` 指向 citations.json；
13. 证据/反方/文献节点必须带 `source_anchor.cite_id`。

## 出处 = 命题 + 引注（骨）

法学论文的论证是 **命题 + 出处**，两者不能拆开：

```text
node.text          ← 原子命题（分析性判断）
node.source_anchor ← 出处锚点（原文引用）
  .quote           ← 原文直接引用
  .paragraph_id    ← 段落索引
  .page            ← PDF 页序（报告里换算成印刷页）
  .cite_id         ← 引注：cite_self 或 references[].id
```

**`text` 与 `quote` 职责分离（防泄漏铁律）**：

- `text` 是**抽象命题**：用拆解者自己的语言概括该命题的语义内容（主项/谓项/模态/范围），**不保留原文的句式与措辞**。它回答"这个命题在论证里说什么"，不是原文的压缩复述。
- `quote` 是**精确锚点**：逐字摘取原文，用于定位与核验。它是"证据在哪"，不是"该写什么"。
- **禁止**：`text` 近乎照抄 `quote`（原句压缩）；`text` 保留原文动词结构（"X 照搬 Y 的理论"应抽象为"X 的主张源于对 Y 理论的移植"）。

这条规则直接服务于仿写防泄漏：下游 `reproduction-draft-prompt.md` 的"命题→表达"层要从 `text` 的**语义**重写文章，若 `text` 本身近乎原句，生成层就要反复"洗一遍"。拆图时就产出抽象命题，泄漏从源头就断了。

- 证据没有 `cite_id` 就不是证据，校验器会 FAIL；
- **归属铁律（防张冠李戴）**：`counter_position`/`literature_position`（被引者立场）**不得挂 `cite_self`**，必须挂 `references[].id` 指向被引者文献；`quote` 是作者转述句、`cite_id` 指归属来源，二者不可混同（校验器强制）；
- `cite_self` 指向本文献引注（法律出版社《法学引注手册》体例，供页下脚注）；
- 参考文献表另用 **GB/T 7714-2025** 体例（连续出版物中的析出文献：`责任者，年. 题名[J]. 刊名，卷(期): 页码.`），由 `legal_citations.build_self` 生成，不得以法学引注体例冒充；
- 引用本文讨论的外部文献时，用 `references[].id`，引注写进 citations.json 的 `references`。

## 原子规则

- 一个节点一个可判断真假的命题；
- 不要把“构成 + 运行规律”“特征 + 类型归属”“否定反方 + 正面定性”放一个节点；
- 证据数据要拆：分布、缺失率、案例分开；
- 规范结论独立于 C1，不要复述；
- 报告按节点逐行展开，不折叠（这是原子级的可视化保证）。

## warrant

warrant 回答“为什么这条边成立”：

- 支持：前提/证据如何推出结论；
- 攻击：反方与作者命题在哪一点冲突；
- 限定：反方哪部分被接受、哪部分被排除；
- 推出：从 C1 到 N1 经过什么中间步骤；
- 例证：案例是说明、反例还是归纳样本。

禁止只写“支持”“显然”。

## 边关系（relation）全集

| relation | 含义 | 法学场景 |
|---|---|---|
| supports | 正向支撑 | 证据支撑前提、前提支撑命题 |
| attacks | 反驳 | 反方攻击作者命题 |
| qualifies | 限定 | 反方部分被接受、部分被排除 |
| derives | 推出 | 命题推出规范结论 |
| explains | 说明 | 解释机制/原因 |
| motivates | 引出 | 问题引出中心命题 |
| constitutes | 构成 | A 是 B 的构成要素 |
| grounds | 奠基 | 规范依据为命题奠基 |
| responds | 回应 | 对反驳的回应 |
| illustrates | 例证 | 案例说明 |
| **balancing** | 权衡 | 利益/原则衡量（同阶衡量、比例原则的均衡性） |
| **subsumption** | 涵摄 | 事实/规范要件归入（构成要件该当） |
| **analogy** | 类推 | 类似情形同一处理 |
| **a_contrario** | 反面论证 | 明示其一排斥其他 |
| **a_fortiori** | 当然论证 | 举重明轻/举轻明重 |

supports 是万金油：若图上 supports 占比 >60%，说明法学论证形式（权衡/涵摄/类推）没拆出来，需回炉。

## 常见不合格

- 从摘要写图；
- 节点没有页码/段落；
- `node.text` 是原句压缩、近乎照抄 `quote`（应抽象命题，不保留原文句式措辞）；
- 证据只在侧表；
- 文献只在 `literature_positions` 侧表；
- 证据/反方/文献没有 `cite_id`；
- 全是 supports，没有 attacks/qualifies；
- warrant 复述关系；
- C1 是复合命题。

## 诊断标记（diagnosis，可选）

claim graph 不只是画"完整自洽"的论证，也能画"论证的问题"——断裂、孤立、证据不足。节点/边可带可选字段 `diagnosis`：

- 节点 `diagnosis`：`isolated`（孤立，没进论证链）、`evidence_insufficient`（证据不足/缺证据）；
- 边 `diagnosis`：`leap`（断言跳步，如"转译"跳过中间步骤）、`gap`（断裂，中间缺一个命题）。

校验规则：标了 `diagnosis=isolated` 的孤立节点是"有意暴露的问题"，不判 FAIL；未标注的孤立节点仍 FAIL。render 会把 diagnosis 画成红虚线/橙边框 + 中文标签。

这样，同一份 claim graph 既能给"好论文"做解剖（无 diagnosis），也能给"有问题的论文"做诊断（diagnosis 标记暴露断裂）——这是"犯罪线索图谱"的关键：不仅画线索关系，还标出线索的断口、缺失、无法关联。

## 命题类型（proposition_type，可选）

premise/claim/problem 节点可带 `proposition_type`（descriptive / normative / definitive / causal / evaluative / interpretive / balancing）。

- `interpretive`：解释命题（“X 条应解释为 Y”）——解释论文章的核心命题必须标它；
- `balancing`：权衡命题（“利益 A 与 B 如何衡量”）——利益衡量/比例原则的均衡性步骤标它。

它是 `detect_leaps.py` 的 `type_leap` 检测器的基础：描述性前提无规范依据却直接 supports 规范性命题，会被标为"事实→规范缺桥"。不标该字段，type_leap 检测器跳过。

## 节点粒度（按篇幅，不设硬上限）

- 每 1000 字约 1–1.5 个节点：2.6 万字论文约 26–40 节点；
- **完整优先**：中间命题宁多拆，不为凑"简洁"压扁——论证链的断口（如比例原则收益侧缺桥）往往就藏在被压掉的中间命题里。
