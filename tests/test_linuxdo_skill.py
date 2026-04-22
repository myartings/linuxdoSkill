from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class LinuxDoSkillTests(unittest.TestCase):
    def run_script(self, *args: str) -> str:
        proc = subprocess.run(
            ["python3", *args],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        return proc.stdout.strip()

    def test_parse_topic_post_url(self) -> None:
        out = self.run_script(
            str(SCRIPTS / "parse_linuxdo_url.py"),
            "https://linux.do/t/topic/1588286/5?page=2",
        )
        data = json.loads(out)
        self.assertEqual(data["resource_type"], "topic_post")
        self.assertEqual(data["topic_id"], 1588286)
        self.assertEqual(data["post_number"], 5)
        self.assertEqual(data["page"], 2)

    def test_parse_category_url(self) -> None:
        out = self.run_script(
            str(SCRIPTS / "parse_linuxdo_url.py"),
            "https://linux.do/c/develop/42",
        )
        data = json.loads(out)
        self.assertEqual(data["resource_type"], "category")
        self.assertEqual(data["category_slug"], "develop")
        self.assertEqual(data["category_id"], 42)

    def test_extract_structured_topic_page(self) -> None:
        out = self.run_script(
            str(SCRIPTS / "extract_linuxdo_structured.py"),
            str(FIXTURES / "topic_page.html"),
            "--post-number",
            "5",
        )
        data = json.loads(out)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["title"], "测试主题标题 - 资源荟萃")
        self.assertEqual(data["category"], "资源荟萃")
        self.assertEqual(data["topic_id"], 1588286)
        self.assertEqual(data["post_count"], 1)
        self.assertEqual(data["posts"][0]["post_number"], 5)
        self.assertIn("第 5 楼内容", data["posts"][0]["content"])

    def test_extract_structured_challenge_page(self) -> None:
        out = self.run_script(
            str(SCRIPTS / "extract_linuxdo_structured.py"),
            str(FIXTURES / "cloudflare.html"),
        )
        data = json.loads(out)
        self.assertEqual(data["status"], "cloudflare_challenge")


if __name__ == "__main__":
    unittest.main()
