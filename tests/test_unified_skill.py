# -*- coding: utf-8 -*-
"""Smoke tests for the unified legal-literature-analysis skill."""
import json
import os
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from legal_citations import build_self  # noqa: E402
from validate_claim_graph import check  # noqa: E402
from md_to_docx import convert  # noqa: E402
from build_report import build_report  # noqa: E402

EX = os.path.join(ROOT, "examples", "ao-shuanghong")


@unittest.skipUnless(os.path.exists(os.path.join(ROOT, "examples", "ao-shuanghong", "ao-shuanghong.claim-graph.json")), "示例数据未随仓库发布（本地保留时照常跑）")
class TestUnifiedSkill(unittest.TestCase):
    def test_example_artifacts_exist(self):
        for name in [
            "ao-shuanghong.md", "ao-shuanghong.paragraphs.json",
            "ao-shuanghong.structure.json", "ao-shuanghong.metadata.json",
            "ao-shuanghong.citations.json", "ao-shuanghong.claim-graph.json",
        ]:
            self.assertTrue(os.path.exists(os.path.join(EX, name)), name)

    def test_citation_build(self):
        meta = json.load(open(os.path.join(EX, "ao-shuanghong.metadata.json"), encoding="utf-8"))
        c = build_self(meta, page="92", quote_type="paraphrase")
        self.assertIn("敖双红", c["gb7714"])
        self.assertIn("法学评论", c["law_footnote"])
        self.assertIn("第92页", c["law_footnote"])

    def test_example_graph_passes_gate(self):
        g = json.load(open(os.path.join(EX, "ao-shuanghong.claim-graph.json"), encoding="utf-8"))
        errs, warns = check(g)
        self.assertEqual(errs, [])

    def test_report_builds_with_footnotes(self):
        g = os.path.join(EX, "ao-shuanghong.claim-graph.json")
        img = os.path.join(EX, "visuals", "ao-shuanghong.png")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "ao.report.md")
            r = build_report(g, img, out)
            self.assertGreater(r["footnotes"], 10)
            md = open(out, encoding="utf-8").read()
            self.assertIn("节点—原文—引注对照表", md)
            self.assertIn("第92页", md)

    def test_docx_has_real_footnote_and_image(self):
        meta = json.load(open(os.path.join(EX, "ao-shuanghong.metadata.json"), encoding="utf-8"))
        c = build_self(meta, page="92", quote_type="paraphrase")
        g = os.path.join(EX, "ao-shuanghong.claim-graph.json")
        img = os.path.join(EX, "visuals", "ao-shuanghong.png")
        with tempfile.TemporaryDirectory() as td:
            report = os.path.join(td, "ao.report.md")
            build_report(g, img, report)
            docx = os.path.join(td, "ao.report.docx")
            r = convert(report, docx)
            self.assertTrue(r.get("success"), r)
            with zipfile.ZipFile(docx) as z:
                xml = z.read("word/footnotes.xml").decode("utf-8", "replace")
                self.assertIn("敖双红", xml)
                doc = z.read("word/document.xml").decode("utf-8", "replace")
                self.assertIn("footnoteReference", doc)
                self.assertTrue(any("media" in n for n in z.namelist()))

    def test_scripts_exist(self):
        for name in ["pdf_to_md.py", "legal_metadata.py", "legal_citations.py",
                     "md_to_docx.py", "validate_claim_graph.py", "render_claim_graph.py",
                     "build_report.py", "build_data_package.py", "pipeline.py"]:
            self.assertTrue(os.path.exists(os.path.join(ROOT, "scripts", name)), name)
        skill = open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
        self.assertIn("解剖报告", skill)
        self.assertIn("数据包", skill)


if __name__ == "__main__":
    unittest.main()

