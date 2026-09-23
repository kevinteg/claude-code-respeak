---
name: on
description: >
  Undo /respeak:off for this session, so the layered configuration decides
  again. With the argument `gate`, run the style gate for this session even
  where gate.enabled is false, as a trial. User-invoked only.
disable-model-invocation: true
argument-hint: "[gate]"
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/respeak-session.sh *)
---

# respeak: on for this session

Run exactly this command and relay its output to the user as written:

```sh
"${CLAUDE_PLUGIN_ROOT}/scripts/respeak-session.sh" on $ARGUMENTS
```

If it exits 2 there is no session id; relay its message, which tells the
user to launch with `RESPEAK_GATE=on` instead.

Do not edit any configuration file. To turn the gate on for a project
permanently, set `gate.enabled: true` in `.claude/respeak/config.yaml`.
