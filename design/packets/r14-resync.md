# Packet R14: the post-S15 re-sync, three pins, the account cells left for ADV12-9

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §5, §6 and §9 at its `main` after `s15-resync` merged; the run-12 re-sync prompt's respeak line ("re-pin the canonical scripts from the session's `main` AFTER s15-resync merges"; the shared account-cells table waits for the relay's review ADV12-9, deferred) |
| pin | claude-code-respeak `main` at this packet's commit or later. Branch `r14-resync`, worktree `.claude/worktrees/r14-resync` off it. The copy source is the session checkout beside this one, `S=$(dirname "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")")/claude-code-session`, bound ONCE at start as `P=$(git -C "$S" rev-parse main)`, and read as four blobs by `git -C "$S" show "$P":<path>` (`scripts/hygiene`, `scripts/doclint`, `scripts/bounded`, `design/conventions.md`) and nothing else there |
| wall | this repo; no push, `--amend`, rebase, device, tag, version bump; the canonical scripts are copied, never edited; no `make readme`; `make check` at most twice; no test opens a path under the real checkout except the script it tests |
| may touch | `scripts/hygiene`, `scripts/doclint`, `scripts/bounded`, `Makefile`, `.hygiene-allow` (only a row the measurement needs), `tests/test_bounded.sh` (only a case the new copy's measured behavior changes), `CHANGELOG.md` (one bullet under `## Unreleased`); the charter. Nothing else |
| acceptance | the lines of §6 with their baselines, targeted, each under a minute |
| verify | `make check` |
| budget | one row, `r14-resync`, 50 turns, 144k context; one commit per act; the charter's open names doclint's five rows; checkpoint at 80% |

## 1. What the source says (quoted)

Conventions §6 at the session's `main` `2a1dfcb` (S14, before S15): "Every copy of `scripts/hygiene` has sha256 `157edaff...`, of `scripts/doclint` `a45c3ec1...`, of `scripts/bounded` `b3c5f7fe...`." §6 now names THREE shas; this repo's `Makefile` pins two and calls `bounded` "unpinned". §9: "The `verify` row is required (doclint's GRANDFATHERED excepted ...)"; "SPENT ... keeps the row and skips the suite rule." The re-sync prompt: S15 moves doclint's SPENT to the relay's spent stems and takes review ADV11-15 (a file over 4 MiB) into hygiene; this repo copies the result and does not copy the account-cells table until ADV12-9 lands.

## 2. Rulings

Act 0, the precondition, fail early. Open the charter. If `git -C "$S" log --merges --oneline "$P" | grep -c s15-resync` reads 0, copy nothing: close the charter with "s15-resync not merged at `<P>`", no NEXT, exit. Then the invariant: for each script, `git -C "$S" show "$P":scripts/<name> | shasum -a 256` must appear in `git -C "$S" show "$P":design/conventions.md`. A blob that §6 does not name is the session's defect: copy nothing, name the blob and both shas in the charter, exit.

Act 1, the re-sync, ONE commit, `make check` green at it. The three scripts byte-identical to the blobs at `P`. `HYGIENE_SHA` and `DOCLINT_SHA` move to §6's values at `P`, and a new `BOUNDED_SHA` joins them: the `hygiene` target's `printf ... \| shasum -a 256 -c` checks all three, its refusal line names `scripts/bounded` too, and the two Makefile comments that say "unpinned" or name two scripts say three, pinned by hash (§6). Pins and files move in the same commit, so `make hygiene` never reads red at a commit. One CHANGELOG bullet under `## Unreleased`: the re-sync to `P` (name the session commit by its short sha), `bounded` now pinned, and what S14 and S15 changed in the copied scripts, in one to three sentences read from the session's own commit subjects at `P` (`git -C "$S" log --oneline 2a1dfcb.."$P" -- scripts/`), nothing else of its history.

Act 2, only if the measurement finds something. Run the new hygiene, doclint and `bash tests/test_bounded.sh` on the branch. A hit gets an allow row inside §6's groups; a packet the new doclint refuses gets its place in GRANDFATHERED only by the session's copy (never edited here), so a refusal of a respeak packet is named in the charter for the session's next row, and the act commits nothing else. A bounded case that fails is read once against the old copy (`git show HEAD~1:scripts/bounded` to a temp path, `BOUNDED=<path>`); if the old copy passes, the case moves to the new copy's measured behavior, named in the charter. Measured at S14 (§4), none of these fire.

Later, for other rows, named in the charter: (a) the shared account-cells table is copied after the relay's ADV12-9 lands; until then `plugin/scripts/respeak-render.sh` keeps its own pattern and its per-phrasing tests; (b) the README's sentence "`scripts/hygiene` ... and `scripts/doclint` ... are byte-identical across them, pinned by hash" names two of the three; it stays true, so no README act this round; the next README round names `bounded`; (c) the session's Python suites for the three scripts stay the session's; this repo keeps `tests/test_bounded.sh`.

## 3. Interfaces (signatures, not prose)

- `make hygiene`: exits 2 with `hygiene: scripts/hygiene, scripts/doclint or scripts/bounded differ from the canonical copies (conventions section 6)` when any of the three differs from its pin; else runs `scripts/hygiene`, whose last line is `hits outside allowlist: N`.
- `make check`: `scripts/bounded --lock .check.lock --wall 840 --load 4 -- $(MAKE) check-unlocked`; exits 0, or 2 for any failure; unrun when a `bounded: stop: lock|load|wall` line is in stderr.
- Commits `r14 act N: <one line>`; the charter title `# Sitting <run day>-<n>: claude-code-respeak, r14-resync`.

## 4. Findings that name this row

Measured on `main` `0309058` under the virtualenv (3.12.7), the session's three scripts at `2a1dfcb` (S14) run from a temp copy: hygiene `hits outside allowlist: 0` (rc 0); doclint rc 0 over every packet and charter; `BOUNDED=<copy> bash tests/test_bounded.sh` `20 passed, 0 failed`. No tracked file here is over 60 KB, so ADV11-15's 4 MiB path cannot fire. S15's SPENT names only the relay's stems, none of this repo's. `make -n hygiene` names `scripts/bounded` nowhere today. S15 had not merged at this packet's commit: its shas are the builder's to measure at `P`.

## 5. Forbidden reads

Every other repo, beyond the four blobs and the one `git log` of the pin row and act 1. `~/.claude/`. `research/`; `examples/`. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's charter. `design/packets/` beyond this packet. The relay's ledgers; any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line's last output on the branch beside `main` at this packet's commit (`<h> <d> <b>`: the first 8 of §6's shas at `P`, written in the charter):

| line | main | branch |
|---|---|---|
| `grep -oE '^[A-Z]+_SHA = .{8}' Makefile \| paste -sd' ' -` | `HYGIENE_SHA = d63d0ffb DOCLINT_SHA = d5957c6c` | `HYGIENE_SHA = <h> DOCLINT_SHA = <d> BOUNDED_SHA = <b>` |
| `make -n hygiene 2>&1 \| grep -c scripts/bounded` | 0 | 1 |
| `make hygiene 2>&1 \| tail -1` | `hits outside allowlist: 0` | `hits outside allowlist: 0` |
| `make doclint 2>&1 \| grep -c ' 0 blocked, 0 errors'` | 1 | 1 |
| `bash tests/test_bounded.sh 2>&1 \| tail -1` | `20 passed, 0 failed` | `20 passed, 0 failed` |
| `sed -n '/^## Unreleased/,/^## 0/p' CHANGELOG.md \| grep -c '^- '` | 22 | 23 |
| `git status --short \| grep -c .` after the last commit | 0 | 0 |

Bullets: each act's commit and `P`; choices beyond §2 with reasons; what was left undone and for whom; at most ONE open fork. Last line: the branch and its head sha.
