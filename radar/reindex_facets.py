"""Recheck all indexed tools against their current source documents.

This maintenance command updates business facets without changing existing
capability classifications. It is useful after changing the facet taxonomy.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from .collector import DATA_FILE, SITE_DATA_FILE, GitHubAPI, extract_description, iso_now, load_catalog, write_json
from .classifier import rule_classify
from .facets import INDUSTRY_LABELS_EN, INDUSTRY_LABELS_ZH, WORKFLOW_LABELS_EN, WORKFLOW_LABELS_ZH, classify_facets
from .taxonomy import GROUP_LABELS, GROUP_LABELS_EN, TAG_GROUPS, TAXONOMY, TAXONOMY_EN
from .translation import load_local_config, retained_translation, translate_catalog
from .use_cases import generate_use_cases, retained_use_case


def main():
    parser = argparse.ArgumentParser(description="Recheck workflow and industry evidence from GitHub documents")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--capabilities", action="store_true", help="also refresh preliminary capability labels from documents")
    args = parser.parse_args()
    load_local_config()
    catalog = load_catalog()
    repos = {repo["id"]: repo for repo in catalog["repositories"]}
    api = GitHubAPI()

    def inspect(item):
        repo = repos.get(item["repo_id"])
        if not repo:
            return item["id"], None, None, None
        path = item["source_path"]
        try:
            content = api.content(repo["full_name"], path)
        except Exception:
            return item["id"], None, None, None
        if not content:
            return item["id"], None, None, None
        rules = rule_classify({path: content}) if args.capabilities and item.get("method") == "rules" else None
        return item["id"], classify_facets({path: content}), rules, content

    results = {}
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 16))) as pool:
        futures = [pool.submit(inspect, item) for item in catalog["items"]]
        for index, future in enumerate(as_completed(futures), 1):
            item_id, facets, rules, content = future.result()
            if facets:
                results[item_id] = (facets, rules, content)
            if index % 50 == 0:
                print("Documents checked:", index, "/", len(futures), flush=True)

    fix_descriptions = {"calcom/cal.diy", "alextselegidis/easyappointments"}
    for item in catalog["items"]:
        result = results.get(item["id"])
        if not result:
            continue
        facets, rules, content = result
        item.update(facets)
        if rules:
            item.update(rules)
            item["classified_at"] = iso_now()
        repo = repos[item["repo_id"]]
        if item["kind"] == "tool" and repo["full_name"] in fix_descriptions:
            caution = next((line.strip(" >") for line in content.splitlines() if "personal, non-production use" in line.lower()), "")
            repo["usage_note_zh"] = "官方 README 建议仅用于个人、非生产环境。" if caution else ""
            repo["usage_note_en"] = "The README recommends personal, non-production use only." if caution else ""
            repo["usage_note_excerpt"] = caution[:300]
            description = extract_description(content, repo["description"])
            if description != item.get("description"):
                old = item.copy()
                item["description"] = description
                for field in ("description_zh", "description_en", "description_zh_source", "description_en_source", "description_translation_hash"):
                    item.pop(field, None)
                item.update(retained_translation(old, description))
                for field in ("use_case_zh", "use_case_en", "use_case_hash"):
                    item.pop(field, None)
                item.update(retained_use_case(old, description))

    catalog.update({
        "schema_version": 3,
        "generated_at": iso_now(),
        "workflow_labels": WORKFLOW_LABELS_ZH,
        "workflow_labels_en": WORKFLOW_LABELS_EN,
        "industry_labels": INDUSTRY_LABELS_ZH,
        "industry_labels_en": INDUSTRY_LABELS_EN,
        "taxonomy": {key: value["label"] for key, value in TAXONOMY.items()},
        "taxonomy_en": TAXONOMY_EN,
        "tag_groups": TAG_GROUPS,
        "group_labels": GROUP_LABELS,
        "group_labels_en": GROUP_LABELS_EN,
    })
    translated, pending, _ = translate_catalog(catalog, 5)
    summary_calls, summary_pending = generate_use_cases(catalog, 5 - translated)
    write_json(DATA_FILE, catalog)
    write_json(SITE_DATA_FILE, catalog)
    print("Facet documents updated:", len(results), "/", len(catalog["items"]), "translation calls:", translated, "pending:", pending, "use-case calls:", summary_calls, "summaries pending:", summary_pending)


if __name__ == "__main__":
    main()
