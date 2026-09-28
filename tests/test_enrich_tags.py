"""Capability labels must be supported by the cited source text."""

import unittest
from unittest.mock import patch

from radar.classifier import rule_classify
from radar.enrich_tags import _verified_evidence, enrich_missing_tags, source_texts, tag_source_hash


class EnrichTagsTests(unittest.TestCase):
    def test_project_description_keeps_its_own_citation(self):
        item = {"id": "github:owner/coder", "kind": "agent", "status": "active",
                "description": "An open-source coding agent that edits your code.",
                "evidence_excerpt": "This agent runs in your terminal.",
                "project_url": "https://github.com/owner/coder",
                "source_url": "https://github.com/owner/coder/blob/main/README.md",
                "source_path": "README.md", "tags": []}
        sources = source_texts(item)
        self.assertEqual(sources[0]["url"], item["project_url"])
        self.assertEqual(sources[1]["url"], item["source_url"])
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}), patch("radar.enrich_tags.load_local_config"):
            result = enrich_missing_tags({"items": [item]})
        self.assertEqual(result["rule_tagged"], 1)
        self.assertIn("coding-assistance", item["tags"])
        self.assertEqual(item["evidence"][0]["url"], item["project_url"])

    def test_model_quote_must_appear_in_cited_source(self):
        source = {"text": "A local multi-agent harness for coding teams.", "path": "README.md",
                  "url": "https://github.com/owner/agent/blob/main/README.md"}
        self.assertIsNone(_verified_evidence("coding-assistance", source, "Automates browser testing."))
        self.assertIsNone(_verified_evidence("unknown", source, "A local multi-agent harness"))
        self.assertEqual(_verified_evidence("agents", source, "A local multi-agent harness")["url"], source["url"])

    def test_project_type_is_not_a_development_capability(self):
        source = {"text": "An official hosted MCP server for calendar access.", "path": "README.md",
                  "url": "https://github.com/owner/mcp/blob/main/README.md"}
        self.assertIsNone(_verified_evidence("mcp-development", source, "An official hosted MCP server"))
        source["text"] = "An open-source AI agent in your terminal."
        self.assertIsNone(_verified_evidence("agents", source, "An open-source AI agent"))

    def test_specific_functions_can_be_tagged_without_using_project_type(self):
        self.assertIn("communication", rule_classify({"description": "WhatsApp MCP server"})["tags"])
        self.assertIn("agent-workflow", rule_classify({"description": "SDK for multi-agent coding workflows"})["tags"])

    def test_unchanged_insufficient_source_is_not_sent_to_model_again(self):
        item = {"id": "github:owner/agent", "kind": "agent", "status": "active", "tags": [],
                "description": "A personal AI agent.", "evidence_excerpt": "A personal AI agent.",
                "source_url": "https://github.com/owner/agent/blob/main/README.md"}
        item["tag_reviewed_hash"] = tag_source_hash(item)
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}), \
             patch("radar.enrich_tags.load_local_config"), patch("radar.enrich_tags._ai_batch") as batch:
            result = enrich_missing_tags({"items": [item]}, max_ai_calls=1)
        batch.assert_not_called()
        self.assertEqual(result["remaining"], 1)


if __name__ == "__main__":
    unittest.main()
