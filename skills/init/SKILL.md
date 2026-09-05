---
name: init
description: >
  Set up respeak in the current project: create .claude/respeak/ state dirs,
  seed a sparse project config and the lexicon, generate the lexicon digest,
  show the effective configuration stack, and (with consent) wire the
  CLAUDE.md import, the gitignore entries, and the statusline. User-invoked
  only.
disable-model-invocation: true
argument-hint: "(no arguments)"
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh *) Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/render-lexicon-digest.sh *)
---

# respeak project setup

Perform these steps in the current project, reporting each as done/skipped:

1. Create `.claude/respeak/` and `.claude/respeak/proposals/` if missing.
2. Seed project state from the plugin if the files don't exist yet (never
   overwrite existing project files):
   - `.claude/respeak/config.yaml` ← `${CLAUDE_PLUGIN_ROOT}/config/project-seed.yaml`.
     The seed is deliberately sparse: `version`, a `gate:` block (`enabled:
     false`, `include: ["**/*.md"]`, `exclude: []`, `fail_on: error`,
     `allow: []`), and commented examples of `narrative:` and `scopes:`.
     Do not copy the full plugin config: a project file that restates every
     default pins every key and hides the user's own
     `~/.claude/respeak/config.yaml` (docs/config-layers.md, "Upgrading").
     The PostToolUse style gate (`scripts/respeak-gate.sh`) is seeded OFF; a
     human turns it on by editing `gate.enabled` to `true` once the project
     trusts its excludes/allow list. Only this file (or `config.local.yaml`)
     can turn it on.
   - `.claude/respeak/lexicon.yaml` ← `${CLAUDE_PLUGIN_ROOT}/corpus/lexicon.yaml`
3. Generate the lexicon digest: run
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/render-lexicon-digest.sh"` — it writes
   `.claude/respeak/lexicon-active.md` (ratified terms only, compact table).
4. Show the effective configuration stack: run
   `"${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" explain --launch-dir "${CLAUDE_PROJECT_DIR}"`
   and report which layers exist (a user-level `~/.claude/respeak/config.yaml`,
   an ancestor `.respeak.yaml` above the project, the file just seeded) and
   any warnings. If `project:` names a directory other than this one (a
   parent directory carries its own `.claude/respeak/config.yaml`, or a
   nested package does), say so: that file, not the seeded one, governs
   the files under it. If the user wants a folder-specific tone now, create
   `<folder>/.respeak.yaml` with only the keys that differ (for example
   `narrative: {profile: exec}`) and validate it with
   `"${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" validate "<folder>/.respeak.yaml"`.
5. Ask the user (do not do it silently) whether to add these two lines to the
   project's `.gitignore`, so personal overrides never get committed:
   `.claude/respeak/config.local.yaml` and `.respeak.local.yaml`.
6. Ask the user whether to add this line to the project's `CLAUDE.md` so
   every session loads the ratified lexicon:
   `@.claude/respeak/lexicon-active.md`
7. Ask the user whether to install the statusline segment; if yes, set in
   `.claude/settings.json`:
   `"statusLine": {"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/scripts/statusline.sh\""}`
   (If a statusLine already exists, show it and let the user decide.) The
   segment shows the effective mode and, when a nearer layer decided it,
   which file: `respeak bluf/t1 exec @docs/exec/.respeak.yaml · lexicon v0 · 0 proposals`.
8. Report: paths created, seeds copied, digest entry count, the layers
   `explain` found, which integrations the user accepted, whether the
   plugin root `${CLAUDE_PLUGIN_ROOT}` contains a space (if it does, say
   that `/respeak:respeak` will abort its permission check under default
   permissions until the plugin is reinstalled under a space-free path;
   the hooks still work), and the gate's current state (`gate: disabled (default) — enable in
   .claude/respeak/config.yaml` or, if the user asks to turn it on now, edit
   `gate.enabled: true` there and confirm `gate.include`/`gate.exclude`
   match the project's layout).
