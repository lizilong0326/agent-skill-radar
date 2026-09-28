"""Daily GitHub discovery, document inspection, and evidence-backed indexing."""

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .classifier import classify
from .facets import FACETS_VERSION, INDUSTRY_LABELS_EN, INDUSTRY_LABELS_ZH, WORKFLOW_LABELS_EN, WORKFLOW_LABELS_ZH, classify_facets
from .taxonomy import GROUP_LABELS, GROUP_LABELS_EN, TAG_GROUPS, TAXONOMY, TAXONOMY_EN
from .translation import load_local_config, retained_translation, translate_catalog
from .use_cases import generate_use_cases, retained_use_case


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "catalog.json"
SITE_DATA_FILE = ROOT / "site" / "data" / "catalog.json"
SEARCH_QUERIES = [
    "topic:agent-skills stars:>=80 archived:false fork:false",
    "topic:mcp-server stars:>=100 archived:false fork:false",
    "topic:ai-agent stars:>=200 archived:false fork:false",
    '"SKILL.md" in:readme stars:>=80 archived:false fork:false',
]
SEED_REPOS = [
    "alextselegidis/easyappointments",
    "calcom/cal.diy",
    "frappe/erpnext",
    "vercel-labs/skills",
    "obra/superpowers",
    "github/github-mcp-server",
    "ChromeDevTools/chrome-devtools-mcp",
    "upstash/context7",
    "HKUDS/nanobot",
]
IGNORED_PARTS = {"node_modules", "vendor", ".git", "dist", "build", "examples", "fixtures", "tests", "benchmarks"}


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso_now():
    return utc_now().isoformat().replace("+00:00", "Z")


def parse_time(value):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class GitHubAPI:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self.gh = shutil.which("gh") if not self.token else None
        if not self.token and not self.gh:
            raise RuntimeError("Set GITHUB_TOKEN, or sign in with GitHub CLI (gh auth login).")
        self.calls = 0

    def get(self, endpoint):
        self.calls += 1
        if self.token:
            request = urllib.request.Request(
                "https://api.github.com" + endpoint,
                headers={
                    "Authorization": "Bearer " + self.token,
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "agent-skill-radar",
                },
            )
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request, timeout=30) as response:
                        return json.load(response)
                except urllib.error.HTTPError as exc:
                    if exc.code in (403, 429, 502, 503) and attempt < 2:
                        time.sleep(3 * (attempt + 1))
                        continue
                    raise
        result = subprocess.run(
            [self.gh, "api", endpoint, "-H", "Accept: application/vnd.github+json"],
            capture_output=True, text=True, timeout=40,
        )
        if result.returncode:
            raise RuntimeError("GitHub API request failed: " + result.stderr.strip()[:240])
        return json.loads(result.stdout)

    def repo(self, full_name):
        return self.get("/repos/" + full_name)

    def search(self, query, per_page=100, page=1):
        params = urllib.parse.urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": per_page, "page": page})
        return self.get("/search/repositories?" + params).get("items", [])

    def content(self, full_name, path):
        safe_path = urllib.parse.quote(path, safe="/")
        result = self.get("/repos/" + full_name + "/contents/" + safe_path)
        if not isinstance(result, dict) or result.get("encoding") != "base64":
            return ""
        raw = base64.b64decode(result.get("content", ""))
        return raw.decode("utf-8", errors="replace")[:90000]

    def readme(self, full_name):
        result = self.get("/repos/" + full_name + "/readme")
        if result.get("encoding") != "base64":
            return "", "README.md"
        content = base64.b64decode(result.get("content", "")).decode("utf-8", errors="replace")[:90000]
        return content, result.get("path") or "README.md"

    def tree(self, full_name, branch):
        safe_branch = urllib.parse.quote(branch, safe="")
        return self.get("/repos/" + full_name + "/git/trees/" + safe_branch + "?recursive=1")


def empty_catalog():
    return {"schema_version": 3, "generated_at": None, "taxonomy": {key: value["label"] for key, value in TAXONOMY.items()}, "taxonomy_en": TAXONOMY_EN, "tag_groups": TAG_GROUPS, "group_labels": GROUP_LABELS, "group_labels_en": GROUP_LABELS_EN, "workflow_labels": WORKFLOW_LABELS_ZH, "workflow_labels_en": WORKFLOW_LABELS_EN, "industry_labels": INDUSTRY_LABELS_ZH, "industry_labels_en": INDUSTRY_LABELS_EN, "repositories": [], "items": []}


def load_catalog():
    if not DATA_FILE.exists():
        return empty_catalog()
    with DATA_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def repo_record(raw, old=None):
    old = old or {}
    license_info = raw.get("license") or {}
    today = utc_now().date().isoformat()
    history = [entry for entry in old.get("star_history", []) if entry.get("date") != today]
    history.append({"date": today, "stars": raw.get("stargazers_count", 0)})
    history = history[-120:]
    description = raw.get("description") or ""
    result = {
        "id": raw["id"],
        "full_name": raw["full_name"],
        "url": raw["html_url"],
        "description": description,
        **retained_translation(old, description),
        "stars": raw.get("stargazers_count", 0),
        "forks": raw.get("forks_count", 0),
        "license": license_info.get("spdx_id") or "",
        "topics": raw.get("topics") or [],
        "default_branch": raw.get("default_branch") or "main",
        "usage_note_zh": old.get("usage_note_zh", ""),
        "usage_note_en": old.get("usage_note_en", ""),
        "usage_note_excerpt": old.get("usage_note_excerpt", ""),
        "pushed_at": raw.get("pushed_at"),
        "archived": bool(raw.get("archived")),
        "first_seen": old.get("first_seen") or today,
        "last_seen": today,
        "star_history": history,
        "documents_pending": old.get("documents_pending", 0),
        "skill_documents_total": old.get("skill_documents_total", 0),
        "skill_documents_indexed": old.get("skill_documents_indexed", 0),
    }
    for days in (7, 30, 60):
        cutoff = utc_now().date() - dt.timedelta(days=days)
        earlier = [entry for entry in history if dt.date.fromisoformat(entry["date"]) <= cutoff]
        result["stars_" + str(days) + "d"] = result["stars"] - earlier[-1]["stars"] if earlier else None
    return result


def inactivity(repo):
    if repo.get("archived"):
        return "archived", "GitHub 仓库已归档"
    pushed = parse_time(repo.get("pushed_at"))
    inactive_days = (utc_now() - pushed).days if pushed else 0
    growth = repo.get("stars_60d")
    if inactive_days >= 60:
        return "archived", "超过 60 天没有代码更新"
    if growth is not None and growth <= 0:
        return "archived", "观察的 60 天内 Star 未增长"
    if inactive_days >= 30:
        return "watch", "超过 30 天没有代码更新"
    return "active", ""


def extract_description(content, fallback=""):
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---", content, re.S)
    if frontmatter:
        lines = frontmatter.group(1).splitlines()
        for index, line in enumerate(lines):
            match = re.match(r"^description:\s*(.*)$", line)
            if not match:
                continue
            value = match.group(1).strip()
            if re.fullmatch(r"[|>][-+]?", value):
                parts = []
                for part in lines[index + 1:]:
                    if part and not part[0].isspace():
                        break
                    if part.strip():
                        parts.append(part.strip())
                value = " ".join(parts)
            if value:
                return value.strip("'\"")[:240]
    paragraphs = re.split(r"\n\s*\n", content)
    for paragraph in paragraphs:
        if paragraph.lstrip().startswith("> [!"):
            continue
        if paragraph.count("href=") >= 2 or paragraph.count("•") >= 2:
            continue
        if "<img" in paragraph or "![(" in paragraph or "shields.io" in paragraph:
            continue
        if len(re.findall(r"README[^\s)]*\.md", paragraph, re.IGNORECASE)) >= 2 and re.search(r"English|中文|简体|Español|Deutsch|日本語|한국어", paragraph, re.IGNORECASE):
            continue
        if "<" in paragraph and ">" in paragraph:
            cleaned = html.unescape(re.sub(r"<[^>]*>", " ", paragraph))
        else:
            cleaned = paragraph
        cleaned = re.sub(r"[`*#>\[\]]", "", cleaned).strip()
        if 35 <= len(cleaned) <= 500 and not cleaned.startswith(("---", "<", "!")):
            return re.sub(r"\s+", " ", cleaned)[:240]
    return fallback[:240]


def discover(api, existing_names, max_new, min_stars):
    if max_new <= 0:
        return []
    names = []
    for name in SEED_REPOS:
        if name not in existing_names:
            names.append(name)
    for page in range(1, 11):
        groups = []
        for query in SEARCH_QUERIES:
            try:
                matches = api.search(query, page=page)
            except Exception as exc:
                print("Search failed:", query, type(exc).__name__, file=sys.stderr)
                continue
            groups.append([match for match in matches if match.get("stargazers_count", 0) >= min_stars and not match.get("fork") and not match.get("archived")])
        found_any = any(groups)
        while len(names) < max_new and any(groups):
            for group in groups:
                if not group or len(names) >= max_new:
                    continue
                match = group.pop(0)
                name = match.get("full_name")
                if name and name not in existing_names and name not in names:
                    names.append(name)
        if len(names) >= max_new or not found_any:
            break
    return names[:max_new]


def item_paths(tree, max_items=None):
    paths = []
    for entry in tree.get("tree", []):
        path = entry.get("path", "")
        if entry.get("type") != "blob" or Path(path).name.lower() != "skill.md":
            continue
        if any(part in IGNORED_PARTS for part in path.split("/")):
            continue
        paths.append(path)
    paths.sort(key=lambda value: (0 if value.startswith("skills/") else 1, value.count("/"), value))
    selected = []
    seen_names = set()
    for path in paths:
        name = Path(path).parent.name if path != "SKILL.md" else path
        if name in seen_names:
            continue
        selected.append(path)
        seen_names.add(name)
        if max_items is not None and len(selected) >= max_items:
            break
    return selected


def repo_kind(readme, repo):
    text = readme[:1800].lower()
    description = (repo.get("description") or "").lower()
    heading = next((line.strip("#* ").lower() for line in readme.splitlines()[:120] if re.match(r"^#\s+", line)), "")
    topics = set(repo.get("topics", []))
    if "curated list" in text or "awesome list" in text or "directory of" in text:
        return None
    mcp_primary = bool(re.search(r"\bmcp\W{0,8}servers?\b", heading + " " + description))
    mcp_intro = bool(re.search(r"\b(mcp|model[- ]context[- ]protocol)\W{0,8}servers?\b", text[:900]))
    if mcp_primary or ("mcp-server" in topics and mcp_intro):
        return "mcp"
    if re.search(r"^(?:[^a-z]*|an? |the |ultra-lightweight[\s,]*|open-source[\s,]*|self-hosted[\s,]*|personal[\s,]*|ai[\s,]*|coding[\s,]*)*agent\b", description):
        return "agent"
    if re.search(r"\bis an? (?:open-source |ultra-lightweight |self-hosted |personal )*(?:ai |coding )?agent(?: framework)?\b", text[:900]):
        return "agent"
    if mcp_intro and "mcp" in topics:
        return "mcp"
    return "tool"


def build_items(api, repo, old_items, args, ai_budget):
    full_name = repo["full_name"]
    old_by_id = {item["id"]: item for item in old_items}
    readme, readme_path = "", "README.md"
    try:
        readme, readme_path = api.readme(full_name)
    except Exception:
        pass
    if readme:
        caution = next((line.strip(" >") for line in readme.splitlines() if re.search(r"personal, non-production use", line, re.IGNORECASE)), "")
        repo["usage_note_zh"] = "官方 README 建议仅用于个人、非生产环境。" if caution else ""
        repo["usage_note_en"] = "The README recommends personal, non-production use only." if caution else ""
        repo["usage_note_excerpt"] = caution[:300]
    try:
        tree = api.tree(full_name, repo["default_branch"])
    except Exception as exc:
        print("Tree unavailable:", full_name, type(exc).__name__, file=sys.stderr)
        return old_items, ai_budget
    all_paths = item_paths(tree)
    valid_paths = set(all_paths)
    records = {item["id"]: item for item in old_items if item.get("kind") == "skill" and item.get("source_path") in valid_paths}
    unseen = [path for path in all_paths if str(repo["id"]) + ":" + path not in records]
    known = [path for path in all_paths if path not in unseen]
    has_key = bool(os.getenv("DEEPSEEK_API_KEY"))
    known.sort(key=lambda path: (
        records[str(repo["id"]) + ":" + path].get("last_checked_push") == repo.get("pushed_at"),
        has_key and records[str(repo["id"]) + ":" + path].get("method") == "deepseek",
        records[str(repo["id"]) + ":" + path].get("last_checked_at") or "",
    ))
    paths = (unseen + known)[:max(1, args.max_items_per_repo)]
    for path in paths:
        try:
            content = api.content(full_name, path)
        except Exception as exc:
            print("Document unavailable:", full_name, path, type(exc).__name__, file=sys.stderr)
            continue
        if not content:
            continue
        item_id = str(repo["id"]) + ":" + path
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        old = old_by_id.get(item_id, {})
        has_key = bool(os.getenv("DEEPSEEK_API_KEY"))
        should_reclassify = old.get("content_hash") != digest or old.get("facets_version") != FACETS_VERSION or (old.get("method") != "deepseek" and (args.reclassify_all or (has_key and ai_budget > 0)))
        if should_reclassify:
            if old.get("content_hash") == digest and old.get("method") == "deepseek" and not args.reclassify_all:
                category = {key: old.get(key) for key in ("tags", "evidence", "method", "confidence", "summary_zh", "model") if key in old}
                category.update(classify_facets({path: content}))
            else:
                use_ai = has_key and ai_budget > 0
                category = classify({path: content}, "skill", use_ai)
                ai_budget -= int(use_ai)
        else:
            category = {key: old.get(key) for key in ("tags", "evidence", "method", "confidence", "summary_zh", "model", "workflows", "workflow_evidence", "industry_matches", "facets_source", "facets_version") if key in old}
        description = extract_description(content, repo["description"])
        records[item_id] = {
            "id": item_id,
            "repo_id": repo["id"],
            "kind": "skill",
            "name": Path(path).parent.name if path != "SKILL.md" else full_name.split("/")[-1],
            "description": description,
            **retained_translation(old, description),
            **retained_use_case(old, description),
            "source_path": path,
            "source_url": repo["url"] + "/blob/" + repo["default_branch"] + "/" + urllib.parse.quote(path),
            "content_hash": digest,
            "classified_at": iso_now() if should_reclassify else old.get("classified_at"),
            "last_checked_at": iso_now(),
            "last_checked_push": repo.get("pushed_at"),
            **category,
        }
    repo["skill_documents_total"] = len(all_paths)
    repo["skill_documents_indexed"] = sum(str(repo["id"]) + ":" + path in records for path in all_paths)
    repo["documents_pending"] = sum(
        str(repo["id"]) + ":" + path not in records or records[str(repo["id"]) + ":" + path].get("last_checked_push") != repo.get("pushed_at")
        for path in all_paths
    )
    kind = repo_kind(readme, repo) if readme else None
    if readme and kind is not None:
        path = readme_path
        item_id = str(repo["id"]) + ":" + path
        digest = hashlib.sha256(readme.encode("utf-8")).hexdigest()
        old = old_by_id.get(item_id, {})
        has_key = bool(os.getenv("DEEPSEEK_API_KEY"))
        should_reclassify = old.get("content_hash") != digest or old.get("facets_version") != FACETS_VERSION or (old.get("method") != "deepseek" and (args.reclassify_all or (has_key and ai_budget > 0)))
        if should_reclassify:
            if old.get("content_hash") == digest and old.get("method") == "deepseek" and not args.reclassify_all:
                category = {key: old.get(key) for key in ("tags", "evidence", "method", "confidence", "summary_zh", "model") if key in old}
                category.update(classify_facets({path: readme}))
            else:
                use_ai = has_key and ai_budget > 0
                category = classify({path: readme}, kind, use_ai)
                ai_budget -= int(use_ai)
        else:
            category = {key: old.get(key) for key in ("tags", "evidence", "method", "confidence", "summary_zh", "model", "workflows", "workflow_evidence", "industry_matches", "facets_source", "facets_version") if key in old}
        description = extract_description(readme, repo["description"])
        records[item_id] = {
            "id": item_id,
            "repo_id": repo["id"],
            "kind": kind,
            "name": full_name.split("/")[-1],
            "description": description,
            **retained_translation(old, description),
            **retained_use_case(old, description),
            "source_path": path,
            "source_url": repo["url"] + "/blob/" + repo["default_branch"] + "/" + urllib.parse.quote(path),
            "content_hash": digest,
            "classified_at": iso_now() if should_reclassify else old.get("classified_at"),
            "last_checked_at": iso_now(),
            "last_checked_push": repo.get("pushed_at"),
            **category,
        }
    elif not readme:
        for item in old_items:
            if item.get("kind") != "skill":
                records[item["id"]] = item
    return list(records.values()), ai_budget


def refresh(args):
    catalog = load_catalog()
    api = GitHubAPI()
    existing = {repo["full_name"]: repo for repo in catalog["repositories"]}
    old_items = {}
    for item in catalog["items"]:
        old_items.setdefault(item["repo_id"], []).append(item)
    new_names = discover(api, set(existing), args.max_new, args.min_stars)
    new_names = new_names[:args.max_repos]
    queued_existing = sorted(existing, key=lambda name: existing[name].get("last_seen", ""))[:max(0, args.max_repos - len(new_names))]
    names = queued_existing + new_names
    print("Repositories queued:", len(names), "new:", len(new_names))
    repos = []
    items = []
    has_key = bool(os.getenv("DEEPSEEK_API_KEY"))
    classification_limit = args.max_ai_calls * 2 // 3 if has_key else args.max_ai_calls
    ai_budget = classification_limit
    for index, name in enumerate(names, 1):
        old_repo = existing.get(name, {})
        try:
            raw = api.repo(name)
            repo = repo_record(raw, old_repo)
        except Exception as exc:
            print("Repository unavailable:", name, type(exc).__name__, file=sys.stderr)
            if old_repo:
                repos.append(old_repo)
                items.extend(old_items.get(old_repo["id"], []))
            continue
        if repo["license"] in {"", "NOASSERTION"} and not old_repo:
            print("Skipping without verified license:", name)
            continue
        if repo["stars"] < args.min_stars and not old_repo:
            continue
        status, reason = inactivity(repo)
        repo["status"], repo["status_reason"] = status, reason
        has_rule_backlog = bool(os.getenv("DEEPSEEK_API_KEY")) and ai_budget > 0 and any(item.get("method") != "deepseek" for item in old_items.get(repo["id"], []))
        needs_docs = args.reclassify_all or not old_repo or not old_items.get(repo["id"]) or old_repo.get("pushed_at") != repo.get("pushed_at") or old_repo.get("documents_pending", 0) > 0 or has_rule_backlog or any(item.get("facets_source") != "full_document" or item.get("facets_version") != FACETS_VERSION for item in old_items.get(repo["id"], []))
        if needs_docs:
            fresh, ai_budget = build_items(api, repo, old_items.get(repo["id"], []), args, ai_budget)
        else:
            fresh = old_items.get(repo["id"], [])
        if not fresh:
            print("Skipping without eligible tool documents:", name)
            continue
        repos.append(repo)
        for item in fresh:
            item["status"] = status
            item["status_reason"] = reason
        items.extend(fresh)
        print("[{}/{}] {}: {} items, {} stars, {}".format(index, len(names), name, len(fresh), repo["stars"], status), flush=True)
    for name, old_repo in existing.items():
        if name not in names:
            repos.append(old_repo)
            items.extend(old_items.get(old_repo["id"], []))
    catalog.update({
        "schema_version": 3,
        "generated_at": iso_now(),
        "taxonomy": {key: value["label"] for key, value in TAXONOMY.items()},
        "taxonomy_en": TAXONOMY_EN,
        "tag_groups": TAG_GROUPS,
        "group_labels": GROUP_LABELS,
        "group_labels_en": GROUP_LABELS_EN,
        "workflow_labels": WORKFLOW_LABELS_ZH,
        "workflow_labels_en": WORKFLOW_LABELS_EN,
        "industry_labels": INDUSTRY_LABELS_ZH,
        "industry_labels_en": INDUSTRY_LABELS_EN,
        "repositories": sorted(repos, key=lambda value: value["stars"], reverse=True),
        "items": sorted(items, key=lambda value: (value["repo_id"], value["source_path"])),
    })
    remaining_calls = args.max_ai_calls - classification_limit + ai_budget
    translation_calls, translation_pending, _ = translate_catalog(catalog, remaining_calls)
    summary_calls, summary_pending = generate_use_cases(catalog, remaining_calls - translation_calls)
    write_json(DATA_FILE, catalog)
    write_json(SITE_DATA_FILE, catalog)
    print("Saved:", len(repos), "repositories,", len(items), "items;", api.calls, "GitHub API calls;", translation_calls, "translation calls;", translation_pending, "translations pending;", summary_calls, "use-case calls;", summary_pending, "summaries pending")


def main():
    parser = argparse.ArgumentParser(description="Refresh the public Agent Skill Radar index")
    parser.add_argument("--max-new", type=int, default=15, help="maximum newly discovered repositories per run")
    parser.add_argument("--max-repos", type=int, default=500, help="maximum total repositories in one run")
    parser.add_argument("--max-items-per-repo", type=int, default=20)
    parser.add_argument("--min-stars", type=int, default=80)
    parser.add_argument("--max-ai-calls", type=int, default=100)
    parser.add_argument("--reclassify-all", action="store_true")
    parser.add_argument("--translate-only", action="store_true", help="backfill Chinese descriptions without fetching GitHub")
    args = parser.parse_args()
    load_local_config()
    if args.translate_only:
        catalog = load_catalog()
        catalog.update({"schema_version": 3, "taxonomy_en": TAXONOMY_EN, "group_labels_en": GROUP_LABELS_EN, "workflow_labels": WORKFLOW_LABELS_ZH, "workflow_labels_en": WORKFLOW_LABELS_EN, "industry_labels": INDUSTRY_LABELS_ZH, "industry_labels_en": INDUSTRY_LABELS_EN})
        calls, pending, changed = translate_catalog(catalog, args.max_ai_calls)
        summary_calls, summary_pending = generate_use_cases(catalog, args.max_ai_calls - calls)
        if changed or summary_calls:
            write_json(DATA_FILE, catalog)
            write_json(SITE_DATA_FILE, catalog)
        print("Translation calls:", calls, "pending:", pending, "use-case calls:", summary_calls, "summaries pending:", summary_pending)
    else:
        refresh(args)


if __name__ == "__main__":
    main()
