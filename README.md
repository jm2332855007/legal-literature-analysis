# 🔥 把一篇法学论文，拆成「论证图 + 数据包」

> 读法核 / CLSCI 读到崩溃的人，懂的都懂：一篇 2 万字，读完脑子里只剩「好像很有道理」。
> 这个 skill 只干一件事——**把论文拆开，拆成看得见的论证结构和能直接用的数据**。

---

## 💡 一句话说清它是什么

它像一个**帮你读论文的助手**：你把论文（PDF 或 Word）给它，它替你回答——

- 这篇论文要解决什么问题？
- 中心主张是什么？
- 用了哪些前提、哪些证据（法条/判例/数据/学说）？
- 反方是谁？作者怎么回应的？
- 论证有没有断的地方（跳步、证据不足、没回应反方）？

然后把答案画成一张**论证图**，再写成一份**带脚注的 Word 报告**。

> ⚠️ 不懂任何计算机知识也能用：你只需要会**复制命令、粘贴、回车**。每一步下面都写了怎么做。

---

## ✨ 拆完你手里有什么

| 产出 | 长什么样 |
|---|---|
| 🕸 **论证图** | 一张图：问题、前提、证据、反方、结论各用不同颜色，箭头写「根据/支持/攻击/权衡」等关系 |
| 📄 **解剖报告** | Word 文件：中国法学样式（宋体五号、页下脚注），含「节点—原文—引注」对照表 |
| 🗂 **数据包** | 几个结构化文件，别的工具可以直接拿去写综述、写论文 |

## 📚 还附赠一个「读透包」（选装）

加 `--reading` 参数，会额外生成一套按章节精读的提示词：

- 01 章节结构：先让 AI 标出每章的作用（立论/驳论/释义/例证…）
- 02 逐章精读：每章六问（作用、命题、规范依据、论证形式、术语、漏洞）
- 03 核心贡献 · 04 局限与未决
- 05 思维导图：四个固定分支（背景与问题 / 论证方法与结构 / 规范结论 / 结论与意义）
- 06/07/08 **复现训练三遍**：先抽骨架 → 不看原文写提纲 → 对照找差距 → 三遍补结构、补规范依据、补反方

> 最实用的场景：**教人默写一篇文章**。不是抄，是用同样的骨架写自己的内容，再对照找差距。

---

## 🚀 先用起来：三条命令（复制粘贴即可）

**前提**：先按下面「零基础安装」装好（就三步，5 分钟）。

**① 拆一篇论文（最常用）**

```bash
python scripts/pipeline.py --pdf 论文.pdf --out-dir out/ao --id ao --title "论文标题"
```

翻译成人话：`pipeline.py` 是主程序；`--pdf` 后面换成你的论文文件名；`--out-dir` 是结果放哪个文件夹；`--id` 是给这篇论文起个英文名；`--title` 是论文中文标题。回车后等它跑完，去 `out/ao` 文件夹看结果。

**② 连「读透包」一起生成**

```bash
python scripts/pipeline.py --pdf 论文.docx --out-dir out/ao --id ao --reading
```

就是在第①条后面加 `--reading`。

**③ 只想提取脚注（含「前引」自动展开）**

```bash
python scripts/extract_footnotes.py --json 论文.content_list.json --out out/ao/ao.footnotes.json --resolve
```

`content_list.json` 是从 PDF 转出来的结构化文件（如果只有 PDF，先跑第①条，它会顺手生成）。

---

## 📦 零基础安装（不需要会编程）

> 下面每一步都告诉你「在哪操作、做什么、看到什么算成功」。

### 第 0 步：打开「命令行」

- **Windows**：按 `Win + R`，输入 `powershell`，回车 → 出现一个蓝色/黑色窗口。
- **macOS**：打开「启动台」搜「终端」，打开。

后面所有命令都是**复制、粘贴进这个窗口、按回车**。出错不要慌，把报错整段复制给我。

### 第 1 步：把技能下载到电脑里

```bash
cd ~/.dsh/skills
git clone https://github.com/jm2332855007/legal-literature-analysis.git
```

- `cd` = 打开某个文件夹；`git clone` = 把这个技能从 GitHub 下载一份到本地。
- Windows 上 `~` 表示 `C:\Users\你的用户名`，所以这一步会把技能放进 `C:\Users\你的用户名\.dsh\skills\legal-literature-analysis`。
- 如果提示「`.dsh\skills` 不存在」：先跑 `mkdir -p ~/.dsh/skills` 建目录，再重跑。

### 第 2 步：装依赖（像给 App 装运行库）

```bash
pip install -r legal-literature-analysis/requirements.txt
```

- `pip` 是 Python 的「应用商店」；这句话把四个必需的库装上（PyMuPDF 读 PDF、python-docx 读写 Word、matplotlib/networkx 画图）。
- 还要一个转换 Word 的工具 **pandoc**：
  - Windows：`winget install JohnMacFarlane.Pandoc`
  - macOS：`brew install pandoc`

### 第 3 步：确认被识别

新开一个 Harness 会话，问一句「现在有哪些技能」。列表里出现 `legal-literature-analysis` 就装好了。

### 触发方式（任选一种）

- 直接说：「拆一下这篇论文 / 画论证图 / 做法学文献分析」；
- 上传 PDF/Word 后说：「用 legal-literature-analysis 处理它」；
- 有技能选择器的界面：点技能按钮选它，或输入框打 `/legal-literature-analysis`。

> **换个 AI 工具也能用**：这个技能是通用格式，Claude Code 等工具只要把目录放进它们的技能文件夹即可。

---

## 🎯 适合谁

- **法学生**：论文读不完、综述写不出——先把别人的论证拆成图，照着结构写自己的。
- **研究者**：快速判断一篇论文的论证骨架有没有硬伤（跳步、证据不足、未回应反方）。
- **想复现/仿写的**：先读透，再默写，再对照——比「照着原文改词」靠谱得多。

---

## 🧠 为什么不是玄学

- **400 篇国内 CLSCI 语料校准的语义基线**：论证信号词、11 学科画像、论证段模板、衔接搭配——拆解不靠临场拍脑袋；
- **论证图有机器校验**：原文引用与概括必须分开（防照抄）、被引者观点不能记到作者头上（归属铁律）、每条箭头必须写清「为什么成立」；
- **五维审稿测试**：覆盖概念/法条/逻辑/证据/格式五个维度，示例库全过；
- **引注两套体例分清**：参考文献表用 GB/T 7714-2025，页下脚注用《法学引注手册》，不混用。

---

## ⚠️ 诚实说明（很重要）

- 它帮你**拆**，不替你**想**：命题怎么切、关系怎么标，是分析判断，最终仍要你自己判断对错；
- **引注真实性**：脚注从原文提取，投稿前仍须人工核验；
- 图上的「关系」是作者论证的呈现，不代表本技能赞同该论证。

---

## 📖 术语看不懂？看这篇

`references/术语对照.md`——把本文档里出现的计算机词（命令行、依赖、JSON、pipeline、仓库……）全部翻译成法学人听得懂的话。

---

## 🧾 目录

```
SKILL.md · README.md · requirements.txt
references/   claim-graph-standard.md · reading-prompts.md · 术语对照.md · argument-grammar.md …
assets/       signal-lexicon.json · reading_prompts.json · templates/中国法学_style.docx
scripts/      pipeline.py · validate_claim_graph.py · build_report.py · extract_footnotes.py …
examples/     原本有400 个已拆示例（含基准文复现训练实跑）因为版权问题下架
tests/        单元测试 + 五维审稿测试
```
## 交流邮箱
461582455@qq.com
