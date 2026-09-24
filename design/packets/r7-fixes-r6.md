# Packet R7: the R6 and ADV6 fixes, a hermetic check and bounded spawns

| item | value |
|---|---|
| from | `design/review-r6.md` (F1, F2, F4, F5, T1, T2, T6; R6-4, 6, 11, 12, 13, 19 to fold) and `design/review-adv6.md` (ADV6-1, 2, 3, 5, 6, 7, 11, 12); the relay's defect brief D2 items 1, 4, 5, 7; the owner's word 2026-09-23 10:20 (circuit breakers, invariants, fail early) |
| pin | claude-code-respeak `main` at `17030b4` or later. Branch `r7-fixes-r6`, worktree `.claude/worktrees/r7-fixes-r6` off it |
| wall | this repo; no push, `--amend`, rebase, device, tag, version bump, `make readme`; no real `claude` beyond `plugin validate` inside `make check`; no test opens a path under the real checkout except the scripts it tests |
| may touch | `Makefile`, `CLAUDE.md`, `CHANGELOG.md` (a bullet per act under `## Unreleased`), `plugin/docs/config-layers.md`, `scripts/readme-fresh.sh`, the config, gate, check and render scripts in `plugin/scripts/`, the check, gate_hook, readme_fresh, install, report_env and config_layers suites; new: `plugin/scripts/respeak-deadline.sh`, `scripts/readme-render.sh`, `design/readme/contract.txt`, `tests/test_render.sh`, the charter. Nothing else |
| acceptance | the lines of §6 with their baselines, targeted, under a minute |
| verify | `make check` |
| budget | 110 turns (one builder; the acts share three scripts), 144k context; one commit per act; the charter's open names doclint's five rows; checkpoint at 80% |

## 1. What the source says (quoted)

D2: "Fail early", "Bounded work", the load breaker "above 4x cores", "the kill is a group kill". ADV6: "the CI side, the part a relay treats as proof, can be turned green without fixing anything". config-layers: "`gate.fail_on` is deliberately open: a folder of drafts can say `gate: {fail_on: none}` and the hook still runs there but never blocks" (kept for the hook). Each ADV6 repro is its act's first test.

## 2. Rulings

Act 0, the fold, one commit. `CLAUDE.md`: three sentences (under about ten new lines the gate is the pass; README links are `/`-rooted; the source ceiling is 24,576 bytes, enforced by `readme-fresh.sh`). `config-layers.md` "Trust boundaries": one bullet (Apple's `/usr/bin/python3` stays a hook-time candidate for a Mac without pyenv; the checks never use it); its CI paragraph names `--committed`. The Makefile pin comment names the copy source (the checkout beside this one, found by `git rev-parse --git-common-dir`). The renderer's header says why the icon line sits under the title. Written once, hook-gated; no render.

Act 1, the hermetic check (ADV6-1, 2, T1). The resolver's `gate` gains `--committed`: every `gate.*` key comes from the plugin defaults and the project file with its scopes ONLY; the same keys from every other layer are dropped and named in `dropped`. The hook keeps the open folder rule. `respeak-gate.sh --file F --committed` passes it through, prints each drop, and refuses to guess: no python, a resolver failure, measure exit 2 or its deadline is exit 3, never 0. `respeak-check.sh` unsets `RESPEAK_CONFIG`, `CLAUDE_CODE_SESSION_ID` and `XDG_STATE_HOME` too, calls `--file --committed`, counts rc 3 as `ERROR    f`, exits 1 on any. Invariant before the summary: passed + skipped + blocked + errors + missing equals the files named, else exit 2. Tests: ADV6's first test; a `chmod 000` doc reads `1 errors`, rc 1; `test_config_layers.py` pins `dropped`.

Act 2, the stamp (ADV6-3, R6-13). `readme-fresh.sh`: after the hashes match it runs `respeak-verify-edit.py source README`, `stale` on a failure; a stamp without its source is `stale`, never `skipped`; a source over the ceiling is its own verdict; `--stamp` refuses unless the verifier passes. Tests: ADV6's second test, plus the ceiling.

Act 3, bounded spawns (ADV6-5, 6, 7, 12; F2, F4, T6). New `respeak-deadline.sh`: CMD runs in its own process group (`os.setpgrp()` then `os.execvp`, or bash job control), stdin and stdout pass through; on expiry the group gets TERM, KILL after 5 s, exit 124. The renderer refuses at exit 2 before any spawn when `RESPEAK_RENDER_DEPTH` is set (it exports it to the runner), when the 1-minute load (`sysctl -n vm.loadavg`, else `/proc/loadavg`) exceeds `RESPEAK_LOAD_MAX`, and when `--max-rounds` is not an integer 1 to 5; the runner gets `--tools Read Grep Glob --max-turns N` beside `--allowedTools` and runs under the deadline; `mktemp` failure is exit 2 here, in the gate and in the check. New `readme-render.sh`: renders to a temp file with `design/readme/contract.txt` (the Makefile's `README_CONTRACT`, moved verbatim), verifies, only then moves over `README.md` and stamps; `make readme` calls it. The gate blocks a file over `RESPEAK_GATE_MAX_BYTES` with `too large to gate` and runs measure under `RESPEAK_GATE_DEADLINE`. Makefile: `validate` under the helper at 60 s, each suite in `test` under 120 s. Tests in `tests/test_render.sh`, a fake runner on PATH: ADV6's third test; a fake `sysctl` at 999 and a bad `--max-rounds` exit 2 with the runner's log empty; the helper alone, `sleep 30` under 1 s, is 124 inside 7 s with no survivor; on a fixture, a runner echoing the source as `result` writes and stamps, one returning a banned phrase leaves `README.md` byte-identical; in `test_gate_hook.sh` a 3 MB file blocks.

Act 4, the interpreter and the install (T2, F1). Makefile: `PYTHON` is the virtualenv's `python3` under `PYENV_ROOT` when that file exists (no process), else today's line; `PATH` is exported with its bin dir first so every recipe and every hook a suite runs skips the shim; `CLAUDE ?= claude` for `install` and `validate`; `install` exits 2 naming a missing `CLAUDE`. `test_install.sh` passes `CLAUDE=$work/bin/claude`; new case: a missing `CLAUDE` exits 2, nothing ran.

Act 5, tests off the real tree (F5, ADV6-11). `test_check.sh` drops its dogfood block (`make doclint` is the dogfood); `test_report_env.sh` puts a fake `claude` first on PATH for every case.

Later: ADV6-4 (its own packet; it changes every repo's verify); ADV6-8 (the canonical doclint in claude-code-session); ADV6-10 (a cached `sys.executable` is an arbitrary path, against the trust boundary; act 4 removes the shim instead); R6-18 (the README packet). ADV6-9 with R6-22 is the coordinator's one fork for the owner; this row keeps today's rows shape.

## 3. Interfaces (signatures, not prose)

- `respeak-config.py gate --for F --committed [--write-config P]`: JSON gains `"committed": true, "dropped": ["<layer label>: gate.fail_on", ...]`.
- `respeak-gate.sh --file F [--committed] [--baseline-ref R]`: 0 pass, 2 block, 3 setup failure (committed only), stderr names the reason; each drop is one line `respeak gate: ignored <layer> <key> (committed)`. Env: `RESPEAK_GATE_MAX_BYTES` (2097152), `RESPEAK_GATE_DEADLINE` (15, under the hook's 20).
- `respeak-check.sh` summary gains `, E errors` after `blocked`.
- `respeak-deadline.sh SECONDS CMD [ARGS...]`: CMD's exit, or 124 with stderr `respeak-deadline: CMD killed after SECONDS s`.
- Renderer env: `RESPEAK_RENDER_DEPTH`, `RESPEAK_LOAD_MAX` (4 x `hw.ncpu`), `RESPEAK_RENDER_MAX_TURNS` (8), `RESPEAK_RENDER_WALL` (600); each refusal is one stderr line naming the cause.
- `readme-render.sh [--repo DIR] [--plugin-root DIR]`: 0 wrote and stamped; 1 the gate; 2 setup or verify; `README.md` untouched unless 0.
- Commits `r7 act N: <one line>`; the charter title `# Sitting <run day>-<n>: claude-code-respeak, r7-fixes-r6`.

## 4. Findings that name this row

On `main` `17030b4` under the virtualenv (3.12.7): `make check` 0 in 55 s; `make doclint` 20 s, 8 s with the virtualenv's bin first on PATH. `timeout` is brew's here, so the helper is bash. `claude --help` lists `--tools <tools...>` and `--max-turns`. `sysctl -n vm.loadavg` prints `{ 6.70 6.23 6.46 }`, `hw.ncpu` 16. `test_overrides.sh:71` and `test_gate_hook.sh:111` pin the open forms: committed is opt-in, both stay green. `verify-edit source README` passes today.

## 5. Forbidden reads

Every other repo. `~/.claude/`. `research/`; `examples/` beyond the tests' fixtures. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's charter. The relay's ledgers; any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line's last output on the branch beside `main` at this packet's commit:

| line | main | branch |
|---|---|---|
| `bash tests/test_check.sh 2>&1 \| tail -1` | `31 passed, 0 failed` | at least 35 passed, 0 failed |
| `bash tests/test_readme_fresh.sh 2>&1 \| tail -1` | `5 passed, 0 failed` | at least 8 passed, 0 failed |
| `bash tests/test_render.sh 2>&1 \| tail -1` | no such file | at least 8 passed, 0 failed |
| `grep -c dogfood tests/test_check.sh` | 2 | 0 |
| `grep -cE 'RENDER_DEPTH\|deadline\|LOAD_MAX' plugin/scripts/respeak-render.sh` | 0 | at least 3 |
| `grep -cE '^export PATH \|^CLAUDE \?= ' Makefile; make -n validate \| grep -c respeak-deadline` | 0 0 | 2 1 |
| `git status --short \| wc -l \| tr -d ' '` after the last commit | 0 | 0 |

Bullets: each act's commit; choices beyond §2 with reasons; what was left undone and for whom; at most ONE open fork. Last line: the branch and its head sha.
