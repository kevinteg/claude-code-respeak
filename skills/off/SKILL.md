---
name: off
description: >
  Silence the respeak hooks for this session only: the session-start lexicon
  note, the Stop-hook narrative nudge, and the PostToolUse style gate. With
  the argument `gate`, only the style gate goes quiet. Nothing in the project
  changes; a per-session marker in the cache carries the choice and
  /respeak:on removes it. User-invoked only.
disable-model-invocation: true
argument-hint: "[gate]"
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/respeak-session.sh *)
---

# respeak: off for this session

Run exactly this command and relay its output to the user as written:

```sh
"${CLAUDE_PLUGIN_ROOT}/scripts/respeak-session.sh" off $ARGUMENTS
```

If it exits 2 there is no session id; relay its message, which tells the
user to launch with `RESPEAK_HOOKS=off` or `RESPEAK_GATE=off` instead.

Do not edit any configuration file. A durable preference belongs in the
project's gitignored `.claude/respeak/config.local.yaml`
(docs/config-layers.md); this command is for the session you are in.
