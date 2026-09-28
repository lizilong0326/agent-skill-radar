"""Checks that the published directory keeps source identity and citations."""

import json
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from radar.unified_index import canonical_url, merge_index


ROOT = Path(__file__).resolve().parent.parent


class UnifiedIndexTests(unittest.TestCase):
    def test_published_index_is_one_deduplicated_catalog(self):
        catalog = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
        rankings = json.loads((ROOT / "data/rankings.json").read_text(encoding="utf-8"))
        index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
        site_copy = json.loads((ROOT / "site/data/index.json").read_text(encoding="utf-8"))
        self.assertEqual(index, site_copy)
        active = [item for item in index["items"] if item["status"] == "active"]
        counts = Counter(item["kind"] for item in active)
        self.assertEqual(index["counts"]["all"], len(active))
        self.assertEqual({kind: index["counts"][kind] for kind in ("skill", "agent", "mcp", "tool")},
                         {kind: counts[kind] for kind in ("skill", "agent", "mcp", "tool")})
        self.assertEqual(len({item["canonical_key"] for item in index["items"]}), len(index["items"]))
        repos = {repo["id"]: repo for repo in catalog["repositories"]}
        catalog_projects = {(item["kind"], canonical_url(repos[item["repo_id"]]["url"]))
                            for item in catalog["items"] if item["kind"] != "skill"}
        ranking_items = [item for kind in ("agent", "mcp") for item in rankings["items"][kind]]
        overlaps = sum((item["kind"], canonical_url(item["project_url"])) in catalog_projects
                       for item in ranking_items)
        self.assertEqual(len(index["items"]), len(catalog["items"]) + len(ranking_items) - overlaps)
        for item in active:
            self.assertIn(item["source_platform"], {"GitHub", "Hugging Face Spaces", "GitLab", "Codeberg"})
            self.assertTrue(item["evidence_excerpt"])
            for field in ("project_url", "source_url"):
                parsed = urlparse(item[field])
                self.assertEqual(parsed.scheme, "https")
                self.assertTrue(parsed.hostname)

    def test_project_dedup_does_not_collapse_distinct_skills(self):
        repo = {"id": 1, "full_name": "owner/project", "url": "https://github.com/owner/project",
                "stars": 10, "license": "MIT", "pushed_at": "2026-09-01", "status": "active"}
        skill = {"repo_id": 1, "kind": "skill", "name": "one", "description": "Skill one",
                 "source_path": "one/SKILL.md", "source_url": repo["url"] + "/blob/main/one/SKILL.md",
                 "status": "active", "method": "rules", "evidence": [{"excerpt": "Skill one"}]}
        agent = {"repo_id": 1, "kind": "agent", "name": "project", "description": "Agent project",
                 "source_path": "README.md", "source_url": repo["url"] + "/blob/main/README.md",
                 "status": "active", "method": "deepseek", "tags": ["code"],
                 "evidence": [{"excerpt": "Agent project"}]}
        catalog = {"generated_at": "2026-09-01", "repositories": [repo], "items": [skill, {**skill,
            "name": "two", "source_path": "two/SKILL.md", "source_url": repo["url"] + "/blob/main/two/SKILL.md"}, agent]}
        ranked = {"generated_at": "2026-09-02", "items": {"agent": [{
            "id": "github:owner/project", "name": "project", "project_url": repo["url"] + "/",
            "source_url": agent["source_url"], "platform": "GitHub", "evidence_excerpt": "Agent project",
            "popularity": {"metric": "stars", "value": 10}, "ai_category": "agent_app",
            "platform_rank": 1, "top_200_github": True,
        }], "mcp": []}}
        result = merge_index(catalog, ranked)
        self.assertEqual(result["counts"], {"all": 3, "skill": 2, "agent": 1, "mcp": 0, "tool": 0})
        self.assertEqual(len(result["items"]), 3)
        merged_agent = next(item for item in result["items"] if item["kind"] == "agent")
        self.assertEqual(merged_agent["tags"], ["code"])
        self.assertEqual(merged_agent["platform_rank"], 1)
        self.assertTrue(merged_agent["top_200_github"])


if __name__ == "__main__":
    unittest.main()
