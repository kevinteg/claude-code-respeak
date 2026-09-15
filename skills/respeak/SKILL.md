---
name: respeak
description: >
  Translate agent/swarm output into a human-facing narrative. Fires on
  /respeak:respeak [mode] [source], and on natural-language asks like
  "explain that to my manager", "give me the ELI5", "make this readable",
  "what would I tell the reviewers", "translate this for the docs".
argument-hint: "[eli5|bluf|technical] [text or file path — defaults to this session's latest outcome]"
arguments: [mode, source]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh *) Bash(${CLAUDE_PLUGIN_ROOT}/scripts/respeak-py.sh *)
---

# respeak — render a narrative

Effective configuration for the working directory (plugin defaults,
`~/.claude/respeak/config.yaml`, the project's `.claude/respeak/config.yaml`
and its `scopes:`, any folder `.respeak.yaml`; nearest wins. The contract
is `docs/config-layers.md`):

!`"${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" explain --brief --launch-dir "${CLAUDE_PROJECT_DIR}"`

The last line above names any session override in force. Overrides silence
hooks; they never change this skill, which runs because the user asked.

Steps:

1. Determine the mode. `$mode` if given and one of `eli5|bluf|technical`;
   otherwise infer from the audience the user named (a child, a newcomer,
   "plain English" → eli5; a manager, exec, "bottom line", "leadership" →
   bluf; an engineer, reviewer, "for the PR/docs" → technical); otherwise
   the effective `narrative.default_mode` shown above, which already
   reflects the user, project, and folder layers for this directory.
2. Determine the source material. `$source` if given (text or a readable
   file path); otherwise this session's most recent substantive outcome —
   the latest completed task, findings, or state change, including any
   shorthand used along the way.
3. Resolve the configuration for the target. The target is the source file
   when `$source` is a file path (a folder's `.respeak.yaml` governs the
   files in it), otherwise the working directory. Run (quote the paths as
   shown; `--out` writes the file so no shell redirect is needed):
   `"${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" resolve --for "<target>" --launch-dir "${CLAUDE_PROJECT_DIR}" [--mode <mode>] --format yaml --out "/tmp/respeak-${CLAUDE_SESSION_ID}.yaml"`
   Add `--profile <name>` when the user named an audience that matches a
   profile the config defines under `profiles:` (for example "for the exec
   audience" → `exec`, or a household profile the user defined at user level);
   run `"${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" explain --for "<target>" --launch-dir "${CLAUDE_PROJECT_DIR}"`
   when you need the full layer-by-layer listing.
4. Delegate to the `respeak:respeak` agent with: the mode, the contents of
   that resolved config file verbatim under a heading
   `Resolved respeak configuration`, the source material, and the working
   directory. Do not translate inline yourself — the agent owns the corpus
   gates and lexicon bookkeeping, and an inline paraphrase bypasses both.
5. Verify before relaying — do not trust the agent's narrative on its own
   report. Feed the narrative to the scanner on stdin (a heredoc; no temp
   file, so no file-write permission is needed):
   ```
   "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-py.sh" respeak-measure.py - --fail-on error --config "/tmp/respeak-${CLAUDE_SESSION_ID}.yaml" <<'RESPEAK_EOF'
   <the narrative, verbatim>
   RESPEAK_EOF
   ```
   (the resolved config carries every layer's `gate.allow` and
   `style.budgets`, so a project's or folder's exceptions apply).
   - Exit 0: relay the narrative verbatim, its opening `📣 respeak · <mode>`
     marker line included — do not re-wrap, soften, or append commentary.
     If the agent omitted the marker, add it as the first line.
   - Exit 1: send the printed report back to the `respeak:respeak` agent and
     ask for a rewrite that clears every error-severity hit; run the check
     again. Allow at most 2 rounds total.
   - Still exit 1 after 2 rounds: relay the narrative anyway (marker line
     first), with the final measure report appended under a `respeak gate:
     still failing after 2 rounds` heading — the human sees exactly what did not clear, instead of
     a silently-shipped violation. Do not attempt a 3rd round yourself.
6. If the agent reports lexicon proposals, list the proposed terms in one
   line and note that ratification is pending per the shorthand config.
