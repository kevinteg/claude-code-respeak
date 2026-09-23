# Review R6: the design decisions of 2026-09-22 and 23 in claude-code-respeak

Relay row `review-6-respeak`, 2026-09-23, `main` `2a21d76`. Read: the two days' charters,
packets R1 to R6, the design of record (`CLAUDE.md`, `plugin/docs/config-layers.md`,
`docs/architecture.md`, `design/readme/source.md`, the Makefile), the brief D1 to D7.

## 1. Decisions ledger

Record = in the design of record. Charter = only in a charter or packet (a gap; the home
section follows).

- R6-1 Marketplace `claude-code-respeak`, install `respeak@claude-code-respeak` (R1). Record.
- R6-2 `make check` = test, lint, doclint, hygiene, readme-fresh, validate (R1). Record.
- R6-3 Checks run under the pyenv virtualenv `.python-version` names; suites get its bin dir first on PATH (R1, R2). Record.
- R6-4 The hook-time interpreter finder keeps Apple's python as a candidate for other machines (R1, asked twice, never ruled). Charter; home: config-layers "Trust boundaries". See 6.1.
- R6-5 `scripts/hygiene` and `scripts/doclint` are byte copies of the session's, pinned by two sha256 in the Makefile, files and pins moving in one commit (R1, R3, R5, R6). Record.
- R6-6 The copy source is the checkout beside this one, found by `git rev-parse --git-common-dir`, never a home path (R6). Charter; home: the Makefile's pin comment.
- R6-7 The provider layer: the session plugin's resolved file, major 2, tone keys only, above the folder files (R1). Record.
- R6-8 The session id is `CLAUDE_CODE_SESSION_ID` only, measured (R3). Record.
- R6-9 `README.md` is written by `make readme` only, from `design/readme/source.md`, proven prose-only, stamped; `make check` refuses a stale README (R2). Record.
- R6-10 Freshness is a content stamp, not mtime; the stamp keeps two lines (R2, R4; owner 05:53 item 4). Record.
- R6-11 The render carries a keep-the-structure contract; the icon line sits under the title because the renderer strips preamble (R2). Charter; home: `respeak-render.sh`'s header, or fix the renderer.
- R6-12 README links are `/`-rooted so one target resolves from the source and the root (R2). Charter; home: CLAUDE.md "The README is rendered".
- R6-13 Source ceiling 24,576 bytes (R2). Packet only; no check enforces it. Home: doclint or CLAUDE.md.
- R6-14 0.6.1 bumped inside a row; the tag is the owner's, cut at `bcaf292`; later changes go under `## Unreleased` (R2, R5). Record.
- R6-15 The `plugin/` subtree is the marketplace source; self-contained means no shipped file opens a path outside it; `config-layers.md` ships inside (R4). Record.
- R6-16 No `hooks/run` shim; the hooks name their scripts by the plugin root (R4; owner 05:53 item 4). Record via conventions.
- R6-17 `make doctor`, six lines, python suggests newer releases (R4). Record.
- R6-18 `make install` installs from this checkout and never removes a registration (R4). Makefile only; the README Layout names check, readme, doctor and not install. Home: the source's Layout.
- R6-19 A short CHANGELOG bullet is written once and gated, no editorial pass (R5, R6). Charter; contradicts CLAUDE.md. See 2.
- R6-20 Skill descriptions at most 200 chars; `respeak` keeps three of five asks, the agent keeps all (R6). Record.
- R6-21 Charters may name a person; the sittings allow row narrowed as hygiene stopped scanning `person` and `sibling` there (17e488d, R5, R6). Record.
- R6-22 The relay row's `prompt` went repo-relative (R1, R2) then absolute (R3 on), the home path admitted by `.hygiene-allow` (R3). Charter. See 2 and 6.2.
- R6-23 A relay child renders the README itself: nested `claude -p` works (R2). Record.

## 2. Reversals and tensions

- R1 kept the plugin at the repo root; R4 built `plugin/`. An evolution, both recorded; no action.
- R1 called 0.6.1 the owner's release act; R2 bumped it on the prompt's word. Recorded; the tag stayed the owner's. No action.
- R6-19 against CLAUDE.md, which says new content is passed the same way. CLAUDE.md should yield: under about ten lines the gate is the pass. One sentence there.
- R6-22: this public repo tracks the owner's home path in `design/packets/rows-*.json`. The relay's row shape should accept a repo-relative prompt resolved against `repo`; the rows here go relative.
- Conventions §5 words freshness as "older than"; R6-10 is a content stamp because git keeps no mtimes. Settled per repo by the owner; the wording should still yield, for every repo.
- R5 and R6 carry `make check` and `make test` as acceptance lines; the run-5 rule refuses whole-suite lines. The next packet here names targeted lines (one bash suite, one unittest module); the verify line stays `make check`.
- The python ruling binds the tooling; `respeak-python.sh` still probes `/usr/bin/python3`. Not a contradiction once R6-4 is ruled and recorded.

## 3. Fork-storm class

Cycle, bound today, fix. Nothing here runs the relay, so no cycle closes through `relay plan`; the danger is nested spawns without a clock and real binaries under a measurement.

- F1 `make check` > `make test` > `tests/test_install.sh` > `make -C <real root> install` > `claude plugin marketplace add`, `plugin install`. Not a cycle, but a nested make on the real tree that would register the checkout on this Mac if the fake `claude` ever left PATH. Bound: the fake, prefixed on PATH; NONE in the recipe. Fix: `CLAUDE ?= claude` in the Makefile, the test passes its fake by variable; the recipe refuses under `RELAY_MEASURE_DEPTH`.
- F2 `make readme` > `respeak-render.sh` > `claude -p` (plugins load: SessionStart, Stop, the gate) > could it run make? No. Bound: `--allowedTools Read Grep Glob`, `--max-rounds 2`; `readme` is outside `check`, so a measurement never renders. NONE for time: no `--max-turns`, no `timeout`; no test covers the target. Fix: both, plus `RESPEAK_RENDER_DEPTH` so a render inside a render refuses, and a fake-runner test of `make readme`.
- F3 Hooks. The gate never writes or spawns `claude`; the Stop nudge is bounded by `stop_hook_active` (tested); lexicon-status is read-only. Bound: present. No fix.
- F4 `make check` > `validate` > two real `claude plugin validate` at every measurement. Bound NONE for time. Fix: `timeout 60`, and a skipped validate never reads green under a measurement.
- F5 `tests/test_check.sh` dogfoods the real checkout's tracked docs (the D7 class), and `make doclint` already runs the same scan: every measurement measures 36 files twice. Bound: tracked files, `--quiet`. Fix: drop the block from the suite; the doclint target is the dogfood.
- F6 Git hooks: none; project hooks: none.

## 4. Timing and edge conditions

- T1 The gate fails open on any setup error and on its 20 s hook timeout (documented in its header). Under a load of 200 a relay child's Markdown writes pass unmeasured. Invariant: a failing doc never lands unnoticed; held only by the verify line's respeak-check, which a same-as-main pass skips. Tested: the no-python path, not the timeout. Fix: the hook prints `gate: skipped` on the timeout path, and the verify line never reads same-as-main when the gate was skipped.
- T2 `PYTHON ?= $(shell python3 ...)` resolves through the pyenv shim at every top-level make; D5 measured 60 s waits on its lock under load. Invariant: no check-time process goes through the shim. Untested. Fix: resolve the interpreter once from `.python-version` and put its bin dir first for every recipe, not only `test`.
- T3 The render is nondeterministic. Two branches that each run `make readme` conflict on README.md and the stamp. Invariant: one render per source change, on one branch. Untested; the packets enforce it by "no `make readme`".
- T4 `make readme` runs `git checkout -- README.md` on a failed verify. Safe only because the README is never hand-edited; a worktree with a stray README edit loses it.
- T5 The main checkout's index is never touched by a worktree's `make check` (a worktree has its own index); the shared object store is. `git diff --quiet` in respeak-check may refresh an index; a two-minute `git status` (D1) means a slow, not a wrong, check. No invariant needed.
- T6 No bash suite has a timeout; a hung fake or a slow python is a hang in `make test` until the relay's wall clock. Invariant: every suite finishes under a minute. Fix: `timeout` in the Makefile's test loop.

## 5. TLA+

No protocol here deserves a model: the render loop is two bounded rounds, the overrides are per-session markers, the hooks are stateless. This repo appears in the relay's model as one leaf step, `make check`, with a wall clock, and must have no branch that spawns the relay.

## 6. Decisions for the owner

1. R6-4: keep Apple's python as a hook-time candidate for other machines, and record it in config-layers "Trust boundaries". Consumer: the R7 packet writer.
2. R6-22: rows files go repo-relative and the relay resolves the prompt against `repo`. Consumers: the relay's row-shape owner; this repo's next packet writer.
3. R6-19: CLAUDE.md gets one sentence, under about ten new lines the gate is the pass. Consumer: the owner's editorial pass.
4. Queue one packet, R7, for F1, F2, F4, F5, T1, T2, T6, each with a test. Consumer: the relay orchestrator.
