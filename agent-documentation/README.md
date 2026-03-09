# Agent Documentation Strategy

This folder contains documentation structured specifically for AI agent consumption. It is optimized for tools like Claude Code, Cursor, GitHub Copilot, Windsurf, and other AI coding assistants.

## Strategy Overview

This documentation follows best practices from the llms.txt standard, AGENTS.md convention (Linux Foundation / Agentic AI Foundation), and context engineering principles for AI-readable repositories.

### Design Principles

1. **Progressive disclosure** — Start with a lightweight index (`llms.txt`) that points to focused topic files. Agents load only what they need for the current task.
2. **One concept per file** — Each file covers a single domain (API, SDK, analytics, management). No file exceeds 300 lines to respect context window budgets.
3. **Structured Markdown** — All files use consistent heading hierarchy, tables, and code blocks. Markdown is the optimal format for AI agents: it balances human readability with machine parseability and is natively understood by all major LLMs.
4. **Pointers over copies** — References use `file_path:line_number` format to point to source code. Content that changes frequently is referenced, not duplicated.
5. **Front-loaded important information** — Each file leads with the most critical context (purpose, endpoints, gotchas) before diving into details. LLMs weight earlier content more heavily.
6. **Cross-tool compatibility** — The structure works with Claude Code (CLAUDE.md), Cursor (.cursor/rules), GitHub Copilot (.github/copilot-instructions.md), and the universal AGENTS.md standard.

### File Format Rationale

- **Markdown (.md)**: Primary format for all documentation. Token-efficient, universally parsed by AI tools, supports structured tables and code blocks.
- **Plain text for indexes**: `llms.txt` follows the llms.txt standard — a lightweight entry point with curated links.
- **No JSON/YAML for prose**: Structured data formats are reserved for schemas and configs, not documentation narratives.

### Context Window Optimization

| Model | Context Window | Practical Limit |
|-------|---------------|-----------------|
| Claude Opus/Sonnet | 200K tokens | ~150K usable after system prompt |
| GPT-4o | 128K tokens | ~100K usable |
| Gemini 2.0 | 1M tokens | ~800K usable |

Each file in this folder is designed to be independently useful within 2-5K tokens (roughly 1-2 pages). An agent working on a specific task should rarely need to load more than 2-3 files from this folder.

## Folder Structure

```
agent-documentation/
  README.md                          # This file — strategy overview
  llms.txt                           # Entry point index (llms.txt standard)
  AGENTS.md                          # Universal agent instructions (cross-tool)
  01-project-overview.md             # Repository structure and purpose
  02-api-reference.md                # Particle Health Query Flow API
  03-management-api-reference.md     # Particle Health Management API
  04-sdk-reference.md                # Python SDK architecture and usage
  05-analytics-pipeline.md           # DuckDB/BigQuery data pipeline
  06-management-ui.md                # Admin UI architecture (React + FastAPI)
  07-data-models.md                  # Patient, query, document data schemas
  08-authentication.md               # Auth flows for all APIs
  09-troubleshooting.md              # Common errors and solutions
  10-environment-setup.md            # Setup, configuration, and credentials
  11-flat-data-contract.md           # ODCS v3 flat data contract (22 table schemas)
  12-notification-data-contract.md   # Webhook notification schemas (7 notification types)
```

## How Agents Should Use This Folder

1. **Start with `llms.txt`** — It provides a one-line description of each file and what it covers. Use this to decide which files to read.
2. **Read `AGENTS.md`** — Contains universal conventions, build/test commands, and code style rules.
3. **Load topic files on demand** — Only read the specific file(s) relevant to the current task.
4. **Follow source references** — When a doc references `src/particle/core/auth.py:85`, read the source directly for implementation details.

## Standards Implemented

| Standard | File | Supported By |
|----------|------|-------------|
| llms.txt | `llms.txt` | 844K+ websites, emerging LLM standard |
| AGENTS.md | `AGENTS.md` | 60K+ repos, Copilot, Cursor, Codex, Gemini CLI, Devin, Jules |
| Structured Markdown | All `.md` files | All LLM-based coding tools |

## Anti-Patterns Avoided

- **No monolithic docs** — No single file tries to document everything
- **No deeply nested folders** — Flat structure with numeric prefixes for ordering
- **No generated API specs** — Human-curated descriptions optimized for agent comprehension
- **No outdated code snippets** — References to source files instead of inline code that goes stale
- **No ambiguous instructions** — Every file has a clear scope stated in its first line
