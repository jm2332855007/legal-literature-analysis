# -*- coding: utf-8 -*-
"""阅读任务包 + 脚注提取的回归测试。"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from gen_reading_prompts import main as gen_main  # noqa: E402
from extract_footnotes import extract_from_json, extract_from_md, resolve_qianyin  # noqa: E402


class TestReadingPackage(unittest.TestCase):
    def test_generates_package_with_slots(self):
        with tempfile.TemporaryDirectory() as td:
            ch = os.path.join(td, "chapters.json")
            json.dump({"chapters": [
                {"id": "ch1", "title_zh": "问题的提出", "role": "立论"},
                {"id": "ch2", "title_zh": "结语", "role": "回扣"},
            ]}, open(ch, "w", encoding="utf-8"), ensure_ascii=False)
            old = sys.argv
            sys.argv = ["gen_reading_prompts.py", "--out-dir", td, "--id", "t1",
                        "--title", "测试论文", "--chapters", ch]
            try:
                gen_main()
            finally:
                sys.argv = old
            d = os.path.join(td, "t1.reading")
            self.assertTrue(os.path.isdir(d))
            names = os.listdir(d)
            # 阶段一 / 逐章 / 追问 / 导图 / 复现三遍
            self.assertTrue(any("01_章节结构" in n for n in names))
            self.assertEqual(sum(1 for n in names if n.startswith("02_逐章精读")), 2)
            self.assertTrue(any("03_核心贡献" in n for n in names))
            self.assertTrue(any("05_思维导图" in n for n in names))
            self.assertTrue(any("06_复现训练_第1遍" in n for n in names))
            self.assertTrue(any("07_复现训练_第2遍" in n for n in names))
            self.assertTrue(any("08_复现训练_第3遍" in n for n in names))
            # 每个 prompt 末尾必须有输出槽
            for n in names:
                if n.endswith(".prompt.md") or n.startswith("06_"):
                    txt = open(os.path.join(d, n), encoding="utf-8").read()
                    self.assertIn("输出槽", txt, n)


class TestFootnotes(unittest.TestCase):
    def test_extract_md_mixed_brackets(self):
        md = "（1）参见甲文，第5页。\n〔2〕参见乙文。\n[3] See丙文。\n(4) 参见丁文。"
        fns = extract_from_md(md)
        self.assertEqual(set(fns), {"1", "2", "3", "4"})

    def test_resolve_qianyin_chain(self):
        fns = {"34": "See M. Van Smith, Preventing the Manipulation, 32 Hastings Law Journal 1585 (1981).",
               "52": "参见前引 [34], Smith 文, 第 1580 页。"}
        out = resolve_qianyin("52", fns)
        self.assertIn("Hastings Law Journal", out)

    def test_extract_from_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump([{"type": "page_footnote", "text": "（2）参见汪庆华《算法透明》，《比较法研究》2020年第6期。"},
                       {"type": "text", "text": "正文"}], f, ensure_ascii=False)
            p = f.name
        fns = extract_from_json(p)
        self.assertIn("2", fns)
        self.assertIn("汪庆华", fns["2"])
        os.unlink(p)


if __name__ == "__main__":
    unittest.main()
