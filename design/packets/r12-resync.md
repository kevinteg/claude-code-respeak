# Packet R12: the post-S13 re-sync, one test for the one-cut `bounded`, and the README at 840 s

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §5, §6 and §9 at its `main` `35b5870`; the S13a and S13b charters' re-sync lines (hygiene `d63d0ffb`, doclint `d5957c6c`, bounded `e343b094`); packet R11 §2's "later" line (the README still says 900 s) |
| pin | claude-code-respeak `main` at this packet's commit or later. Branch `r12-resync`, worktree `.claude/worktrees/r12-resync` off it. The copy source is the session checkout beside this one, `S=$(dirname "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")")/claude-code-session`, read as three blobs by `git -C "$S" show 35b5870:scripts/<name>` and nothing else there |
| wall | this repo; no push, `--amend`, rebase, device, tag, version bump; the canonical scripts are copied, never edited; `make readme` once, in act 3; `make check` at most twice; no test opens a path under the real checkout except the script it tests |
| may touch | `scripts/hygiene`, `scripts/doclint`, `scripts/bounded`, `Makefile`, `tests/test_bounded.sh`, `CHANGELOG.md` (one bullet under `## Unreleased`), `design/readme/source.md`, `design/readme/rendered.sha256`, `README.md` (by `make readme` only); the charter. Nothing else |
| acceptance | the lines of §6 with their baselines, targeted, each under a minute |
| verify | `make check` |
| budget | one row, `r12-resync`, 50 turns, 144k context; one commit per act; the charter's open names doclint's five rows; checkpoint at 80% |

## 1. What the source says (quoted)

Conventions §5: "`check` runs under `scripts/bounded --lock .check.lock --wall 840 --load 4`"; "A last stderr line `bounded: stop: lock|load|wall` (exits 2, 2, 124) is unrun, never red." §6: "Every copy of `scripts/hygiene` has sha256 `d63d0ffb3775b3e4ba5ee8cdde48f6f73b71ab588ea6de824772f0b9e19adb09`, of `scripts/doclint` `d5957c6c282aa14ca57698ebdc82f5cf24b38325b9fa7bb404d1edfec2d65d1e`." §9: "The `verify` row is required (doclint's GRANDFATHERED excepted: 28 unrowed packets, this repo's 11 and agent-relay's 17)". S13b: "`bounded` ignores TERM, INT and HUP once the handler starts, so a second signal cannot start a second cut." S13a: "hygiene binary groups home, secret, email (ADV10-17)".

## 2. Rulings

Act 1, the re-sync, ONE commit, `make check` green at it. The three scripts byte-identical to the blobs at `35b5870` (`bounded` sha256 `e343b0943eff6507a3bc696d73a67f386ecfceaa652dc8bbd8a0cea9c2d5afa3`, unpinned as today). `HYGIENE_SHA` and `DOCLINT_SHA` in the `Makefile` move to the §1 values in the same commit, so `make hygiene` never reads red. Nothing else moves: measured (§4), the new hygiene finds 0 hits outside the allowlist, so no allow row; the new doclint passes every packet and charter, so no packet is edited (GRANDFATHERED holds the historical stems); `tests/test_bounded.sh` passes whole against the new copy. If the builder's measurement disagrees, it decides inside §5 and §9 and names the choice in the charter.

Act 2, S13b's one cut, a test, then the words. One case in `tests/test_bounded.sh`: `BOUNDED_GRACE=2 bounded --wall 20 -- sh -c 'trap "" TERM; sleep 32'` sent TERM, then INT 0.2 s later, then HUP 0.2 s later, exits 143 (the first signal's 128+15), with no `Traceback` on stderr and no `sleep 32` (by `pgrep -f`) 3 s later; kill any survivor in the test's trap. Run it once against the old copy (`git show HEAD~1:scripts/bounded` to a temp path, `BOUNDED=<path>`) and note the result in the charter; measured, the old copy exits 129 (the last signal re-entered the cut). One CHANGELOG bullet under `## Unreleased` covers acts 1 and 2: the re-sync to `35b5870`, the binary scan (a secret or home path inside a binary is a hit, a UTF-16 file is text, a file over 4 MiB is scanned by path only), and the one cut.

Act 3, the README, last. `design/readme/source.md` line 271 says "an 840 s wall" where it says "a 900 s wall"; nothing else in the source changes. The builder runs `make readme` once, at close, per the README round's rules: the render is the repo's own `scripts/readme-render.sh` in technical mode, the verifier `respeak-verify-edit.py` must pass before the move, the renderer writes the status line (version, the day, the live unittest and bash-suite counts), and the sidecar moves in the same commit. If the render or its verifier refuses, the act commits the source edit alone, `make check` reads the README stale, and the charter says so; no second render.

Later, for other rows: none known.

## 3. Interfaces (signatures, not prose)

- `make check`: `scripts/bounded --lock .check.lock --wall 840 --load 4 -- $(MAKE) check-unlocked`; exits 0, or 2 for any failure; unrun when the last stderr line is `bounded: stop: lock|load|wall`.
- `scripts/bounded`: the session's, verbatim; exits the command's own, 124 wall, 2 lock or load, 1 usage, 127 cannot start, 128+signum on the first of TERM, INT or HUP.
- `make readme`: `bash scripts/readme-render.sh`; writes `README.md`, the source's status line and `design/readme/rendered.sha256`, or nothing.
- Commits `r12 act N: <one line>`; the charter title `# Sitting <run day>-<n>: claude-code-respeak, r12-resync`.

## 4. Findings that name this row

Measured on `main` `e5f31ed` under the virtualenv (3.12.7), the session's three scripts at `35b5870` run from a temp copy: hygiene `hits outside allowlist: 0` (rc 0); doclint rc 0 over every packet and charter; `BOUNDED=<copy> bash tests/test_bounded.sh` `18 passed, 0 failed`. A single TERM gives 143 on both copies. TERM, INT, HUP in turn: the old copy exits 129, the new 143; neither prints a traceback or leaves a survivor. The README and its source each say "a 900 s wall" once; the Makefile already walls at 840 (R11).

## 5. Forbidden reads

Every other repo, beyond the three blobs of the pin row. `~/.claude/`. `research/`; `examples/`. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's charter. `design/packets/` beyond this packet. The relay's ledgers; any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line's last output on the branch beside `main` at this packet's commit:

| line | main | branch |
|---|---|---|
| `shasum -a 256 scripts/hygiene scripts/doclint scripts/bounded \| cut -c1-8 \| paste -sd' ' -` | `efc59152 b924a7bc 63cebd3d` | `d63d0ffb d5957c6c e343b094` |
| `make hygiene 2>&1 \| tail -1` | `hits outside allowlist: 0` | `hits outside allowlist: 0` |
| `grep -c d63d0ffb3775b3e4ba5ee8cdde48f6f73b71ab588ea6de824772f0b9e19adb09 Makefile` | 0 | 1 |
| `bash tests/test_bounded.sh 2>&1 \| tail -1` | `18 passed, 0 failed` | `19 passed, 0 failed` |
| `cat design/readme/source.md README.md \| grep -c '900 s wall'` | 2 | 0 |
| `bash scripts/readme-fresh.sh 2>&1 \| tail -1` | `readme: fresh` | `readme: fresh` |
| `git status --short \| wc -l \| tr -d ' '` after the last commit | 0 | 0 |

Bullets: each act's commit; choices beyond §2 with reasons; what was left undone and for whom; at most ONE open fork. Last line: the branch and its head sha.
