# Packet R4: the plugin subtree and the doclint re-sync in claude-code-respeak

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §1 (layout), §2 (marketplace), §3 (`doctor`), §5 (`validate`, the sidecar), §6 (the sha256); the decisions brief's items 24 and 26 as ruled 2026-09-22 16:30; the R3 handover (`history/sittings/2026-09-22-5.md`). The builder reads THIS packet; §1 quotes the rest |
| pin | claude-code-respeak `main` at `cf4d924` or later. Branch `r4-plugin-and-sync`, worktree `.claude/worktrees/r4-plugin-and-sync` off it |
| wall | this repo. No other repo; no push; no `--amend`; no rebase; no device. Real `claude`: only `plugin validate`, the two `--json` lists, the render |
| may touch | edit: `Makefile`, `CHANGELOG.md`, `CLAUDE.md`, `.hygiene-allow`, `.claude-plugin/marketplace.json`, `.claude/respeak/config.yaml`, `design/readme/source.md`, `design/readme/rendered.sha256`, `README.md` (by `make readme` only), `docs/architecture.md`, `scripts/doclint`, the eleven files `git ls-files tests` names (path spans only); git mv into `plugin/` (path spans only): `.claude-plugin/plugin.json`, `agents/`, `config/`, `corpus/`, `hooks/`, `skills/`, `docs/config-layers.md`, every `scripts/*` except `hygiene`, `doclint`, `readme-fresh.sh`; new: `plugin/scripts/respeak-doctor.sh`, `tests/test_doctor.sh`, `tests/test_install.sh`, the charter `history/sittings/<run day>-<n>.md`. Nothing else |
| acceptance | the lines of §6 with their baselines; the gate reruns them on the branch |
| verify | `make check` |
| budget | 80 turns (the move and one render), 60k context; commit per act; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

§1: "`plugin/` the plugin subtree, self-contained: names no path outside itself"; "`hooks/run` execs `<tool> hook <event>` when on PATH, else exits 0 silently"; the tool is "on PATH via `make install`" §2: "`source: "./plugin"`". §3: a plugin "reports its provider in `doctor`"; unknown keys are "reported by `doctor`, never fatal". §5: "`validate` (`claude plugin validate plugin/`)"; the sidecar "holds the full `shasum -a 256 design/readme/source.md` line", checked "by `shasum -c --status`". §6: `scripts/doclint` is `b46db3dfed41b9d3cf9298dbfdb2d83781e9ee041c1d9b5a94c032e0c4b7aa21`. Items 24, 26: "respeak's already matches"; "keep the byte-identical rule". R3: "Named for R4: the `plugin/` subtree with `hooks/run`, `make install`, `make doctor`, and `validate` on `plugin/`". The standing word: decide inside the design, record the choice, escalate only a real fork.

## 2. Rulings

Act 1: S7 changed `scripts/doclint` only (`scripts/hygiene` is still `fb05f620`, measured); the whole diff is the conventions ceiling, quoted in §3; the file and `DOCLINT_SHA` move in one commit; the proof is the sha256. Act 2: build the subtree. The installed 0.6.1 carries all 100 tracked files because the marketplace source is the repo root. Moves: the manifest, `agents/`, `config/`, `corpus/`, `hooks/`, `skills/`, the sixteen shipped scripts, and `docs/config-layers.md` (the skills and the agent name it as the contract; an installed plugin must carry it). Self-contained means: nothing under `plugin/` opens or executes a path outside it; comments and prose may cite the repository's tree. `${CLAUDE_PLUGIN_ROOT}` spans stay: the root moves, the paths under it do not. Tests: the plugin root is `$REPO_ROOT/plugin`. Docs: path spans by hand (R3's precedent). The README: Layout, Install (`--plugin-dir "$RESPEAK_SRC/plugin"`), the path spans and the contract link change in the source, then ONE render. Version: `v0.6.1` is untagged, so the 0.6.1 entry grows; if the tag exists at open, a `## 0.7.0` entry and both manifests. `hooks/run`: not built; it reaches a tool the plugin does not carry, and respeak's `hooks.json` already names its own scripts by `${CLAUDE_PLUGIN_ROOT}`. Act 3: `make doctor` runs `plugin/scripts/respeak-doctor.sh`, one line per check, exit 0 unless no PyYAML python (2), tested with a fake `claude` on a temporary PATH. Act 4, only if turns remain after act 3, else the handover names it for R5: `make install` installs the plugin from THIS checkout and never removes a registration. Item 24: build nothing; the sidecar's line 1 is the ruled line, checked by `shasum -a 256 -c --status`; line 2 is CLAUDE.md's README tamper guard. `python3` is the pyenv virtualenv.

## 3. Interfaces (signatures, not prose)

- `scripts/doclint`: after `RECORD_CEILING = 6144` add `CONVENTIONS_CEILING = 8192`; in `check_sizes` the loop body becomes:

```python
        if match(path, "design/conventions*.md"):
            ceiling = CONVENTIONS_CEILING
        elif match(path, "design/research*.md"):
            ceiling = RECORD_CEILING
        else:
            continue
        size = len(read(repo, path))
        if size >= ceiling:
            out.append("%s: size: %d bytes, ceiling %d" % (path, size, ceiling))
```

- `Makefile`: `DOCLINT_SHA` holds the §6 pin; `doclint:`, `readme:` name the scripts under `plugin/scripts/`; `validate:` runs `claude plugin validate plugin/` then `claude plugin validate .` behind the existing guard; `doctor:` runs `bash plugin/scripts/respeak-doctor.sh`; `install:` (act 4). `check` is unchanged.
- `.claude-plugin/marketplace.json`: `"source": "./plugin"`. `.hygiene-allow`: one `plugin/<dir>/*: sibling` row per moved directory (`skills/*/*`, `corpus/style/*` as today), `plugin/.claude-plugin/*: sibling,person`; the old rows go.
- `.claude/respeak/config.yaml`: `exclude` names `plugin/corpus/**`; the human-lane scope gains `plugin/docs/**`. `CLAUDE.md`: the human lane names `docs/` and `plugin/docs/`; its code spans move.
- `plugin/scripts/respeak-doctor.sh` prints six lines: `python: <path> <version> pyyaml=<yes|no>`; `claude: <version>` or `claude: missing`; `marketplace: claude-code-respeak <source> <path>` or `marketplace: none`; `plugin: respeak@claude-code-respeak <version>, manifest <version>` or `plugin: not installed`; `provider: ...` as `respeak-config.sh explain --for README.md` prints it; `config: <n> unknown keys`.
- `tests/test_doctor.sh`: a fake `claude` answers with canned JSON; asserts the six lines and exit 0, and `claude: missing` without it.
- `make install` (act 4): no marketplace named `claude-code-respeak`: `marketplace add "$(CURDIR)"`, then `plugin install respeak@claude-code-respeak`; one whose `path` is `$(CURDIR)`: `marketplace update`, then `plugin update`; any other source: print it and the two commands the owner would run, exit 2. `tests/test_install.sh`: the fake `claude` records argv; the three cases.
- `CHANGELOG.md`: one bullet per act, each naming its failure (the cache carried the whole repository; the doclint drift; a silent hook; act 4's install).

## 4. Findings that name this row

On `main` `cf4d924` under pyenv 3.12.7: `make check` 0 in 44 s (218 tests). `scripts/hygiene` equals the canonical copy; `scripts/doclint` differs by the ceiling only, and the canonical copy run on this tree exits 0. No `plugin/`; 19 tracked scripts, 16 shipped; 100 tracked files, all in the installed cache. `CLAUDE_PLUGIN_ROOT` appears in 28 files; shipped files cite `docs/config-layers.md` in 20 places. The marketplace on this Mac is GitHub-sourced; the sibling ones are directories. Tags: `v0.5.0` to `v0.5.2`.

## 5. Forbidden reads

Every repo but this one. `~/.claude/projects/`. `~/.claude/plugins/` beyond the two `--json` lists. `research/`. `examples/` beyond `git ls-files`. `README.md` (rendered, never edited by hand). `design/readme/source.md` beyond Layout, Install and `grep -n` for path spans. The docs beyond `grep -n` and the lines it names. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's own charter. The relay's ledgers. The brief.

## 6. Report (capped: one table, at most five bullets, under 1,200 words)

Each line, its exit and last output on the branch, beside `main` `cf4d924` under pyenv 3.12.7:

| line | main | branch |
|---|---|---|
| `make check >/dev/null 2>&1; echo $?` | 0 | 0 |
| `shasum -a 256 scripts/doclint scripts/hygiene \| cut -c1-8 \| tr '\n' ' '` | `f5a9ae84 fb05f620` | `b46db3df fb05f620` |
| `grep -c b46db3dfed41b9d3cf9298dbfdb2d83781e9ee041c1d9b5a94c032e0c4b7aa21 Makefile` | 0 | 1 |
| `claude plugin validate plugin/ >/dev/null 2>&1; echo $?` | 1 | 0 |
| `grep -c '"source": "./plugin"' .claude-plugin/marketplace.json` | 0 | 1 |
| `git ls-files scripts plugin \| wc -l` | 19 | 35 |
| `test -f plugin/docs/config-layers.md -a ! -f docs/config-layers.md; echo $?` | 1 | 0 |
| `shasum -a 256 -c --status design/readme/rendered.sha256; echo $?` | 0 | 0 |
| `make doctor >/dev/null 2>&1; echo $?` | 2 | 0 |
| `grep -c '^install:' Makefile` | 0 | 1 (0 if act 4 was not built; the report says) |
| `git status --short \| wc -l` after the last commit | 0 | 0 |

Bullets: each act's commit, one line; the choices made inside the design beyond §2, with their reason; the render rounds; what was left undone and for whom (act 4 for R5 if unbuilt; `make install` and the tag for the owner); at most ONE open fork for the owner. Last line: the branch and its head sha.
