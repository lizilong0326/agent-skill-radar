import datetime as dt
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from radar.classifier import _valid_evidence, rule_classify
from radar.collector import build_items, extract_description, inactivity, item_paths, repo_kind, repo_record
from radar.taxonomy import GROUP_LABELS, TAG_GROUPS, TAXONOMY


class ClassificationTests(unittest.TestCase):
    def test_every_tag_has_a_visible_category(self):
        self.assertEqual(set(TAG_GROUPS), set(TAXONOMY))
        self.assertTrue(set(TAG_GROUPS.values()).issubset(GROUP_LABELS))

    def test_document_content_drives_tags_and_cites_source(self):
        result = rule_classify({"skills/example/SKILL.md": "Build React components and run Playwright end-to-end tests."})
        self.assertIn("frontend", result["tags"])
        self.assertIn("testing", result["tags"])
        self.assertTrue(all(entry["path"] == "skills/example/SKILL.md" for entry in result["evidence"]))

    def test_unverified_model_quote_is_rejected(self):
        documents = {"SKILL.md": "Build accessible React components."}
        self.assertFalse(_valid_evidence({"path": "SKILL.md", "excerpt": "Writes secure API services"}, documents))
        self.assertTrue(_valid_evidence({"path": "SKILL.md", "excerpt": "accessible React components"}, documents))

    def test_reference_list_does_not_become_capability(self):
        document = "---\ndescription: Helps users find and install agent skills\n---\n# Find Skills\nDiscover skills for a task.\n\n## Examples\n- React frontend design\n- Playwright testing\n- Cloud deployment"
        result = rule_classify({"skills/find-skills/SKILL.md": document})
        self.assertIn("skill-management", result["tags"])
        self.assertNotIn("frontend", result["tags"])
        self.assertNotIn("testing", result["tags"])

    def test_mirrored_skill_paths_are_deduplicated(self):
        tree = {"tree": [
            {"type": "blob", "path": "benchmarks/sample/SKILL.md"},
            {"type": "blob", "path": "backup/sample/SKILL.md"},
            {"type": "blob", "path": "skills/sample/SKILL.md"},
        ]}
        self.assertEqual(item_paths(tree, 10), ["skills/sample/SKILL.md"])

    def test_multiline_frontmatter_description_is_used(self):
        document = "---\nname: browser-helper\ndescription: >-\n  Automate browser actions on dynamic pages.\n  Fill forms and inspect results.\n---\n# Helper"
        self.assertEqual(extract_description(document), "Automate browser actions on dynamic pages. Fill forms and inspect results.")
        self.assertIn("browser", rule_classify({"SKILL.md": document})["tags"])

    def test_integration_mentions_do_not_define_repository_type(self):
        scraper = {"description": "An adaptive web scraping framework", "topics": ["mcp-server"]}
        self.assertEqual(repo_kind("# Scraper\nScrape and crawl sites with Python.\n\n## MCP integration", scraper), "tool")
        agent = {"description": "An open-source AI agent for the terminal", "topics": ["mcp-client"]}
        self.assertEqual(repo_kind("# CLI\nUses MCP servers as optional integrations.", agent), "agent")
        mcp = {"description": "Browser debugging server", "topics": ["mcp"]}
        self.assertEqual(repo_kind("# Browser DevTools\nIt acts as an MCP server for browser inspection.", mcp), "mcp")
        self.assertEqual(repo_kind("# Hermes Agent\nA coding assistant.", {"description": "The agent that grows with you", "topics": []}), "agent")
        self.assertEqual(repo_kind("# Design Plugin\nYour coding agent becomes the design engine.", {"description": "Your coding agent becomes the design engine", "topics": ["ai-agent"]}), "tool")

    def test_large_skill_repository_is_collected_over_successive_runs(self):
        class API:
            def readme(self, _):
                return "# Tool\nA collection of documented tools.", "README.md"

            def tree(self, _, __):
                return {"tree": [{"type": "blob", "path": "skills/{}/SKILL.md".format(name)} for name in "abc"]}

            def content(self, _, path):
                return "---\ndescription: Review code changes\n---\n# Review"

        repo = {"id": 7, "full_name": "org/tools", "url": "https://github.com/org/tools", "default_branch": "main",
                "description": "A tools collection", "topics": [], "pushed_at": "2026-09-28T00:00:00Z"}
        args = SimpleNamespace(max_items_per_repo=1, reclassify_all=False)
        records = []
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}):
            for expected in (1, 2, 3):
                records, _ = build_items(API(), repo, records, args, 0)
                self.assertEqual(sum(item["kind"] == "skill" for item in records), expected)
                self.assertEqual(repo["documents_pending"], 3 - expected)


class LifecycleTests(unittest.TestCase):
    def test_missing_history_is_not_zero_growth(self):
        raw = {"id": 123, "full_name": "org/repo", "html_url": "https://github.com/org/repo", "stargazers_count": 200,
               "forks_count": 0, "license": {"spdx_id": "MIT"}, "pushed_at": "2026-01-01T00:00:00Z"}
        with patch("radar.collector.utc_now", return_value=dt.datetime(2026, 9, 28, tzinfo=dt.timezone.utc)):
            repo = repo_record(raw)
            self.assertIsNone(repo["stars_60d"])
            self.assertEqual(inactivity(repo)[0], "archived")

    def test_stale_repository_with_observed_flat_stars_is_archived(self):
        raw = {"id": 123, "full_name": "org/repo", "html_url": "https://github.com/org/repo", "stargazers_count": 200,
               "forks_count": 0, "license": {"spdx_id": "MIT"}, "pushed_at": "2026-01-01T00:00:00Z"}
        previous = {"star_history": [{"date": "2026-07-01", "stars": 200}], "first_seen": "2026-07-01"}
        with patch("radar.collector.utc_now", return_value=dt.datetime(2026, 9, 28, tzinfo=dt.timezone.utc)):
            repo = repo_record(raw, previous)
            self.assertEqual(repo["stars_60d"], 0)
            self.assertEqual(inactivity(repo)[0], "archived")

    def test_flat_stars_archive_even_when_code_is_fresh(self):
        raw = {"id": 123, "full_name": "org/repo", "html_url": "https://github.com/org/repo", "stargazers_count": 200,
               "forks_count": 0, "license": {"spdx_id": "MIT"}, "pushed_at": "2026-09-27T00:00:00Z"}
        previous = {"star_history": [{"date": "2026-07-01", "stars": 200}], "first_seen": "2026-07-01"}
        with patch("radar.collector.utc_now", return_value=dt.datetime(2026, 9, 28, tzinfo=dt.timezone.utc)):
            self.assertEqual(inactivity(repo_record(raw, previous))[0], "archived")

    def test_thirty_days_without_push_enters_watch(self):
        repo = {"pushed_at": "2026-08-20T00:00:00Z", "archived": False, "stars_60d": None}
        with patch("radar.collector.utc_now", return_value=dt.datetime(2026, 9, 28, tzinfo=dt.timezone.utc)):
            self.assertEqual(inactivity(repo)[0], "watch")


if __name__ == "__main__":
    unittest.main()
