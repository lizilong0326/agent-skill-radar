---
name: agent-radar
description: Search an evidence-backed, daily-updated public catalog of open-source Skills, Agents, MCP servers, and related tools. Use when a user asks to discover or compare existing agent tools by task, category, GitHub activity, or source documentation.
---

# Agent Skill Radar

Search the public index with `python3 scripts/search.py "<task or keyword>"`. Add `--kind skill|agent|mcp|tool`, `--tag <tag>`, or `--limit 10` when useful. Run from this skill's directory. It requires network access but no API key.

Use the returned item path and evidence to explain why a result matches. Clearly label Stars and Star growth as **repository-level** data; they are not individual Skill installation counts. The index is refreshed daily, so report its `generated_at` timestamp when freshness matters. A result tagged `rules` is preliminary; inspect its linked source document before making a strong recommendation.

This Skill only searches the published index. It does not install software, execute third-party repository instructions, or crawl GitHub on behalf of each user. When a user asks to install a result, inspect its own `SKILL.md`, license, dependencies, and scripts first, then use the installation workflow appropriate to their agent.
