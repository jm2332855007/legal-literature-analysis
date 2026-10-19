#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成法学论文阅读/复现的可执行提示词任务包。

用法：
  python gen_reading_prompts.py --out-dir out/ao --id ao --title "标题" \
      [--structure out/ao/ao.structure.json] [--chapters chapters.json]

输出（<out-dir>/<id>.reading/）：
  00_README.md            运行顺序 + 产出槽说明
  01_章节结构.prompt.md    阶段一（只回 JSON）
  02_逐章精读_<n>_<标题>.prompt.md  阶段二（按章节逐个；无章节信息时给通用模板）
  03_核心贡献.prompt.md
  04_局限与未决.prompt.md
  05_思维导图.prompt.md
  06_复现训练_第1遍_补结构.md
  07_复现训练_第2遍_补规范依据.md
  08_复现训练_第3遍_补反方回应.md

每个 .prompt.md 末尾附「输出槽」，agent 或用户把模型回复粘贴进去即完成一轮。
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
ASSETS = os.path.join(SKILL, "assets", "reading_prompts.json")


def load_prompts():
    return json.load(open(ASSETS, encoding="utf-8"))


def slot(title, hint=""):
    return f"\n\n---\n\n## 输出槽：{title}\n\n<!-- {hint or '把模型回复粘贴到此处'} -->\n\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--id", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--structure", default="")
    ap.add_argument("--chapters", default="")
    args = ap.parse_args()

    doc_id = args.id or "paper"
    title = args.title
    out = os.path.join(os.path.abspath(args.out_dir), f"{doc_id}.reading")
    os.makedirs(out, exist_ok=True)
    P = load_prompts()

    chapters = []
    if args.chapters and os.path.exists(args.chapters):
        data = json.load(open(args.chapters, encoding="utf-8-sig"))
        chapters = data.get("chapters", data if isinstance(data, list) else [])
    elif args.structure and os.path.exists(args.structure):
        st = json.load(open(args.structure, encoding="utf-8-sig"))
        title = title or st.get("title", "")
        chapters = [{"id": f"ch{i+1}", "title_zh": s.get("heading", ""), "role": ""}
                    for i, s in enumerate(st.get("sections", [])) if s.get("heading")]

    def w(name, text):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return name

    made = []
    made.append(w("00_README.md",
                  f"# 阅读任务包：{title or doc_id}\n\n"
                  "运行顺序：01 → 02（逐章）→ 03 → 04 → 05 → 06/07/08（复现训练三遍）。\n"
                  "每个文件末尾有「输出槽」，把模型回复粘贴进去即完成该轮。\n\n"
                  "验收：01 返回合法 JSON；02 每章六问齐全；03/04 各三条以上判断；05 四固定分支齐全且含“规范结论”；06-08 每遍有“补上了什么/还差什么”。\n"))

    made.append(w("01_章节结构.prompt.md", P["chapter_plan_prompt"] + slot("chapters JSON")))

    if chapters:
        for i, ch in enumerate(chapters, 1):
            t = ch.get("title_zh") or ch.get("title") or f"第{i}章"
            role = ch.get("role", "")
            prompt = P["chapter_template"].replace("{{title_zh}}", t).replace("{{role}}", role or "（待判定）")
            safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", t)[:24]
            made.append(w(f"02_逐章精读_{i}_{safe}.prompt.md", prompt + slot(f"第{i}章精读：{t}")))
    else:
        made.append(w("02_逐章精读_通用模板.prompt.md",
                      P["chapter_template"] + slot("逐章精读（先跑 01 拿到章节后再复制每章）")))

    made.append(w("03_核心贡献.prompt.md", P["q_core_prompt"] + slot("核心贡献与学说定位")))
    made.append(w("04_局限与未决.prompt.md", P["q_limits_prompt"] + slot("局限与未决问题")))
    made.append(w("05_思维导图.prompt.md", P["mindmap_prompt"] + slot("思维导图 Markdown")))

    repro = P["repro"]
    made.append(w("06_复现训练_第1遍_补结构.md",
                  repro["step1_skeleton"] + "\n\n---\n\n## 默写提纲（不看原文）\n\n" + repro["step2_outline"]
                  + "\n\n## 输出槽：第 1 遍（只补结构）\n\n<!-- 章节命题序列必须与原骨架同构；填完回复“补上了什么/还差什么” -->\n\n"))
    made.append(w("07_复现训练_第2遍_补规范依据.md",
                  repro["step3_compare"] + "\n\n## 输出槽：第 2 遍（只补规范依据）\n\n<!-- 法条/判例与命题一一对应；差异类型：缺/弱/偏/多 -->\n\n"))
    made.append(w("08_复现训练_第3遍_补反方回应.md",
                  repro["step4_checklist"] + "\n\n## 输出槽：第 3 遍（只补反方回应）\n\n<!-- 每条预设施辩 + 一句回应；缺口标“未回应” -->\n\n"))

    print(json.dumps({"status": "success", "reading_dir": out, "files": len(made)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
