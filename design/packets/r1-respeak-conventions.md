# Packet R1: conventions, hygiene and the provider layer in claude-code-respeak

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §1, §2, §3, §5, §6; `design/overhaul-r1.md` §5, D11 in §7; `design/research.md` §1 (the respeak row); `design/plan.md` row 8. The builder reads THIS packet and those sections only |
| pin | claude-code-respeak `main` at `5a5819b` or later; claude-code-session `main` at `a78158d` (the two copied scripts). Branch `r1-respeak-conventions`, worktree `.claude/worktrees/r1-respeak-conventions` off `main` |
| wall | this repo. Read-only: the claude-code-session checkout beside this repo, four files: `scripts/hygiene`, `scripts/doclint`, `.hygiene-allow`, `design/conventions.md`. No other repo; no push; no `--amend` |
| may touch | new: `Makefile`, `.python-version`, `.hygiene-allow`, `scripts/hygiene`, `scripts/doclint`, `tests/test_provider_layer.py`. Edit: both files under `.claude-plugin/`, `scripts/respeak-config.py`, `scripts/respeak-gate.sh`, `tests/test_config_layers.py`, `tests/test_hooks.sh`, `tests/test_report_env.sh`. Human lane, only what §3 names: `CLAUDE.md`, `README.md`, `docs/config-layers.md`, `research/sources/deai-language-landscape.md`. Nothing else; anything else is a report line |
| acceptance | the twelve lines of §6 with their baselines; the gate reruns them on the branch |
| budget | 100 turns, 120k context; commit per item; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

conventions §1: "`scripts/hygiene` the public-hygiene scan, byte-identical across the repos (canonical: claude-code-session)"; "`.claude-plugin/marketplace.json` name = the repo name (exception: `respeak`)". §2: "`author {name}`". §3: "the session's resolved file when present" above respeak's folder and scope files; "accepts the file only when `provider.version` is inside its declared range ... never writes it ... Absent, it behaves as it does alone." overhaul-r1 §7 D11: "respeak's (`respeak` today) is either renamed in R1 or listed as the exception." research §1, the respeak row: domain 1/1, person 12/6, sibling self 1103/66, every other group 0.

## 2. Rulings

D11 (the owner, 2026-09-22): one marketplace per repo, named for the repo, the shape a new repo copies, no exception list. The marketplace is renamed `claude-code-respeak`; conventions §1's exception is void. Python (the owner, same day): never Apple's `/usr/bin/python3`; the repo's scripts run under a pyenv virtualenv on 3.12; a doctor suggests newer as released. It binds this repo's tooling (Makefile, tests, CLAUDE.md), not the plugin's hook-time interpreter search in `scripts/respeak-python.sh`, which stays. The two copied scripts keep their Apple shebang; the Makefile runs them as `$(PYTHON) scripts/...`, so it is never used here. R25-91 (3): respeak works without the session; the resolved file is one override layer, never a requirement, empty when absent. Packets-1's handover: respeak stays 0.6.x (the session pins `^0.6`); no version bump or CHANGELOG entry here, the owner's release act. Cut around, not ruled: the `plugin/` subtree (the plugin stays at the root); `make readme`, `install`, `doctor` (later rows); the human-lane editorial pass, which the builder cannot run: the four human-lane edits are code spans, one table row and one link, never prose, listed in the report for the owner's pass.

## 3. Interfaces (signatures, not prose)

- `Makefile`: `PYTHON ?= $(shell python3 -c 'import sys; print(sys.executable)')`, exported; `check: test lint doclint hygiene validate`; `test:` `$(PYTHON) -m unittest discover tests`, then each `tests/*.sh` under `bash`; `lint:` `$(PYTHON) -m compileall -q scripts tests`, then `$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 12)'`; `doclint:` `$(PYTHON) scripts/doclint`, then `bash scripts/respeak-check.sh`; `hygiene:` `$(PYTHON) scripts/hygiene`; `validate:` `claude plugin validate .`, or `validate: skipped, no claude on PATH`, exit 0.
- `.python-version`: one line, `claude-code-respeak`, the pyenv virtualenv. Bootstrap, when `pyenv versions --bare` lacks it: `pyenv virtualenv 3.12.7 claude-code-respeak && PYENV_VERSION=claude-code-respeak python3 -m pip install pyyaml`.
- `scripts/hygiene`, `scripts/doclint`: `cp` from the session checkout at the pin, mode 755; `shasum -a 256` reads the §6 prefixes. Never edited here.
- `.hygiene-allow`: `<path-glob>: <group>[,<group>]`, `*` inside one segment. Every `sibling` hit on main is the plugin's own name (no other sibling appears): one `sibling` glob per directory, with a comment saying so. `person`: `LICENSE`, `.claude-plugin/*.json` (author, owner), `README.md` (the repo URL). `design/packets/*: sibling,home,person`; `history/sittings/*.md: sibling,private`. The `home` and `person` docstring lines in `scripts/respeak-config.py` become placeholders, never allowlisted; the `person` fixture lines in `tests/test_report_env.sh` are rewritten, or allowlisted with a comment.
- `.claude-plugin/marketplace.json`: `name` `claude-code-respeak`; the plugin entry gains `version` equal to `plugin.json`'s. Its shape (the repo name, `owner {name}`, one plugin with `source`, `description`, `version`) is what a new repo copies. `plugin.json`: `author` loses `email`; nothing else changes.
- `scripts/respeak-config.py`: a layer `session` between `folders` and `env`, reading `${XDG_STATE_HOME:-~/.local/state}/claude-code-session/sessions/<session_id>/resolved.json`; `session_id` from `--session ID`, else `$CLAUDE_SESSION_ID`, else `$CLAUDE_CODE_SESSION_ID`; accepted when `provider.version` has major 2 (constant `SESSION_PROVIDER_MAJOR`); its `respeak` section is a tone-key layer (as the user layer); absent, unreadable, wrong major or no id: an empty layer, one warning at most, never fatal, never written. `explain` prints `provider: claude-code-session <version> profile <name>` or `provider: none`. `scripts/respeak-gate.sh` passes the payload's `session_id` as `--session`. `docs/config-layers.md`: one row in the layer table.
- Tests: `tests/test_provider_layer.py` fixtures a resolved file under a temporary `XDG_STATE_HOME` for accepted, wrong major, malformed JSON, absent and no session id; asserts values, warnings and the `explain` line. `tests/test_hooks.sh`, `tests/test_report_env.sh`: `"${PYTHON:-python3}"` wherever an interpreter is named; the fake-home fixture symlinks that binary.
- `CLAUDE.md`: the two `/usr/bin/python3` command lines become `python3`; the interpreter sentence names the virtualenv `.python-version` declares; "the test suites listed in the README" becomes `make check`. `README.md`: `respeak@respeak` becomes `respeak@claude-code-respeak` (three spans). `research/sources/deai-language-landscape.md` line 60: the dangling `url` link becomes text.

## 4. Findings that name this row

The scan on main: home 1/1, lan 0, domain 1/1, private 0, person 12/6, sibling 1114/67; outside the allowlist 1128 (no allowlist yet). The session's `doclint` at the pin refuses one thing, the dangling link. Validate, the gate, `unittest` and the five bash suites read 0 on main under pyenv 3.12.7. The rename changes the session's dependency row to `"marketplace": "claude-code-respeak"` and the owner's installed marketplace (remove `respeak`, add this repo, reinstall): report lines, not done here.

## 5. Forbidden reads

Every repo but this one and the four session files in the wall. `~/.claude/projects/` (transcripts hold secrets). `research/` beyond the one link; `README.md`, `CHANGELOG.md`, `docs/` beyond `grep -n` for the named spans and the layer table. The brief. No file over 8 KB whole.

## 6. Report (capped: one table, at most five bullets, under 1,500 words)

Each line, its exit and last output on the branch, beside main `5a5819b` under pyenv 3.12.7:

| line | main | branch |
|---|---|---|
| `make check >/dev/null 2>&1; echo $?` | 2 (no Makefile) | 0 |
| `python3 -m unittest discover tests 2>&1 \| tail -1` | `OK` | `OK` |
| `python3 scripts/hygiene; echo $?` | 2 (1128 outside; the session's copy) | 0 |
| `shasum -a 256 scripts/hygiene scripts/doclint \| cut -c1-8` | absent | `5232a0ef`, `510c7da5` |
| `python3 scripts/doclint; echo $?` | 2 (the session's copy) | 0 |
| `grep -c -E '"(name|version)": "(claude-code-respeak|0\.6\.[0-9]+)"' .claude-plugin/marketplace.json` | 0 | 2 |
| `grep -c '"email"' .claude-plugin/plugin.json` | 1 | 0 |
| `git grep -l 'usr/bin/python3' -- CLAUDE.md Makefile tests \| wc -l` | 3 | 0 |
| `cat .python-version` | absent | `claude-code-respeak` |
| `bash scripts/respeak-config.sh explain \| grep -c '^provider: '` | 0 | 1 |
| `claude plugin validate . 2>&1 \| tail -1; bash scripts/respeak-check.sh; echo $?` | `✔ Validation passed`, 0 | the same |
| `git status --short \| wc -l` after the last commit | 0 | 0 |

Bullets: hygiene counts per group after, with the allowlist entries and their reasons; the human-lane edits, span by span, for the owner's pass; the session's dependency change and the owner's marketplace re-add lines; what was left undone. Last line: the branch and its head sha.
