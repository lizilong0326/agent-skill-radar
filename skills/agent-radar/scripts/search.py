#!/usr/bin/env python3
"""Read the published catalog without making GitHub or DeepSeek API calls."""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


DEFAULT_URL = "https://raw.githubusercontent.com/lizilong0326/agent-skill-radar/main/data/catalog.json"


def get_catalog(source):
    if source.startswith("https://"):
        request = urllib.request.Request(source, headers={"User-Agent": "agent-skill-radar-skill"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    with open(source, encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser(description="Search the Agent Skill Radar public index")
    parser.add_argument("query", nargs="?", default="", help="task, capability, or project keyword")
    parser.add_argument("--kind", choices=["skill", "agent", "mcp", "tool"])
    parser.add_argument("--tag", help="taxonomy slug, such as design or testing")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--include-inactive", action="store_true")
    parser.add_argument("--catalog", help="local JSON file or HTTPS URL")
    args = parser.parse_args()

    local = Path(__file__).resolve().parents[3] / "data" / "catalog.json"
    source = args.catalog or os.getenv("AGENT_RADAR_CATALOG_URL") or (str(local) if local.exists() else DEFAULT_URL)
    try:
        catalog = get_catalog(source)
    except (OSError, ValueError) as exc:
        print("Could not read catalog:", exc, file=sys.stderr)
        return 1
    repos = {repo["id"]: repo for repo in catalog.get("repositories", [])}
    query = args.query.casefold().strip()
    matches = []
    for item in catalog.get("items", []):
        repo = repos.get(item.get("repo_id"))
        if not repo or (not args.include_inactive and item.get("status") != "active"):
            continue
        if args.kind and item.get("kind") != args.kind:
            continue
        if args.tag and args.tag not in item.get("tags", []):
            continue
        tag_names = " ".join(catalog.get("taxonomy", {}).get(tag, tag) for tag in item.get("tags", []))
        haystack = " ".join((item.get("name", ""), item.get("description", ""), item.get("summary_zh", ""), repo.get("full_name", ""), tag_names)).casefold()
        if query and query not in haystack:
            continue
        matches.append((item, repo))
    matches.sort(key=lambda pair: pair[1].get("stars", 0), reverse=True)
    print("Catalog updated:", catalog.get("generated_at", "unknown"), "| results:", len(matches))
    for item, repo in matches[:max(1, min(args.limit, 50))]:
        print("\n{} [{}] — {}".format(item.get("name"), item.get("kind"), repo.get("full_name")))
        print("  {}".format(item.get("summary_zh") or item.get("description") or "No description"))
        print("  Tags: {} | method: {} | repository Stars: {} | 30d growth: {}".format(
            ", ".join(item.get("tags", [])) or "unclassified", item.get("method", "unknown"),
            repo.get("stars", 0), repo.get("stars_30d") if repo.get("stars_30d") is not None else "history unavailable"))
        for evidence in item.get("evidence", [])[:2]:
            print("  Evidence: {} — {}".format(evidence.get("path"), evidence.get("excerpt", "")[:120]))
        print("  Source:", item.get("source_url"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
