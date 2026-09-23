# Packet R3: the follow-ups after R1 and R2 in claude-code-respeak

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §1 (the canonical scripts), §3 (the session id), §6 (the sha256); the decisions brief's items 25, 26, 30, 38 as ruled 2026-09-22 16:30; the R1 and R2 handovers (`history/sittings/2026-09-22-2.md`, `2026-09-22-3b.md`). The builder reads THIS packet and those only |
| pin | claude-code-respeak `main` at `6b1e529` or later. Branch `r3-respeak-followups`, worktree `.claude/worktrees/r3-respeak-followups` off it |
| wall | this repo. No other repo (the canonical bytes are quoted here by sha); no push; no `--amend`; no rebase; no device |
| may touch | edit: `Makefile`, `CHANGELOG.md`, `docs/config-layers.md`, `scripts/respeak-config.py`, `scripts/respeak-config.sh`, `scripts/respeak-session.sh`, `scripts/hygiene`, `scripts/doclint`, `skills/respeak/SKILL.md`, `tests/test_overrides.sh`, `tests/test_provider_layer.py`, `tests/test_config_layers.py`; new: `history/sittings/2026-09-22-5.md` (the charter; dated by the run's day). Nothing else; anything else is a report line |
| acceptance | the lines of §6 with their baselines; the gate reruns them on the branch |
| budget | 60 turns, 60k context; commit per act; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

conventions §3: "A plugin takes `session_id` from hook stdin or `$CLAUDE_CODE_SESSION_ID`". §1: `scripts/hygiene` is "byte-identical across the repos (canonical: claude-code-session)". §6: "Every copy has sha256 `fb05f6203ac904a0839345e257d4cf39855bcfbb8ebc25f307684c275f111d4d`". Item 25: "rule `CLAUDE_CODE_SESSION_ID` only; respeak drops the first name". Item 26: "re-sync the copies ... keep the byte-identical rule rather than allowing a differing first line". Item 30: "the `person` group ignores `history/sittings/**` in every repo (charters are records; the README and code stay scanned)". Item 38: "leave the hook's finder and its fixture as they are". The R1 handover: "The session layer reads `$CLAUDE_SESSION_ID` first". The owner's standing word: decide inside the design, record the choice in the charter, escalate only a real fork.

## 2. Rulings

Act 1 is repo-wide, not the provider layer alone: measured today, a Claude Code Bash tool has `CLAUDE_CODE_SESSION_ID` set and `CLAUDE_SESSION_ID` unset, so `respeak-session.sh status` prints `session: unknown (CLAUDE_SESSION_ID unset)` and `/respeak:off` refuses in a real session. Every reader (eight files) moves to the one name; the precedence test goes, one assertion stays that the old name alone yields `provider: none`. The docs edit is one code span, by hand, no editorial pass (no prose changes). The CHANGELOG bullet names the failure and so names the old variable; the grep line excludes it. Act 2: both scripts differ from the canonical copies in line 1 only (claude-code-session `main` at `4901b1b`, measured), so the edit is the shebang and the proof is the sha256. The gate is two pins in the Makefile, not a `cmp`: a public repo names no sibling path and the canonical repo is outside the wall; the `hygiene` target checks the pins before it scans. If the session's S7 row changes the scripts again, that is a later re-sync: files and pins move together. Act 3: after act 2 the canonical script still scans `history/sittings/**` for `person`, so the one place is this repo's allowlist row `history/sittings/*.md: sibling,private,person`, already on `main` (17e488d); build nothing, the report says so; a canonical rule later removes the row in that re-sync. Act 4: record, build nothing; `test_gate_hook.sh` lines 164 to 170 stay bare. Act 5: the only small open follow-up is act 1 (R1's fifth bullet). Closed here: the icon line under the README title stays (the renderer's preamble strip is by design); the `/`-rooted links stay. Named for R4, not this row: the `plugin/` subtree with `hooks/run`, `make install`, `make doctor`, `validate` on `plugin/`. Act 6: items 36 and 39 are the owner's: the editorial reads at merge; the tag `v0.6.1` after this branch merges. No version bump: no tag exists yet, so the 0.6.1 entry grows and the manifests stay. `make readme`: no described README section changes, zero renders expected; at most two if one does, counted in the charter. `python3` is the pyenv virtualenv.

## 3. Interfaces (signatures, not prose)

- `scripts/respeak-config.py`: `SESSION_ID_ENV = ("CLAUDE_CODE_SESSION_ID",)`; the docstring line and the `--session` help read `else $CLAUDE_CODE_SESSION_ID`.
- `scripts/respeak-session.sh`: `sid="${CLAUDE_CODE_SESSION_ID:-}"`; the header comment and both messages name that variable. `scripts/respeak-config.sh` lines 24 and 27: the same.
- `skills/respeak/SKILL.md` lines 41 and 56: `/tmp/respeak-${CLAUDE_CODE_SESSION_ID}.yaml`. `docs/config-layers.md` line 515: the code span only.
- `tests/test_overrides.sh`: every `CLAUDE_SESSION_ID` (17) becomes `CLAUDE_CODE_SESSION_ID`, the `unset` line and the check labels included. `tests/test_config_layers.py` line 485: the pop of the old name goes.
- `tests/test_provider_layer.py` `test_session_id_from_the_environment`: the loop stays; the two precedence asserts become one, `env(CLAUDE_SESSION_ID=SID)` alone gives `provider: none`; `--session` over `CLAUDE_CODE_SESSION_ID="other"` stays.
- `scripts/hygiene`, `scripts/doclint`: line 1 `#!/usr/bin/env python3`; nothing else changes; sha256 `fb05f620...` and `f5a9ae84fd112c48818799dd6f96c3fbbaae7dc0ad6df62886c93953ea70bdd4`.
- `Makefile`: `HYGIENE_SHA` and `DOCLINT_SHA` hold the two full pins; `hygiene:` gains a first line, `@printf '%s  %s\n' $(HYGIENE_SHA) scripts/hygiene $(DOCLINT_SHA) scripts/doclint | shasum -a 256 -c --status || { echo "hygiene: scripts/hygiene or scripts/doclint differ from the canonical copies (conventions section 6)"; exit 2; }`.
- `CHANGELOG.md`: two bullets appended to `## 0.6.1 (2026-09-22)`, each naming its failure: `/respeak:off` refused in a real session because it read `CLAUDE_SESSION_ID`, which Claude Code does not set; the two canonical scripts drifted from claude-code-session's by their first line, and `make hygiene` now checks their sha256 pins.

## 4. Findings that name this row

On `main` `6b1e529` under pyenv 3.12.7: `make check` 0 (unittest `Ran 218 tests`, `OK`, six bash suites, `readme: fresh`, `✔ Validation passed`). `CLAUDE_SESSION_ID` is read in eight tracked files outside the records (33 spans; `tests/test_overrides.sh` holds 17). Both scripts carry `#!/usr/bin/python3`; sha256 `5232a0ef...` and `510c7da5...`; the Makefile has no pin and no `cmp`. The allowlist row for charters is present. Both suites hold `"${PYTHON:-python3}"` twice. Tags: `v0.5.0` to `v0.5.2`; no `v0.6.1`. The README and its source name no session variable. Outside the wall, named, not done: the marketplace re-add on this Mac and the tag (the owner); the session's dependency row (the session's row).

## 5. Forbidden reads

Every repo but this one (§1 and §2 quote what the builder needs). `~/.claude/projects/`. `research/`. `docs/` beyond `grep -n CLAUDE_SESSION_ID`. `README.md` and `design/readme/source.md` (untouched). `CHANGELOG.md` beyond its first 30 lines. `scripts/respeak-config.py` beyond `grep -n` and the lines it names. `history/` beyond the builder's own charter. The relay's ledgers. The brief.

## 6. Report (capped: one table, at most five bullets, under 1,200 words)

Each line, its exit and last output on the branch, beside `main` `6b1e529` under pyenv 3.12.7:

| line | main | branch |
|---|---|---|
| `make check >/dev/null 2>&1; echo $?` | 0 | 0 |
| `git grep -l CLAUDE_SESSION_ID -- . ':!history' ':!design/packets' ':!CHANGELOG.md' \| wc -l` | 8 | 0 |
| `CLAUDE_CODE_SESSION_ID=S1 bash scripts/respeak-session.sh status \| head -1` | `session: unknown (CLAUDE_SESSION_ID unset)` | `session: S1` |
| `grep -c CLAUDE_CODE_SESSION_ID tests/test_overrides.sh skills/respeak/SKILL.md` | 0, 0 | 17, 2 |
| `grep -q CLAUDE_SESSION_ID CHANGELOG.md; echo $?` | 1 | 0 |
| `head -1 scripts/hygiene scripts/doclint \| grep -c 'env python3'` | 0 | 2 |
| `shasum -a 256 scripts/hygiene \| cut -c1-8` | `5232a0ef` | `fb05f620` |
| `shasum -a 256 scripts/doclint \| cut -c1-8` | `510c7da5` | `f5a9ae84` |
| `grep -c 'shasum -a 256 -c --status' Makefile` | 0 | 1 |
| `make hygiene >/dev/null 2>&1; echo $?` | 0 | 0 |
| `grep -c '^history/sittings/\*.md: .*person' .hygiene-allow` | 1 | 1 |
| `grep -c 'PYTHON:-python3' tests/test_overrides.sh tests/test_gate_hook.sh` | 2, 2 | 2, 2 |
| `grep -c '"version": "0.6.1"' .claude-plugin/plugin.json .claude-plugin/marketplace.json` | 1, 1 | 1, 1 |
| `shasum -a 256 -c --status design/readme/rendered.sha256; echo $?` | 0 | 0 |
| `bash scripts/respeak-check.sh >/dev/null; echo $?` | 0 | 0 |
| `git status --short \| wc -l` after the last commit | 0 | 0 |

Bullets: each act's commit and what it changed, one line each; the choices made inside the design beyond §2, if any, with their reason; the render rounds if any; what was left undone and for whom (R4's list, the owner's items 36 and 39); at most ONE open fork for the owner. Last line: the branch and its head sha.
