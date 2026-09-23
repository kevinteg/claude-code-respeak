# Layered configuration, worked example

This tree is a small project plus a sample user-level file. The test suite
resolves against it (`tests/test_config_layers.py`), so the outcomes below
cannot drift from the code. The contract is in
[`docs/config-layers.md`](../../plugin/docs/config-layers.md).

```
home/.claude/respeak/config.yaml         user layer (point CLAUDE_CONFIG_DIR at home/.claude)
project/.claude/respeak/config.yaml      project layer, with two `scopes:`
project/.claude/respeak/config.local.yaml personal layer (gitignored in a real repo)
project/docs/exec/.respeak.yaml          folder layer: formal register
project/docs/api/.respeak.yaml           folder layer: profile author
project/notes/.respeak.yaml              folder layer with an ignored project-only key
```

Try it from the plugin checkout:

```sh
export CLAUDE_CONFIG_DIR=$PWD/examples/layered/home/.claude
P=examples/layered/project
bash scripts/respeak-config.sh explain --project $P --for $P/docs/exec/q3-summary.md
bash scripts/respeak-config.sh explain --brief --for $P/docs/api/endpoints.md   # no --project: discovered
bash scripts/respeak-config.sh resolve --project $P --for $P/docs/api/endpoints.md --format statusline
bash scripts/respeak-config.sh gate    --project $P --for $P/notes/scratch.md
bash scripts/respeak-config.sh validate $P/notes/.respeak.yaml            # exits 1: gate.enabled is project-only
bash scripts/respeak-config.sh validate --kind user examples/layered/home/.claude/respeak/config.yaml
CLAUDE_PROJECT_DIR=$P RESPEAK_GATE_TRACE=1 bash scripts/respeak-gate.sh --file $P/docs/overview.md   # the hook, as a command
RESPEAK_GATE=on CLAUDE_PROJECT_DIR=$P RESPEAK_GATE_TRACE=1 bash scripts/respeak-gate.sh --file $P/notes/scratch.md   # session override: forced on for this run
```

What each file gets, and which layer decided it:

| Target | mode | tech_level | profile | formality | gate applies (fail_on) | decided by |
| --- | --- | --- | --- | --- | --- | --- |
| `README.md` | technical | 3 | peer-engineer | 0.2 | yes (error) | project; formality from config.local |
| `docs/overview.md` | technical | 3 | peer-engineer | 0.2 | yes (error) | scope `docs/**` |
| `docs/exec/q3-summary.md` | bluf | 1 | exec | 0.8 | yes (warn) | scope `docs/exec/**`; formality from the folder file |
| `docs/api/endpoints.md` | technical | 5 | author | 0.2 | yes (error) | folder file beats scope `docs/**` |
| `reports/week-36.md` | bluf | 1 | exec | 0.2 | yes (warn) | scope `docs/exec/**, reports/**` |
| `notes/scratch.md` | technical | 5 | author | 0.2 | no (`notes/**` excluded) | folder file; its `gate.enabled` is ignored |

Outside any project (a directory with no `.claude/respeak/config.yaml`
above it and no `.git`, such as `--project` pointing at an empty
directory) the user file wins: BLUF, tech_level 2. A file outside this
project but resolved in a session that found it (`--project $P --for
/tmp/x.md`) still gets the project's layers, minus its folder files, and
the gate never applies to it. The `gate.enabled: false` in
`notes/.respeak.yaml` never takes effect: `explain` reports it under
`warnings:` and `validate` on that file exits 1 naming the key.
