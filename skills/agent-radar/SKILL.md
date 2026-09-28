---
name: agent-radar
description: Search an evidence-backed, daily-updated public catalog of open-source Skills, Agents, MCP servers, and related tools. Use when a user asks to discover or compare existing agent tools by task, category, GitHub activity, or source documentation.
---

# Agent Skill Radar

Search the public index with `python3 scripts/search.py "<task or keyword>"`. Results show a short project-use sentence in Simplified Chinese by default; add `--lang en` for English. Add `--kind skill|agent|mcp|tool`, `--tag <capability>`, `--workflow <workflow>`, `--industry <industry>`, or `--limit 10` when useful. Run from this skill's directory. The bundled local catalog needs no network or API key; a remote catalog needs network access. Missing translations are explicitly marked as pending; do not present the original English text as a Chinese translation.

Use the returned item path and evidence to explain why a result matches. Industry matches have a basis of `explicit` (named in the documentation) or `inferred` (suggested by a documented workflow); never present an inferred industry as a verified deployment. Clearly label Stars and Star growth as **repository-level** data; they are not individual Skill installation counts. The index is refreshed daily, so report its `generated_at` timestamp when freshness matters. A result tagged `rules` is preliminary; inspect its linked source document before making a strong recommendation.

This Skill only searches the published index. It does not install software, execute third-party repository instructions, or crawl GitHub on behalf of each user. When a user asks to install a result, inspect its own `SKILL.md`, license, dependencies, and scripts first, then use the installation workflow appropriate to their agent.
