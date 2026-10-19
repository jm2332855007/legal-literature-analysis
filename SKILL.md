---
name: legal-literature-analysis
description: 法学文献分析（单篇 PDF → 解剖报告 + 结构化数据包）。读全文拆原子命题、连证据与法学引注、画论证图、出 Word 报告（含页下脚注）与可复用数据包。内置 400 篇法学论文精读积累的论证语义基线：论证信号词库、11 学科画像、结构范式、论证段模板与衔接搭配，单篇拆解不再临场硬拆。用户上传法学论文 PDF，或要求“法学文献分析、论文解剖、拆论文、画论证图、claim graph、法学引注、Word 报告、论证段模板、法学语体、组织语言”时使用。触发：法学文献分析、论文解剖、论证图、claim graph、法学引注、PDF 转 Word、论证段模板、衔接搭配。
agent_created: true
---

# 法学文献分析

**这个 skill 干一件事：把一篇法学论文拆开，拆成"论证结构"和"机器可读的数据"。**

> 写给法学读者：文档里的计算机词（命令行、JSON、pipeline、依赖…）都在 `references/术语对照.md` 里翻译成法学话；**大多数词你不用懂**，只需要会复制命令、粘贴、回车。

它有两个产出：

- **解剖报告**（给人看）：这篇论文的中心命题是什么、用了哪些前提和证据、引了哪些法条和文献，画成一张论证图，再出一份带脚注的 Word 报告。
- **数据包**（给机器和别的 skill 用）：段落、引注、论证图（claim graph）等结构化文件，供后续写综述、写论文、做风格分析复用。

## 快速开始

```bash
# 一条命令跑完（PDF 或 DOCX 均可；--reading 同时生成阅读/复现任务包）
python scripts/pipeline.py --pdf 论文.pdf --out-dir out/ao --id ao --title "标题" --reading

# 只拆图（已有段落索引时）
python scripts/validate_claim_graph.py out/ao/ao.claim-graph.json
python scripts/mermaid_claim_graph.py --file out/ao/ao.claim-graph.json --out out/ao/ao.mmd

# 只提脚注（含前引解析）
python scripts/extract_footnotes.py --json 论文.content_list.json --out out/ao/ao.footnotes.json --resolve
```

## 怎么拆（五步 + 一步扩展）

1. **读全文**——不要只看摘要，摘要会漏掉论证细节。
2. **拆原子命题**——把论文拆成一条条"可以判断真假"的最小命题（一个节点一句话），并标注每个命题是从原文哪段、哪句话来的（quote 逐字摘，命题用自己的话概括，别照抄）。
3. **连证据和引注**——每个证据、反方观点、文献都要挂上出处（cite_id），不能凭空捏。**归属铁律**：反方/文献（被引者立场）不得挂 `cite_self`，必须挂被引者文献（`references[].id`）——否则就是把别人的观点记到作者头上。
4. **画论证图**——把命题和它们之间的关系（支持/反驳/限定/推导…）画成图；关系要写清"为什么成立"（warrant），不能只写"支持"。
5. **出报告和数据包**——Word 报告 + 结构化数据，一键由 `pipeline.py` 完成。Word 默认套用技能内置的**中国法学样式集**（`assets/templates/中国法学_style.docx`，源自主机 `中国法学.dot`）；参考文献表用 GB/T 7714-2025 体例，页下脚注用《法学引注手册》体例，两者分开标注。
6. **读与复现（可选）**——`--reading` 生成阅读任务包：章节结构 → 逐章精读（研究者/初学者双模式）→ 核心贡献 → 局限与未决 → 思维导图 → 复现训练三遍（骨架→默写→对照→清单）。提示词见 `references/reading-prompts.md`。

## 为什么说"不临场硬拆"

这个 skill 里已经存了 400 篇法学论文精读积累下来的**语义基线**，拆新论文时先翻它们，而不是从零拍脑袋：

- **论证信号词库**（`assets/signal-lexicon.json`）——哪些词提示"反方来了""作者要转折""这是证据"。
- **学科画像**（`references/discipline-profiles.md`）——11 个二级学科各自的论证套路。
- **结构范式**（`references/argument-grammar.md`）+ **论证段模板**（`references/discourse-templates.md`）+ **衔接搭配**（`assets/connector-collocations.json`）——真实法学论文是怎么组织段落、怎么衔接的。

这几样东西有双重用途：拆论文时当"参照系"，写论文时当"反 AI 味探测器"（真实论文模板有偏离、衔接有换用，AI 文则均匀套模板）。

## 额外能力：找出论证的问题

拆图不只是画"完整自洽"的论证，还能标出论证的**断裂、孤立、证据不足**：

- 图里的节点/边可以带 `diagnosis` 标记（孤立/证据缺/跳步/断裂），渲染成红虚线、橙框，让问题一眼可见。
- `scripts/detect_leaps.py` 自动扫出"跳步/无锚规范句/孤立小节"的候选问题，人复核后写进问题清单。
- `scripts/check_graph_issues.py` 核对"你列的问题是不是都进了图"。

这套东西的用途：拿论文去"体检"，看出它哪里论证断了、哪里证据不足、哪里论证链没接上。

## 文件在哪

- `scripts/pipeline.py`——一条命令：PDF → 段落 → 引注 → 论证图校验 + 出图 → Word 报告 → 数据包。加 `--reading` 会同时生成**阅读/复现任务包**（`<id>.reading/`：01 章节结构 → 02 逐章精读（按章节逐个）→ 03 核心贡献 → 04 局限与未决 → 05 思维导图 → 06/07/08 复现训练三遍），每个 `.prompt.md` 末尾带输出槽，agent 或用户把模型回复贴进去即完成一轮。
- `scripts/validate_claim_graph.py`——论证图校验（quote 是否精确、节点是否孤立、**text 是否照抄 quote（防泄漏铁律）**、proposition_type 是否合法等）。
- `scripts/mermaid_claim_graph.py`——论证图转 Mermaid（大图首选，自动布局不重叠）。
- `scripts/detect_leaps.py` / `check_graph_issues.py`——上面说的"找问题"和"核对问题"。
- `references/claim-graph-standard.md`——论证图的完整规则（写图之前必读）。
- `references/术语对照.md`——计算机词 → 法学人话（命令行/JSON/pipeline/依赖/claim graph…），法学读者先看这篇。
- `references/reading-prompts.md`——**法学阅读提示词库**（双阶段逐章精读·研究者/初学者双模式、思维导图 4+1 分支、复现训练四步：骨架→默写→对照→清单、综述 [num] 引用规范）。提示词模式改编自 Zotero-AI-Butler（AGPL-3.0）。
- `scripts/extract_footnotes.py`——从 `content_list.json`（首选）或 MD 提取脚注定义、解析"前引"链（L 节点归属与参考文献的权威来源）。
- `scripts/gen_reading_prompts.py`——生成阅读/复现任务包（`--chapters chapters.json` 可按章节逐个渲染）。
- `scripts/build_report.py`——论证图 JSON → 解剖报告 Markdown（论证链 + 图 + 节点对照表 + 归属说明 + 脚注）。
- `scripts/md_to_docx.py`——Markdown → Word（真实页下脚注；默认中国法学样式基底、自动清空模板页眉）。
- `scripts/legal_citations.py`——GB/T 7714-2025 与《法学引注手册》两套引注的生成器。
- `assets/reading_prompts.json`——四套提示词的模板资产（与 `references/reading-prompts.md` 同步维护）。
- `tests/`——单元测试（含阅读任务包、脚注提取、样例图过门）与五维审稿测试（`test_legal_review.py`）。

## 什么时候不用（转给别人）

- 写综述 / 论文 / 复现某篇 → 用 `law-literature-review`（本 skill 只拆，不写；但它的复现模式要本 skill 的 claim graph）。
- 做论文风格复现基准实验 → 用 `legal-style-benchmark`（本 skill 的 claim graph 是它的评分输入）。
- 去 AI 味 / 诊断 AI 腔 → 用 `ai-style-diagnosis`（本 skill 的语言层数据是它的探测器）。


