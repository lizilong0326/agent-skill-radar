import datetime as dt
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from radar.classifier import _valid_evidence, deepseek_classify, rule_classify
from radar.facets import classify_facets
from radar.collector import build_items, extract_description, inactivity, item_paths, repo_kind, repo_record
from radar.taxonomy import GROUP_LABELS, TAG_GROUPS, TAXONOMY


class ClassificationTests(unittest.TestCase):
    def test_workflow_and_industry_have_source_and_basis(self):
        result = classify_facets({"README.md": "The service lets clients book appointments online and manage scheduling.\nAccounting reports show cash flow."})
        self.assertIn("appointments", result["workflows"])
        self.assertIn("accounting", result["workflows"])
        matches = {entry["tag"]: entry for entry in result["industry_matches"]}
        self.assertEqual(matches["beauty"]["basis"], "inferred")
        self.assertEqual(matches["beauty"]["workflow"], "appointments")
        self.assertEqual(matches["finance"]["basis"], "explicit")
        self.assertEqual(matches["beauty"]["path"], "README.md")
        self.assertIn("appointments", matches["beauty"]["excerpt"])

    def test_generic_agent_and_payment_do_not_imply_industry(self):
        result = classify_facets({"SKILL.md": "Run coding agents and execute API payments for tools."})
        self.assertEqual(result["industry_matches"], [])

    def test_badges_and_image_names_do_not_become_business_evidence(self):
        doc = "[![Learn on Frappe School](https://img.shields.io/badge/School)](https://example.com)\n<img alt=\"booking-screen\" src=\"https://example.com/booking.png\">\nA self-hosted scheduling platform for people to book appointments."
        result = classify_facets({"README.md": doc})
        industries = {entry["tag"]: entry for entry in result["industry_matches"]}
        self.assertNotIn("education", industries)
        self.assertEqual(industries["beauty"]["basis"], "inferred")
        self.assertIn("scheduling platform", industries["beauty"]["excerpt"])

    def test_project_tags_ignore_metadata_and_unrelated_examples(self):
        doc = '---\nname: ecommerce-image-workflow\nen_name: "Ecommerce Image Workflow"\ndescription: Generate product images for online stores.\n---\nThis tool makes product images.\nThe transition does not use blocker recurrence accounting.\nChoose a domain, e.g. e-commerce or SaaS.'
        result = classify_facets({"SKILL.md": doc})
        matches = {entry["tag"]: entry for entry in result["industry_matches"]}
        self.assertEqual(matches["retail"]["basis"], "inferred")
        self.assertIn("product images", matches["retail"]["excerpt"])
        self.assertNotIn("finance", matches)

    def test_delivery_appointments_do_not_imply_barbershop(self):
        result = classify_facets({"SKILL.md": "Freight carriers charge extra for residential delivery and appointment scheduling."})
        self.assertIn("appointments", result["workflows"])
        self.assertNotIn("beauty", [entry["tag"] for entry in result["industry_matches"]])

    def test_incidental_billing_dashboard_and_support_examples_are_not_workflows(self):
        doc = "Generate a report, invoice, or multi-page document as PDF.\nGet an API key at https://vendor.example/dashboard.\nDo you offer customer support?\nBilling is handled by the cloud provider."
        self.assertEqual(classify_facets({"SKILL.md": doc})["workflows"], [])

    def test_classifier_uses_configured_model(self):
        requested = []
        response = {"choices": [{"message": {"content": json.dumps({"evidence": [], "tags": [], "confidence": "low", "summary_zh": ""})}}]}
        def fake_urlopen(request, timeout):
            requested.append(json.loads(request.data)["model"])
            return io.BytesIO(json.dumps(response).encode())
        with patch.dict("os.environ", {"DEEPSEEK_MODEL": "deepseek-v4-flash"}), patch(
            "radar.classifier.urllib.request.urlopen", side_effect=fake_urlopen
        ):
            deepseek_classify({"SKILL.md": "Review code changes."}, "skill", "test-key")
        self.assertEqual(requested, ["deepseek-v4-flash"])

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

    def test_removed_and_future_features_are_not_accepted(self):
        documents = {"README.md": "No enterprise features — Workflows have been removed. Calendar integrations can be added later from Settings."}
        self.assertFalse(_valid_evidence({"path": "README.md", "excerpt": "Workflows have been removed"}, documents))
        self.assertFalse(_valid_evidence({"path": "README.md", "excerpt": "Calendar integrations can be added later"}, documents))

    def test_quote_must_support_the_specific_capability(self):
        documents = {"README.md": "Projects: track tasks and budgets. Appointment scheduling platform for customers."}
        self.assertFalse(_valid_evidence({"tag": "product", "path": "README.md", "excerpt": "Projects: track tasks and budgets"}, documents))
        self.assertTrue(_valid_evidence({"tag": "scheduling", "path": "README.md", "excerpt": "Appointment scheduling platform for customers"}, documents))

    def test_reference_list_does_not_become_capability(self):
        document = "---\ndescription: Helps users find and install agent skills\n---\n# Find Skills\nDiscover skills for a task.\n\n## Examples\n- React frontend design\n- Playwright testing\n- Cloud deployment"
        result = rule_classify({"skills/find-skills/SKILL.md": document})
        self.assertIn("skill-management", result["tags"])
        self.assertNotIn("frontend", result["tags"])
        self.assertNotIn("testing", result["tags"])

    def test_readme_badges_do_not_hide_primary_capability(self):
        boilerplate = '<a href="https://example.com"><img src="https://img.shields.io/badge/x-y"></a>\n' * 30
        document = boilerplate + '# Firecrawl\nThe API to search, scrape, and interact with the web at scale.\n\n## Why it works\n'
        result = rule_classify({"README.md": document})
        self.assertIn("web-scraping", result["tags"])
        self.assertIn("scrape", result["evidence"][0]["excerpt"])

    def test_new_capability_categories_use_document_description(self):
        result = rule_classify({"SKILL.md": "---\ndescription: Audit WCAG accessibility and create PowerPoint slide decks.\n---\n# Assistant"})
        self.assertIn("accessibility", result["tags"])
        self.assertIn("presentations", result["tags"])

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

    def test_readme_language_navigation_is_not_a_description(self):
        readme = "# Tool\n\nEnglish(README.md) | 简体中文(README.zh-CN.md)\n\n<p align=\"center\">Collects job listings and helps candidates review which ones are worth applying to.</p>"
        self.assertEqual(extract_description(readme), "Collects job listings and helps candidates review which ones are worth applying to.")

    def test_readme_html_heading_precedes_navigation_and_badges(self):
        readme = '<h1><img src="logo.png">Tool</h1>\n\n<h4>A self-hosted appointment scheduling platform built for flexibility.</h4>\n\n<p><a href="#features">Features</a> • <a href="#start">Start</a> • <a href="#license">License</a></p>'
        self.assertEqual(extract_description(readme), "A self-hosted appointment scheduling platform built for flexibility.")

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
