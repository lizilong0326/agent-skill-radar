"""The published candidate list must keep distinct, inspectable source records."""

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


DATA = Path(__file__).resolve().parent.parent / "data" / "rankings.json"


class RankingsDataTests(unittest.TestCase):
    def test_counts_links_licenses_and_platform_ranks(self):
        if not DATA.exists():
            self.skipTest("Rankings have not been collected")
        catalog = json.loads(DATA.read_text(encoding="utf-8"))
        allowed_hosts = {"github.com", "huggingface.co", "gitlab.com", "codeberg.org", "registry.modelcontextprotocol.io"}
        for kind in ("agent", "mcp"):
            items = catalog["items"][kind]
            self.assertEqual(catalog["counts"][kind], len(items))
            self.assertEqual(len({item["id"] for item in items}), len(items))
            github = [item for item in items if item["platform"] == "GitHub"]
            self.assertEqual([item["platform_rank"] for item in github], list(range(1, len(github) + 1)))
            self.assertEqual([item["popularity"]["value"] for item in github],
                             sorted((item["popularity"]["value"] for item in github), reverse=True))
            self.assertEqual(sum(item["top_200_github"] for item in github), min(200, len(github)))
            for item in items:
                self.assertEqual(item["kind"], kind)
                self.assertTrue(item["license"])
                self.assertTrue(item["evidence_excerpt"])
                for field in ("project_url", "source_url"):
                    parsed = urlparse(item[field])
                    self.assertEqual(parsed.scheme, "https")
                    self.assertIn(parsed.hostname, allowed_hosts)


if __name__ == "__main__":
    unittest.main()
