# Packet R11: the post-S12 re-sync, and the `bounded` half of ADV10 closed by the copy

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §5, §6 and §9 at its `main` `330bded`; the S12a and S12b charters' re-sync lines; `design/review-adv10.md` ADV10-2 (the `bounded` half), ADV10-4 and ADV10-5, which packet R10 §2 left to the canonical `bounded` |
| pin | claude-code-respeak `main` at this packet's commit or later. Branch `r11-resync`, worktree `.claude/worktrees/r11-resync` off it. The copy source is the session checkout beside this one, `S=$(dirname "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")")/claude-code-session`, read as three blobs by `git -C "$S" show 330bded:scripts/<name>` and nothing else there |
| wall | this repo; no push, `--amend`, rebase, device, tag, version bump, `make readme`; the canonical scripts are copied, never edited; `make check` at most twice; no test opens a path under the real checkout except the script it tests |
| may touch | `scripts/hygiene`, `scripts/doclint`, `scripts/bounded`, `Makefile`, `tests/test_bounded.sh`, `CHANGELOG.md` (one bullet under `## Unreleased`), and, one header row each, `design/packets/r1-respeak-conventions.md`, `design/packets/r2-readme.md`, `design/packets/r3-respeak-followups.md`, `design/packets/r4-plugin-and-sync.md`, `design/packets/r5-resync.md`, `design/packets/r6-resync.md`, `design/packets/r7-fixes-r6.md`, `design/packets/r10-fixes-adv10.md`; the charter. Nothing else |
| acceptance | the lines of §6 with their baselines, targeted, each under a minute |
| verify | `make check` |
| budget | one row, `r11-resync`, 50 turns, 144k context; one commit per act; the charter's open names doclint's five rows; checkpoint at 80% |

## 1. What the source says (quoted)

Conventions §5: "`check` runs under `scripts/bounded --lock .check.lock --wall 840 --load 4`"; "A last stderr line `bounded: stop: lock|load|wall` (exits 2, 2, 124) is unrun, never red." §6: "Every copy of `scripts/hygiene` has sha256 `efc5915222e8b9e36d127ab5974f84e3c3818636c0af185539af3db16c5dbb89`, of `scripts/doclint` `b924a7bca4446e38690c2edb8b35a5db2ad91a5b9b679bbbb178388a8dfbab4c`." §9: "The `verify` row is required (doclint's GRANDFATHERED packets excepted)." S12b: "Every sibling copy (respeak, agent-relay, decisions) must take both at its next re-sync." ADV10-5: "The canonical copy lives in the session plugin; this repo carries it verbatim."

## 2. Rulings

Act 1, the re-sync, ONE commit, `make check` green at it. The three scripts byte-identical to the blobs at `330bded` (`bounded` sha256 `63cebd3dbd7605eb22441529554025d801439f91e14120ef00d04bbd8f187454`, unpinned as today). `HYGIENE_SHA` and `DOCLINT_SHA` in the `Makefile` move to the §1 values in the same commit, so `make hygiene` never reads red. The `check` recipe's wall moves from 900 to 840 (§5), and its comment's number with it. The new doclint refuses eight packets with `verify row missing`; GRANDFATHERED lives in the canonical copy, so each gets one header row after its `acceptance` row, `verify` then `make check`, as in r8: the gate every respeak row ran under, a fact added, no ruling rewritten. `r7-fixes-r6.md` and `r10-fixes-adv10.md` would pass the 9,216-byte ceiling, so their `acceptance` cell drops its closing clause, the one that begins "the verify line is" (the new row states it). The new `bounded` keeps a flock lock FILE after a run, so `test_bounded.sh`'s case "...and the lock is released" becomes "a second run after the first takes the lock and runs" (rc 0). The mkdir-era live-holder case stays; the new copy still refuses it with 2. Hygiene needs no allow row (measured: 0 hits outside the allowlist).

Act 2, ADV10 confirmed by the copy, a test per finding, then the words. In `test_bounded.sh`, each case red against the old copy (`git show HEAD~1:scripts/bounded` to a temp path, run once, noted in the charter) and green against the new one:
- ADV10-4: a load refusal (`BOUNDED_LOADAVG=1000 BOUNDED_LOAD_MAX=1 BOUNDED_LOAD_POLL=1`, `--load 4 -- touch <marker>`) exits 2, its last stderr line is `bounded: stop: load`, and the marker is absent; the wall's last line is `bounded: stop: wall` (rc 124); a held lock's is `bounded: stop: lock` (rc 2).
- ADV10-5: two runners started together on one lock file, each `sh -c 'touch <dir>/$$; sleep 1'`: exactly one marker, and one runner exits 2. A leftover lock DIRECTORY whose owner pid is dead is removed and the run goes ahead (rc 0).
- ADV10-2, the `bounded` half: `bounded --wall 20 -- sleep 353` started under python `os.setsid` with `BOUNDED_GRACE=1`, the group SIGKILLed at 1 s: no `sleep 353` (found by `pgrep -f`) 3 s later. Kill any survivor in the test's trap.
Then the `Makefile` comment over `check` says what `make check`'s exit means: make reads any failure as 2, so the exit alone does not tell a refusal from a red suite; a last stderr line `bounded: stop: lock|load|wall` means the suite did not run to its end, unrun and never red (§5), and the relay's gate reads that line. One CHANGELOG bullet under `## Unreleased` covers both acts.

Later, for other rows: `design/readme/source.md` line 271 still says "a 900 s wall"; the next README round says 840 (the builder does not render). ADV10-4's reader half is the relay's gate (agent-relay's re-sync row). ADV6-4 stays its own packet.

## 3. Interfaces (signatures, not prose)

- `make check`: `scripts/bounded --lock .check.lock --wall 840 --load 4 -- $(MAKE) check-unlocked`; exits 0, or 2 for any failure; unrun when the last stderr line is `bounded: stop: lock|load|wall`.
- `scripts/bounded`: the session's, verbatim; exits the command's own, 124 wall, 2 lock or load, 1 usage, 127 cannot start.
- A packet header's `verify` row: cells `verify` and `make check` (in code), after `acceptance`.
- Commits `r11 act N: <one line>`; the charter title `# Sitting <run day>-<n>: claude-code-respeak, r11-resync`.

## 4. Findings that name this row

Measured on `main` `2095db5` under the virtualenv (3.12.7), the session's three scripts run from a temp copy: hygiene `hits outside allowlist: 0` (rc 0); doclint rc 2, `verify row missing` on exactly the eight packets above (r8 and r9 carry one); `test_bounded.sh` against the new copy 6 passed, 1 failed (the lock-released case). The old copy: a load refusal's last line is `bounded: load 1000.00 above 64.00 (4 x 16 cores) for 1 s`, the group-kill repro leaves one `sleep 353`. The new copy: `bounded: stop: load`, `stop: wall`, `stop: lock`, and 0 survivors. Byte sizes before the row: r6 9,194 (9,215 after), r7 9,204, r10 9,198.

## 5. Forbidden reads

Every other repo, beyond the three blobs of the pin row. `~/.claude/`. `research/`; `examples/`. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's charter. `design/packets/` beyond the eight packets' header tables. The relay's ledgers; any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line's last output on the branch beside `main` at this packet's commit:

| line | main | branch |
|---|---|---|
| `shasum -a 256 scripts/hygiene scripts/doclint scripts/bounded \| cut -c1-8 \| paste -sd' ' -` | `ca049635 3040666c e6079e68` | `efc59152 b924a7bc 63cebd3d` |
| `make hygiene 2>&1 \| tail -1` | `hits outside allowlist: 0` | `hits outside allowlist: 0` |
| `grep -L '^\| verify \|' design/packets/r*.md \| wc -l \| tr -d ' '` | 8 | 0 |
| `grep -c -- '--wall 840 --load 4' Makefile` | 0 | 1 |
| `BOUNDED_LOADAVG=1000 BOUNDED_LOAD_MAX=1 BOUNDED_LOAD_POLL=1 python3 scripts/bounded --load 4 -- true 2>&1 \| tail -1` | `bounded: load 1000.00 above 64.00 (4 x 16 cores) for 1 s` | `bounded: stop: load` |
| `bash tests/test_bounded.sh 2>&1 \| tail -1` | `7 passed, 0 failed` | at least 13 passed, 0 failed |
| `git status --short \| wc -l \| tr -d ' '` after the last commit | 0 | 0 |

Bullets: each act's commit; choices beyond §2 with reasons; what was left undone and for whom; at most ONE open fork. Last line: the branch and its head sha.
