# Anthropic Engineering: Effective harnesses for long-running agents

- Source: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents (published 2025-11-26)
- Fetched: 2026-08-31 (extraction notes; not verbatim)
- Reference implementation: https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding
- Relevance to respeak: the session-boundary problem is where a shorthand lexicon must live as a durable artifact; the initializer/coder split is the template for a lexicon-initializer + translator pair.

## Core problem

Long-running agents work across discrete sessions "with no memory of what came before" — like "engineers working in shifts, where each new engineer arrives with no memory of the previous shift."

## Two-part architecture

### Initializer agent (first session)

Creates the durable environment:
- `init.sh` (start dev server), `claude-progress.txt` (session log), initial git commit, and a comprehensive feature list.
- Feature list: 200+ features, **JSON not Markdown** — models are "less likely to inappropriately change or overwrite JSON files." Fields: category, description, steps, `passes` boolean; all start failing; "It is unacceptable to remove or edit tests."

### Coding agent (each later session)

Orientation sequence: `pwd` → read git log + progress file → pick one highest-priority failing feature → run `init.sh` → basic end-to-end verification → work → commit + update progress file.

## Failure modes and fixes

| Problem | Fix |
| --- | --- |
| Premature "done" declarations | structured feature list as ground truth |
| One-shotting the whole build | prompt for one feature per session |
| Undocumented progress + bugs at context exhaustion | git commits + progress file + startup test |
| Claimed-complete features that don't work | explicit end-to-end browser testing (Puppeteer MCP) |
| Environmental confusion | init.sh, progress files, git logs for rapid orientation |

## State mechanisms

- Progress file + git history + feature list = persistent state across sessions.
- Compaction alone is "not sufficient" — even Opus 4.5 needed the harness structure.
- Structured, modification-resistant formats (JSON) for load-bearing state; prose for logs.
  - *Respeak note: the shorthand lexicon should follow the feature-list pattern — a structured, append-mostly registry (JSON/YAML) with ratification status per entry, not free prose the swarm can drift.*

## Open questions (per the article)

- Single general agent vs specialized multi-agent (tester, QA, cleanup) — unresolved.
- Generalization beyond web dev (scientific research, financial modeling).
- Vision/browser-tooling limits on bug detection.
