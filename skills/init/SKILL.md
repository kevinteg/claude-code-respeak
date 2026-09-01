---
name: init
description: >
  Set up respeak in the current project: create .claude/respeak/ state dirs,
  seed the lexicon, generate the lexicon digest, and (with consent) wire the
  CLAUDE.md import and statusline. User-invoked only.
disable-model-invocation: true
argument-hint: "(no arguments)"
---

# respeak project setup

Perform these steps in the current project, reporting each as done/skipped:

1. Create `.claude/respeak/` and `.claude/respeak/proposals/` if missing.
2. Seed project state from the plugin defaults if the files don't exist yet
   (never overwrite existing project files):
   - `.claude/respeak/config.yaml` ← `${CLAUDE_PLUGIN_ROOT}/config/respeak.config.yaml`
   - `.claude/respeak/lexicon.yaml` ← `${CLAUDE_PLUGIN_ROOT}/corpus/lexicon.yaml`
3. Generate the lexicon digest: run
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/render-lexicon-digest.sh"` — it writes
   `.claude/respeak/lexicon-active.md` (ratified terms only, compact table).
4. Ask the user (do not do it silently) whether to add this line to the
   project's `CLAUDE.md` so every session loads the ratified lexicon:
   `@.claude/respeak/lexicon-active.md`
5. Ask the user whether to install the statusline segment; if yes, set in
   `.claude/settings.json`:
   `"statusLine": {"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/scripts/statusline.sh\""}`
   (If a statusLine already exists, show it and let the user decide.)
6. Report: paths created, seeds copied, digest entry count, and which
   integrations the user accepted.
