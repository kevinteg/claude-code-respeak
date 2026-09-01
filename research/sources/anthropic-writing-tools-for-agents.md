# Anthropic Engineering: Writing effective tools for agents

- Source: https://www.anthropic.com/engineering/writing-tools-for-agents
- Fetched: 2026-08-31 (extraction notes; not verbatim)
- Relevance to respeak: tool contract design for the translator agent; token-budgeted response shaping; ResponseFormat enum as precedent for narrative-mode parameters.

## Core concept

Tools are contracts between deterministic systems and non-deterministic agents. Agent tools must tolerate varied agent behavior (hallucination, alternative strategies), unlike developer-facing APIs.

## Build process

- Prototype fast; give Claude LLM-friendly docs (`llms.txt`); test via local MCP.
- Evaluation tasks must be grounded in real workflows and require multiple tool calls.
  - Strong: "Schedule a meeting with Jane next week to discuss our latest Acme Corp project. Attach notes from our last planning meeting and reserve a conference room."
  - Weak: "Schedule a meeting with jane@acme.corp next week."
- Track: accuracy, runtime, tool-call count, token consumption, errors.
- Feed transcripts back into Claude Code and let agents propose tool improvements (held-out test set to avoid overfitting).

## Principles

1. **Fewer, higher-impact tools.** Don't wrap every endpoint. Consolidate: `schedule_event` instead of `list_users` + `list_events` + `create_event`; `search_logs` returning relevant lines + context instead of `read_logs`; `get_customer_context` instead of three getters.
2. **Namespacing.** Group under prefixes (`asana_search`, `asana_projects_search`). Prefix/suffix choice measurably affects eval performance.
3. **Return meaningful context.** High-signal only; semantic names (`name`, `image_url`) over low-level identifiers (`uuid`, `mime_type`, `256px_image_url`). Natural-language identifiers reduce hallucination vs alphanumeric UUIDs.
4. **ResponseFormat enum pattern.** Expose a verbosity control: `DETAILED` (206 tokens in the Slack example) vs `CONCISE` (72 tokens — ⅓ the size). Detailed keeps technical IDs for downstream calls.
   - *Respeak note: this is the direct precedent for exposing `mode: eli5 | bluf | technical` on the translator's tool surface.*
5. **Token efficiency.** Pagination, range selection, filtering, truncation with steering text ("Showing first 25 results. Use filters or pagination for specific data."). Claude Code caps tool responses at 25,000 tokens by default. Prompt-engineer error messages into actionable steering, not opaque codes.
6. **Descriptions are prompts.** Write tool descriptions like instructions to a new team member; make implicit context explicit; unambiguous parameter names (`user_id` not `user`). Small description refinements produced SOTA on SWE-bench Verified for Sonnet 3.5.

## Response structure

XML / JSON / Markdown each have tradeoffs; choose per your own evals; formats matching training-data distribution perform better.

## Closing framing

Effective tools show: intentional clarity, judicious context use, diverse composability, intuitive real-world applicability.
