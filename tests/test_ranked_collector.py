"""Regression checks for false positives observed during ranking discovery."""

import unittest

from radar.ranked_collector import evidence_for, lead_lines, select_records


class RankedCollectorTests(unittest.TestCase):
    def test_frontmatter_is_not_cited_as_feature_evidence(self):
        readme = "---\ntitle: Agent Quiz\ndescription: Test agent knowledge\n---\n# Quiz\nAnswer questions about agents."
        self.assertNotIn("title: Agent Quiz", lead_lines(readme))

    def test_educational_agent_result_is_excluded(self):
        repo = {"name": "Agent Course", "description": "AI agent course with quizzes"}
        self.assertIsNone(evidence_for("agent", repo, "# Agent Course\nLearn how to use agents."))

    def test_primary_agent_is_retained(self):
        repo = {"name": "coding-agent", "description": "Open-source coding agent for software development"}
        self.assertIn("agent", evidence_for("agent", repo, "# Coding Agent\nA coding agent that edits and tests code."))

    def test_mcp_sdk_and_incidental_integration_are_excluded(self):
        sdk = {"name": "fastmcp", "description": "Framework for building MCP servers and clients"}
        database = {"name": "dbx", "description": "Database app with AI and MCP Server integration"}
        self.assertIsNone(evidence_for("mcp", sdk, "# FastMCP\nBuild MCP servers and clients with this SDK."))
        self.assertIsNone(evidence_for("mcp", database, "# DBX\nDatabase UI with an optional MCP server."))

    def test_primary_mcp_server_is_retained(self):
        repo = {"name": "github-mcp-server", "description": "GitHub's official MCP Server"}
        self.assertIn("MCP", evidence_for("mcp", repo, "# GitHub MCP Server\nThe GitHub MCP Server connects AI tools to GitHub."))

    def test_mcp_evidence_prefers_function_over_image_and_recommendation(self):
        repo = {"name": "firecrawl-mcp-server", "description": "Firecrawl MCP server"}
        readme = ('<img alt="MCP server"\n src="https://example.com/mcp.png">\n'
                  'I recommend using another MCP server instead.\n'
                  'A Model Context Protocol (MCP) server that brings [Firecrawl](https://example.com) search to AI agents.')
        self.assertEqual(
            evidence_for("mcp", repo, readme),
            'A Model Context Protocol (MCP) server that brings Firecrawl search to AI agents.',
        )

    def test_agent_evidence_can_follow_license_preamble(self):
        repo = {"name": "Qwen-Agent", "description": "Agent framework"}
        preamble = "\n".join("Licensed under Apache, line " + str(n) for n in range(12))
        readme = preamble + "\nQwen-Agent is a framework for developing LLM applications with tools."
        self.assertIn("framework for developing", evidence_for("agent", repo, readme))

    def test_refresh_without_ai_key_keeps_reviewed_entries_before_preliminary(self):
        rows = [
            {"id": "popular-preliminary", "popularity": {"value": 1000}, "ai_category": None},
            {"id": "another-preliminary", "popularity": {"value": 100}, "ai_category": None},
            {"id": "reviewed", "popularity": {"value": 20}, "ai_category": "agent_app"},
        ]
        self.assertEqual([row["id"] for row in select_records(rows, 2, "")],
                         ["popular-preliminary", "reviewed"])
        self.assertEqual([row["id"] for row in select_records(rows, 2, "configured-key")],
                         ["popular-preliminary", "another-preliminary"])


if __name__ == "__main__":
    unittest.main()
