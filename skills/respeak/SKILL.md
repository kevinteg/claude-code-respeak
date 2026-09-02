---
name: respeak
description: >
  Translate agent/swarm output into a human-facing narrative. Fires on
  /respeak:respeak [mode] [source], and on natural-language asks like
  "explain that to my manager", "give me the ELI5", "make this readable",
  "what would I tell the team", "translate this for the docs".
argument-hint: "[eli5|bluf|technical] [text or file path — defaults to this session's latest outcome]"
arguments: [mode, source]
---

# respeak — render a narrative

Current plugin configuration:

!`cat "${CLAUDE_PLUGIN_ROOT}/config/respeak.config.yaml" 2>/dev/null | head -40`

Steps:

1. Determine the mode. `$mode` if given and one of `eli5|bluf|technical`;
   otherwise infer from the audience the user named (a child, a newcomer,
   "plain English" → eli5; a manager, exec, "bottom line", "leadership" →
   bluf; an engineer, reviewer, "for the PR/docs" → technical); otherwise
   the configured `default_mode`.
2. Determine the source material. `$source` if given (text or a readable
   file path); otherwise this session's most recent substantive outcome —
   the latest completed task, findings, or state change, including any
   shorthand used along the way.
3. Delegate to the `respeak:respeak` agent with: the mode, the source
   material, and the working directory. Do not translate inline yourself —
   the agent owns the config, corpus gates, and lexicon bookkeeping, and an
   inline paraphrase bypasses all three.
4. Verify before relaying — do not trust the agent's narrative on its own
   report. Write it to a temp file, then run:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-measure.py" <tmpfile> --fail-on error`
   (add `--config .claude/respeak/config.yaml` when that file exists, so a
   project's own `gate.allow`/`style.budgets` apply).
   - Exit 0: relay the narrative verbatim — do not re-wrap, soften, or
     append commentary.
   - Exit 1: send the printed report back to the `respeak:respeak` agent and
     ask for a rewrite that clears every error-severity hit; run the check
     again. Allow at most 2 rounds total.
   - Still exit 1 after 2 rounds: relay the narrative anyway, with the final
     measure report appended under a `respeak gate: still failing after 2
     rounds` heading — the human sees exactly what did not clear, instead of
     a silently-shipped violation. Do not attempt a 3rd round yourself.
5. If the agent reports lexicon proposals, list the proposed terms in one
   line and note that ratification is pending per the shorthand config.
