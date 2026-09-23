# Packet R5: the post-S8 re-sync of the two canonical scripts in claude-code-respeak

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §5 (the plugin rule; `pluginlint` retired at the re-sync), §6 (the two sha256 pins), §9 (this packet's shape); the S8 charter's handover (its re-sync line); the owner's rulings of 2026-09-23 05:53 (no tag, no install before the final review pass); the R4 handover (`history/sittings/2026-09-22-7.md`). The builder reads THIS packet; §1 quotes the rest |
| pin | claude-code-respeak `main` at `bcaf292` (tag `v0.6.1`) or later. Branch `r5-resync`, worktree `.claude/worktrees/r5-resync` off it. The copy source is the session's `main` `27b22f9`, read as two blobs by `git -C ~/code/claude-code-session show 27b22f9:scripts/<name>` and nothing else there |
| wall | this repo. No other repo beyond the two blobs; no push; no `--amend`; no rebase; no device; no `make readme`; no tag; no version bump; no real `claude` beyond the `plugin validate` inside `make check` |
| may touch | edit: `scripts/hygiene`, `scripts/doclint`, `Makefile` (lines 25 and 26 only), `.hygiene-allow` (line 37 only), `CHANGELOG.md` (one heading, one bullet); new: the charter `history/sittings/<run day>-<n>.md`; `history/sessions/NEXT` (removed, never left). Nothing else |
| acceptance | the lines of §6 with their baselines; the gate reruns them on the branch |
| budget | 40 turns, 30k context; one commit for act 1, one for the charter; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

§5: doclint enforces "the plugin rule (commands under 31 lines with `description` and `allowed-tools`, agents with `name`, `description`, `model`, `tools`; the verb set is the plugin's own)"; "`pluginlint` is retired at each repo's next re-sync". §6: "Every copy of `scripts/hygiene` has sha256 `5c7408dd5dbfdb66e9470188ce5d2e587f2d7c794f4164efe3269f4a3aa2c1db`, of `scripts/doclint` `ca28e426d956ecbc14424b3ceea606cd0ee5d7ff03b307af7f681302a9120534`"; "Nothing is pushed red". S8's handover: "re-sync, for decisions, respeak, agent-relay: copy scripts/hygiene ... and scripts/doclint ...; pin the Makefile sha where one is pinned; ... the `person` allow rows under history/sittings/ (decisions, respeak) are now no-ops and can go"; "the second (README.md) line is optional, so this repo keeps one. Consumer: respeak, whose two lines now match §5". The new hygiene's docstring: "Under `history/sittings/` (charters are records) the `person` group is not evaluated; the other five groups still scan there." The owner, 2026-09-23: keep the GitHub marketplace; every install on this Mac and the tags wait for the final review pass. The standing word: decide inside the design, record the choice in the charter, escalate only a real fork.

## 2. Rulings

Act 1, ONE commit, four moves: `scripts/hygiene` and `scripts/doclint` become the pinned blobs, byte for byte; `HYGIENE_SHA` and `DOCLINT_SHA` become the §6 values; line 37 of `.hygiene-allow` loses `person`. They land together because the measurement says so: `make hygiene` reads red the moment the files change until the pins follow, and the OLD hygiene with the allow row narrowed is red on one charter (a `person` line in `history/sittings/2026-09-22-3b.md`), while the new one is green either way. The comment above the pins (Makefile lines 23 and 24) stays true and stays. Act 2: NOT cut. The session's doclint, run from this root against `main` `bcaf292`, exits 0: there is no `plugin/commands/`, and `plugin/agents/respeak.md` carries the four keys. The builder re-measures with `make doclint` after the copy; a hit there is a finding for the report, fixed only in a file `may touch` names, else named for the owner. `CHANGELOG.md`: `v0.6.1` is tagged, so its entry cannot grow, and the owner ruled no bump: a `## Unreleased` heading goes above `## 0.6.1` with one bullet in the entry's shape (it names the failure: the pins lagged the canonical copies). Whoever cuts the next version renames the heading. The file is human-lane: the bullet is written once in technical mode, the gate scans the write, and the editorial pass `CLAUDE.md` names is the builder's call. The sidecar (two lines; §5 admits the second) and `scripts/readme-fresh.sh` (writes two, checks both): checked by the acceptance lines, not changed. `make readme` never: the README source, the docs and `CLAUDE.md` name no sha and no `pluginlint` (measured). `python3` is the pyenv virtualenv `.python-version` declares, never Apple's. No sibling path enters a tracked file beyond the session repo's name; no person; no home path in the charter (after act 1 its allow row is `sibling,private`).

## 3. Interfaces (signatures, not prose)

- The copy, from the repo root; the two shas it prints are the §6 values:

```sh
for f in hygiene doclint; do git -C ~/code/claude-code-session show 27b22f9:scripts/$f > scripts/$f; done
shasum -a 256 scripts/hygiene scripts/doclint
```

- `Makefile` lines 25 and 26, exactly:

```
HYGIENE_SHA = 5c7408dd5dbfdb66e9470188ce5d2e587f2d7c794f4164efe3269f4a3aa2c1db
DOCLINT_SHA = ca28e426d956ecbc14424b3ceea606cd0ee5d7ff03b307af7f681302a9120534
```

- `.hygiene-allow` line 37, exactly: `history/sittings/*.md: sibling,private`
- `CHANGELOG.md`: after the intro line, `## Unreleased`, a blank line, one bullet: the two scripts re-synced to the canonical copies (conventions section 6) with the pins moved in the same commit; what changed in them (charters no longer scanned for a person; doclint checks a plugin's agents and commands); the failure (the pins lagged, so `make hygiene` read red between the copy and the pin).
- The commit message of act 1: `r5 act 1: re-sync scripts/hygiene and scripts/doclint to the canonical copies; pins and the sittings allow row move with them`.
- The charter: `# Sitting <run day>-<n>: claude-code-respeak, r5-resync`, the five rows, `## Done-ness`, `## Handover`, `## Next act`, under 4,096 bytes.

## 4. Findings that name this row

On `main` `bcaf292` plus this packet, its rows file and its charter, under pyenv 3.12.7: `make check` 0 in 52 s; 218 unit tests, 8 bash suites, 202 checks. `scripts/hygiene` is `fb05f620`, `scripts/doclint` `b46db3df`; the pins match them. The pinned blobs at the session's `27b22f9` hash to the §6 values, and that tree is clean. The new hygiene differs from the old by four lines (`RECORDS`, the skip, the docstring); the new doclint by the plugin rule (`frontmatter`, `check_plugin`, three constants) and the size docstring. On this tree the new hygiene prints `person 16 8` with either allow file, hits 0; the old prints `person 17 9`, and 1 hit with the row narrowed. The new doclint exits 0 here. `git grep` for the four shas and `pluginlint` hits `Makefile` only. The sidecar holds two lines and checks; `readme: fresh`. Tags `v0.5.0` to `v0.6.1`; `CHANGELOG.md` has no `## Unreleased`. The new doclint is 8,509 bytes, the new hygiene 6,333.

## 5. Forbidden reads

Every repo but this one, except the two blobs by `git show`. `~/.claude/`. `research/`. `examples/`. `README.md`. `design/readme/source.md`. The docs. `CHANGELOG.md` beyond its first 30 lines. `history/` beyond the builder's own charter. The relay's ledgers. The brief. Any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line, its exit and last output on the branch, beside `main` at this packet's commit (`bcaf292` plus three files) under pyenv 3.12.7:

| line | main | branch |
|---|---|---|
| `make check >/dev/null 2>&1; echo $?` | 0 | 0 |
| `shasum -a 256 scripts/hygiene scripts/doclint \| cut -c1-8 \| tr '\n' ' '` | `fb05f620 b46db3df` | `5c7408dd ca28e426` |
| `for f in hygiene doclint; do git -C ~/code/claude-code-session show 27b22f9:scripts/$f \| cmp -s - scripts/$f; printf '%s ' $?; done` | `1 1` | `0 0` |
| `grep -oE '^(HYGIENE\|DOCLINT)_SHA = [0-9a-f]{8}' Makefile \| tr '\n' ' '` | `HYGIENE_SHA = fb05f620 DOCLINT_SHA = b46db3df` | `HYGIENE_SHA = 5c7408dd DOCLINT_SHA = ca28e426` |
| `make hygiene >/dev/null 2>&1; echo $?` | 0 | 0 |
| `grep -cE '^history/sittings/\*\.md: sibling,private$' .hygiene-allow` | 0 | 1 |
| `python3 scripts/hygiene \| grep -E '^person' \| tr -s ' '` | `person 17 9` | `person 16 8` |
| `python3 scripts/doclint; echo $?` | 0 | 0 |
| `make test 2>&1 \| grep -E '^Ran [0-9]+ tests' \| cut -d' ' -f1-3` | `Ran 218 tests` | `Ran 218 tests` |
| `make test 2>&1 \| grep -c ' passed, 0 failed'` | 8 | 8 |
| `wc -l < design/readme/rendered.sha256 \| tr -d ' '; bash scripts/readme-fresh.sh` | `2`, `readme: fresh` | `2`, `readme: fresh` |
| `grep -c '^## Unreleased' CHANGELOG.md` | 0 | 1 |
| `git diff --name-only main..HEAD \| grep -vc '^history/'` | 0 | 5 |
| `git status --short \| wc -l \| tr -d ' '` after the last commit | 0 | 0 |

Bullets: act 1's commit, one line; `make doclint` after the copy (0, or the hit and where it went); the choices made inside the design beyond §2, with their reason; what was left undone and for whom; at most ONE open fork for the owner. Last line: the branch and its head sha.
