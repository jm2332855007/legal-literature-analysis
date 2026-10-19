# 论证骨架卡（Argument Skeleton）Schema

> 一句话（给法学读者）：一张「骨架卡」长什么样、每个字段什么意思（400 篇精读的产物格式）。

精读 400 篇的原子产物。每篇一张卡，放在 `data/argument_skeletons/<id>.json`。

## 定位

骨架卡是**语义精读**的产物，不是机器词典画像：

- 记录一篇论文的**论证语义**：结构、问题、命题、证据、立场、论证链、信号词；
- 是"规则层 + 范式层"的共同载体（见下）；
- 比严格 claim graph 轻（不含 warrant），比机器画像深（含命题间关系与立场归属）。

> **锚点铁律（v2 起）**：`central_claim` / 每条 `premise` / 每条 `position` / 每条 `evidence` 应带 `source_anchor`（原文 quote 片段 + 段落定位），使失真可被机械发现。这是 11 篇抽验（失真率约 7.3%）后加的根因治理——没有锚点，忠实度只能靠人工抽验。

## 字段

| 字段 | 含义 | 用途 |
|---|---|---|
| `structure` | 真实 H1/H2 章节结构 | 结构范式 |
| `problem` | 一句话问题 | 问题识别 |
| `central_claim` | 中心命题（原子） | 命题提取 |
| `central_claim_type` | normative/descriptive/causal/… | 命题类型 |
| `premises[]` | 前提（原子，带 id） | 命题提取 |
| `evidence[]` | 证据（type + supports 指向） | 证据识别 |
| `positions[]` | 通说/少数说/反方（stance + target + author_response） | 立场判别 |
| `normative_conclusions[]` | 规范结论 | 结论识别 |
| `argument_chain[]` | 边（from/to/relation） | 论证链 |
| `signals` | 命中的信号词（counter_intro/author_turn/normative/stance + 证据类型计数） | 规则层来源 |
| `semantic_note` | 一句话论证范式特征 | 学科画像素材 |
| `source_anchor` | 原文 quote 片段 + 段落定位（每条 premise/position/evidence 也各带） | 可追溯/忠实度校验 |

## 两者都要的落地

### 规则层（可程序化）

从 `signals` 字段聚合：

- `counter_intro` → 反方引入信号词；
- `author_turn` → 作者转折/反驳信号词；
- `normative` → 规范结论信号词；
- `stance` → 通说/少数说标记词；
- `evidence_type_counts` → 证据类型分布。

400 篇聚合后生成 `assets/signal-lexicon.json` + `references/argument-grammar.md`。

### 范式层（few-shot）

每张骨架卡就是一个范式样本。agent 拆新论文时，用同学科的骨架卡做参照，形成稳定的法学论证 schema，而不是临场硬拆。

## 证据 type 枚举

- `case`：判例；
- `statute`：法条；
- `data`：数据/实证报告；
- `soft_law`：示范法/软法；
- `doctrine`：学说；
- `archive`：史料。

## 立场 stance 语义

- `通说`：主流观点；
- `少数说`：少数观点；
- 具名学说（如"访问说""目标说""结果排除说"）：作者讨论的具体理论立场；
- `author_response`：作者如何回应这条立场（驳斥/限定/吸收）。
