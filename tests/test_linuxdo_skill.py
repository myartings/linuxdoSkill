from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Allow direct import of scripts (search_linuxdo imports parse_linuxdo_url)
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import search_linuxdo  # noqa: E402


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


class NormalizeUrlTests(unittest.TestCase):
    def test_strips_trailing_quote_and_comma(self) -> None:
        self.assertEqual(
            search_linuxdo.normalize_url('https://linux.do/t/topic/123",'),
            "https://linux.do/t/topic/123",
        )

    def test_decodes_percent_encoding(self) -> None:
        url = search_linuxdo.normalize_url(
            "https://linux.do/t/topic/%E6%B5%8B%E8%AF%95/5"
        )
        self.assertEqual(url, "https://linux.do/t/topic/测试/5")

    def test_replaces_unicode_slash_escape(self) -> None:
        # / is JSON unicode escape for '/'
        url = search_linuxdo.normalize_url(
            "https://linux.do/t/topic/123\\u002F5"
        )
        self.assertEqual(url, "https://linux.do/t/topic/123/5")

    def test_plain_url_unchanged(self) -> None:
        url = "https://linux.do/t/topic/999"
        self.assertEqual(search_linuxdo.normalize_url(url), url)


class ResultPriorityTests(unittest.TestCase):
    def test_topic_before_category_before_tag_before_user(self) -> None:
        urls = [
            "https://linux.do/u/alice",
            "https://linux.do/c/develop/42",
            "https://linux.do/t/topic/123",
            "https://linux.do/tag/resource",
        ]
        urls.sort(key=search_linuxdo.result_priority)
        self.assertTrue(urls[0].startswith("https://linux.do/t/"))
        self.assertTrue(urls[1].startswith("https://linux.do/c/"))
        self.assertTrue(urls[2].startswith("https://linux.do/tag/"))
        self.assertTrue(urls[3].startswith("https://linux.do/u/"))

    def test_unknown_path_is_lowest_priority(self) -> None:
        unknown = "https://linux.do/unknown/path"
        topic = "https://linux.do/t/topic/1"
        urls = [unknown, topic]
        urls.sort(key=search_linuxdo.result_priority)
        self.assertEqual(urls[0], topic)
        self.assertEqual(urls[1], unknown)


class ExtractResultsBraveHtmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (FIXTURES / "brave_search.html").read_text(encoding="utf-8")
        cls.results = search_linuxdo.extract_results(cls.html)

    def test_homepage_is_excluded(self) -> None:
        self.assertNotIn("https://linux.do/", self.results)

    def test_guidelines_url_is_excluded(self) -> None:
        self.assertNotIn("https://linux.do/guidelines?tl=en", self.results)

    def test_non_linux_do_url_is_excluded(self) -> None:
        for url in self.results:
            self.assertTrue(url.startswith("https://linux.do/"), url)

    def test_topic_links_are_present(self) -> None:
        self.assertIn("https://linux.do/t/topic/1234567/1", self.results)
        self.assertIn("https://linux.do/t/topic/9999999/3", self.results)

    def test_category_link_is_present(self) -> None:
        self.assertIn("https://linux.do/c/develop/42", self.results)

    def test_duplicates_removed(self) -> None:
        self.assertEqual(
            self.results.count("https://linux.do/t/topic/1234567/1"), 1
        )

    def test_topic_sorted_before_category(self) -> None:
        topic_idx = next(
            i for i, u in enumerate(self.results) if "/t/" in u
        )
        cat_idx = next(
            i for i, u in enumerate(self.results) if "/c/" in u
        )
        self.assertLess(topic_idx, cat_idx)

    def test_percent_encoded_url_is_decoded(self) -> None:
        self.assertIn("https://linux.do/t/topic/测试/5", self.results)


class ExtractBingRssResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        xml_text = (FIXTURES / "bing_rss.xml").read_text(encoding="utf-8")
        cls.results = search_linuxdo.extract_bing_rss_results(xml_text)

    def test_topic_links_are_present(self) -> None:
        self.assertIn("https://linux.do/t/topic/9876543/2", self.results)
        self.assertIn("https://linux.do/t/topic/1111111", self.results)

    def test_homepage_is_excluded(self) -> None:
        self.assertNotIn("https://linux.do/", self.results)

    def test_non_linux_do_urls_are_excluded(self) -> None:
        self.assertNotIn("https://example.com/some/page", self.results)

    def test_duplicates_removed(self) -> None:
        self.assertEqual(
            self.results.count("https://linux.do/t/topic/9876543/2"), 1
        )

    def test_topic_sorted_before_user(self) -> None:
        topic_idx = next(
            i for i, u in enumerate(self.results) if "/t/" in u
        )
        user_idx = next(
            i for i, u in enumerate(self.results) if "/u/" in u
        )
        self.assertLess(topic_idx, user_idx)


if __name__ == "__main__":
    unittest.main()
