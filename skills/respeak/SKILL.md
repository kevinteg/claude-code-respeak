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
4. Relay the agent's narrative verbatim — do not re-wrap, soften, or append
   commentary.
5. If the agent reports lexicon proposals, list the proposed terms in one
   line and note that ratification is pending per the shorthand config.
