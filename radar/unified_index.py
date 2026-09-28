"""Merge the document catalog and ranked candidates into one public index."""

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from .classifier import classify
from .enrich_tags import enrich_missing_tags
from .taxonomy import TAG_GROUPS, TAXONOMY, TAXONOMY_EN
from .translation import load_local_config, retained_translation, translate_catalog
from .use_cases import generate_use_cases, retained_use_case


ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog.json"
RANKINGS = ROOT / "data" / "rankings.json"
OUTPUTS = (ROOT / "data" / "index.json", ROOT / "site" / "data" / "index.json")


def canonical_url(value):
    """Use source identity, not display name, to identify the same project."""
    parsed = urlparse(value or "")
    path = parsed.path.rstrip("/").removesuffix(".git").lower()
    return parsed.netloc.lower() + path


def project_key(kind, url):
    return kind + ":" + canonical_url(url)


def merge_index(catalog, rankings, previous=None):
    previous = previous or {}
    previous_by_key = {row.get("canonical_key"): row for row in previous.get("items", []) if row.get("canonical_key")}
    repositories = copy.deepcopy(catalog.get("repositories", []))
    repo_by_id = {row["id"]: row for row in repositories}
    repo_by_url = {canonical_url(row.get("url")): row for row in repositories if row.get("url")}
    items = []
    project_items = {}

    for source in catalog.get("items", []):
        row = copy.deepcopy(source)
        repo = repo_by_id.get(row.get("repo_id"))
        if not repo:
            continue
        base = project_key(row["kind"], repo.get("url", ""))
        row["canonical_key"] = base + ":" + row.get("source_path", "") if row["kind"] == "skill" else base
        row["project_url"] = repo.get("url")
        row["source_platform"] = "GitHub"
        row["license"] = repo.get("license")
        row["popularity"] = {"metric": "stars", "value": repo.get("stars", 0), "platform": "GitHub"}
        row["review_state"] = "automated" if row.get("method") == "deepseek" else "preliminary"
        row["first_seen"] = previous_by_key.get(row["canonical_key"], {}).get("first_seen") or row.get("classified_at") or catalog.get("generated_at")
        row["evidence_excerpt"] = next((entry.get("excerpt") for entry in row.get("evidence", []) if entry.get("excerpt")), row.get("description", ""))
        row["last_checked_at"] = row.get("last_checked_at") or catalog.get("generated_at")
        old = previous_by_key.get(row["canonical_key"], {})
        if not row.get("tags") and old.get("tags") and old.get("description") == row.get("description") and old.get("content_hash") == row.get("content_hash"):
            row["tags"] = copy.deepcopy(old["tags"])
            row["evidence"] = copy.deepcopy(old.get("evidence", []))
            row["method"] = old.get("method", row.get("method"))
            row["confidence"] = old.get("confidence", row.get("confidence"))
        if old.get("tag_reviewed_hash") and old.get("description") == row.get("description") and old.get("content_hash") == row.get("content_hash"):
            row["tag_reviewed_hash"] = old["tag_reviewed_hash"]
        items.append(row)
        if row["kind"] != "skill":
            project_items[row["canonical_key"]] = row

    for kind in ("agent", "mcp"):
        for source in rankings.get("items", {}).get(kind, []):
            key = project_key(kind, source.get("project_url", ""))
            existing = project_items.get(key)
            if existing:
                # Retain the richer catalog classification and attach ranking provenance.
                existing.update({
                    "source_platform": source["platform"], "popularity": source["popularity"],
                    "platform_rank": source.get("platform_rank"), "top_200_github": source.get("top_200_github", False),
                    "ai_category": source.get("ai_category"), "registry_url": source.get("registry_url"),
                    "evidence_excerpt": source["evidence_excerpt"], "ranked_source_url": source["source_url"],
                    "last_checked_at": rankings.get("generated_at"),
                    "review_state": "automated" if source.get("ai_category") else existing["review_state"],
                })
                continue

            repo = repo_by_url.get(canonical_url(source["project_url"]))
            if not repo:
                repo_id = "source:" + canonical_url(source["project_url"])
                metric = source.get("popularity") or {}
                repo = {
                    "id": repo_id, "full_name": urlparse(source["project_url"]).path.strip("/"),
                    "url": source["project_url"], "description": source.get("description", ""),
                    "stars": metric.get("value", 0) if metric.get("metric") == "stars" else 0,
                    "stars_30d": None, "pushed_at": source.get("last_updated"),
                    "license": source.get("license"), "status": "active", "source_platform": source["platform"],
                }
                repo_by_url[canonical_url(source["project_url"])] = repo
                repo_by_id[repo_id] = repo
                repositories.append(repo)
            old = previous_by_key.get(key, {})
            description = source.get("description") or ""
            if len(description) < 50 and len(source.get("evidence_excerpt") or "") > len(description) + 20:
                description = source["evidence_excerpt"]
            source_path = urlparse(source["source_url"]).path.rsplit("/", 1)[-1] or "README.md"
            excerpt = source.get("evidence_excerpt") or ""
            classification = classify({source_path: excerpt}, kind, use_ai=False) if excerpt else {}
            row = {
                "id": source["id"], "canonical_key": key, "repo_id": repo["id"], "kind": kind,
                "name": source["name"], "description": description,
                "source_path": source_path, "source_url": source["source_url"],
                "project_url": source["project_url"], "evidence_excerpt": excerpt,
                "source_platform": source["platform"], "license": source.get("license"),
                "popularity": source.get("popularity"), "platform_rank": source.get("platform_rank"),
                "top_200_github": source.get("top_200_github", False),
                "registry_url": source.get("registry_url"), "evidence_url": source.get("evidence_url"),
                "ai_category": source.get("ai_category"),
                "review_state": "automated" if source.get("ai_category") else "preliminary",
                "method": classification.get("method", "rules"), "confidence": classification.get("confidence", "low"),
                "tags": classification.get("tags", []), "evidence": classification.get("evidence", []),
                "workflows": classification.get("workflows", []),
                "workflow_evidence": classification.get("workflow_evidence", []),
                "industry_matches": classification.get("industry_matches", []),
                "facets_source": "source_excerpt",
                "status": "active", "status_reason": "",
                "first_seen": old.get("first_seen") or rankings.get("generated_at"),
                "last_checked_at": rankings.get("generated_at"),
            }
            row.update(retained_translation(old, description))
            row.update(retained_use_case(old, description))
            if old.get("tags") and old.get("description") == description and old.get("evidence_excerpt") == excerpt:
                row["tags"] = copy.deepcopy(old["tags"])
                row["evidence"] = copy.deepcopy(old.get("evidence", []))
                row["method"] = old.get("method", row["method"])
                row["confidence"] = old.get("confidence", row["confidence"])
            if old.get("tag_reviewed_hash") and old.get("description") == description and old.get("evidence_excerpt") == excerpt:
                row["tag_reviewed_hash"] = old["tag_reviewed_hash"]
            items.append(row)
            project_items[key] = row

    counts = Counter(row["kind"] for row in items if row.get("status") == "active")
    result = {key: copy.deepcopy(value) for key, value in catalog.items() if key not in ("items", "repositories")}
    result.update({
        "schema_version": 4, "generated_at": max(catalog.get("generated_at") or "", rankings.get("generated_at") or ""),
        "source_snapshots": {"catalog": catalog.get("generated_at"), "rankings": rankings.get("generated_at")},
        "counts": {"all": sum(counts.values()), **{kind: counts.get(kind, 0) for kind in ("skill", "agent", "mcp", "tool")}},
        "repositories": repositories, "items": items,
    })
    result["taxonomy"] = {slug: definition["label"] for slug, definition in TAXONOMY.items()}
    result["taxonomy_en"] = dict(TAXONOMY_EN)
    result["tag_groups"] = dict(TAG_GROUPS)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-ai-calls", type=int, default=0, help="optional translation and summary calls")
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    rankings = json.loads(RANKINGS.read_text(encoding="utf-8"))
    previous = json.loads(OUTPUTS[0].read_text(encoding="utf-8")) if OUTPUTS[0].exists() else None
    merged = merge_index(catalog, rankings, previous)
    remaining_calls = args.max_ai_calls
    if remaining_calls:
        load_local_config()
        # Repository descriptions duplicate most project descriptions; translate cards only.
        used, pending_translation, _ = translate_catalog({"repositories": [], "items": merged["items"]}, remaining_calls)
        remaining_calls -= used
        summary_calls, pending_summaries = generate_use_cases(merged, remaining_calls)
        remaining_calls -= summary_calls
        print("Enrichment calls:", used + summary_calls, "translation pending:", pending_translation,
              "summaries pending:", pending_summaries, flush=True)
    print("Capability enrichment:", enrich_missing_tags(merged, remaining_calls), flush=True)
    for path in OUTPUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved unified index:", merged["counts"], flush=True)


if __name__ == "__main__":
    main()
