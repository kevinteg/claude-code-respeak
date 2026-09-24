# Packet R6: the post-S9 re-sync of the two canonical scripts, and the five skill descriptions

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §1 (the SKILL.md limits), §5 (the plugin rule), §6 (the sha256 pins), §9 (this shape); the S9 charter's handover; the owner's rulings of 2026-09-23 05:53 (no tag, no install before the final review pass). The builder reads THIS packet; §1 quotes the rest |
| pin | claude-code-respeak `main` at `d9f4802` (after tag `v0.6.1`) or later. Branch `r6-resync`, worktree `.claude/worktrees/r6-resync` off it. The copy source is claude-code-session `main` `c7dbdee`, the checkout beside this repo's (§3 names it), two blobs by `git show`, nothing else there |
| wall | this repo. No other repo beyond the two blobs; no push; no `--amend`; no rebase; no device; no `make readme`; no tag; no version bump; no real `claude` beyond the `plugin validate` inside `make check` |
| may touch | edit: `scripts/hygiene`, `scripts/doclint`, `Makefile` (lines 25 and 26 only), `.hygiene-allow` (line 37 only), `plugin/skills/init/SKILL.md`, `plugin/skills/off/SKILL.md`, `plugin/skills/on/SKILL.md`, `plugin/skills/report/SKILL.md`, `plugin/skills/respeak/SKILL.md` (each: the `description` value only), `CHANGELOG.md` (one bullet under `## Unreleased`); new: the charter `history/sittings/<run day>-<n>.md`; `history/sessions/NEXT` (removed, never left). Nothing else |
| acceptance | the lines of §6 with their baselines |
| verify | `make check` |
| budget | 40 turns, 30k context; one commit per act, one for the charter, whose open names doclint's five rows (goal, budget, pin, window, agents); checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

§1: "frontmatter: name, description under 200 chars, allowed-tools; body under 500 lines". §5: doclint enforces "the plugin rule (... the SKILL.md limits of §1 ...)". §6: "`scripts/hygiene` scans the working tree ... (under `history/sittings/` the `person` and `sibling` groups are not evaluated)"; "Every copy of `scripts/hygiene` has sha256 `d9e99149ec88c943c871795a2d0638a40dd344d0f5a4cac19be8fc02b86f9aa0`, of `scripts/doclint` `4318bc912b4fd57ad111f037dab13f11fb137255515a23f215f2a59c10b1e81a`"; "Nothing is pushed red". S9's handover: "the respeak re-sync row (its five descriptions, 206 to 333 chars, go under 200)"; "drop `sibling`, `person` from the sittings allow row". The new doclint: a `>` or `|` block is "joined by spaces"; it refuses at 201 chars. The standing word: decide inside the design, record the choice, escalate only a real fork.

## 2. Rulings

Act 1, ONE commit, four moves: `scripts/hygiene` and `scripts/doclint` become the pinned blobs, byte for byte; `HYGIENE_SHA` and `DOCLINT_SHA` become the §6 values; line 37 of `.hygiene-allow` loses `sibling` (it carries no `person`; `private` stays, it still scans there). Together, measured: `make hygiene` is red between the copy and the pin; the OLD hygiene with the row narrowed is red on 47 `sibling` lines in ten charters, the new one green either way. Act 2, its own commit: the new doclint, run from this root, refuses five files and only those; each skill's `description` block goes to at most 200 chars joined, keeping the words of §3, in the same `>` block shape, every other key and the body untouched. Four skills are `disable-model-invocation: true`, so their description is the menu line a person reads; `respeak` is model-invoked, so its quoted asks are the trigger and survive; `plugin/agents/respeak.md` keeps the full ask list (agents have no ceiling; measured). `CHANGELOG.md`: `## Unreleased` holds R5's bullet; ONE more follows it, in the entry's shape, naming the failure (five descriptions ran 206 to 333 chars against the 200 ceiling that arrived with the doclint); human-lane, written once in technical mode, the gate scans the write; no separate editorial pass for one bullet (R5's choice, kept). No test, doc or README names a description's text (measured), so nothing else moves; `make readme` never. `python3` is the pyenv 3.12 virtualenv, never Apple's. No sibling path enters a tracked file beyond the session repo's name; no person; no home path.

## 3. Interfaces (signatures, not prose)

- The copy, from the worktree root; the shas it prints are the §6 values:

```sh
S="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/../claude-code-session"
for f in hygiene doclint; do git -C "$S" show c7dbdee:scripts/$f > scripts/$f; done
shasum -a 256 scripts/hygiene scripts/doclint
```

- `Makefile` lines 25 and 26, exactly:

```
HYGIENE_SHA = d9e99149ec88c943c871795a2d0638a40dd344d0f5a4cac19be8fc02b86f9aa0
DOCLINT_SHA = 4318bc912b4fd57ad111f037dab13f11fb137255515a23f215f2a59c10b1e81a
```

- `.hygiene-allow` line 37, exactly: `history/sittings/*.md: private`
- The five descriptions, at most 200 chars each once the block's lines are joined by single spaces; the words that survive, verbatim, each on one line: `init` (297): "Set up respeak", "with consent", "CLAUDE.md import", "gitignore", "statusline", "User-invoked only". `off` (333): "Silence the respeak hooks for this session only", "`gate`", "style gate", "/respeak:on", "User-invoked only". `on` (206): "Undo /respeak:off for this session", "`gate`", "as a trial", "User-invoked only". `report` (316): "bug report", "feature request", "question", "GitHub", "Privacy by default", "opt in", "User-invoked only". `respeak` (274): "Translate agent/swarm output into a human-facing narrative", "/respeak:respeak [mode] [source]", and at least three quoted asks, among them "explain that to my manager", "give me the ELI5", "make this readable".
- After act 2, from the root: `python3 scripts/doclint` prints nothing and exits 0.
- Commit messages: act 1 `r6 act 1: re-sync scripts/hygiene and scripts/doclint to the S9 copies; pins and the sittings allow row move with them`; act 2 `r6 act 2: the five skill descriptions under 200 chars`.
- The charter: `# Sitting <run day>-<n>: claude-code-respeak, r6-resync`, the five rows, `## Done-ness`, `## Handover`, `## Next act`, under 4,096 bytes.

## 4. Findings that name this row

On `main` `d9f4802` plus this packet, its rows file and its charter, under pyenv 3.12.7: `make check` 0 in 52 s; 218 unit tests, 8 bash suites. `scripts/hygiene` is `5c7408dd`, `scripts/doclint` `ca28e426`; the pins match. The new hygiene is 6,667 bytes, the new doclint 10,339. The new doclint from this root exits 2 with exactly five lines, `plugin: description N chars, ceiling 200`, N = 297, 333, 206, 316, 274 for init, off, on, report, respeak; no charter, packet, link or NEXT finding. The new hygiene prints `sibling 1296 84`, hits 0, with the current allow file and with line 37 narrowed; the old one with the row narrowed prints 47 hits. Every skill body is under 110 lines. `init`'s "User-invoked only" wraps across two block lines, so a plain `grep` misses it; §6 joins first.

## 5. Forbidden reads

Every repo but this one, except the two blobs by `git show`. `~/.claude/`. `research/`. `examples/`. `README.md`. `design/readme/source.md`. The docs. `CHANGELOG.md` beyond its first 30 lines. `history/` beyond the builder's own charter. The relay's ledgers. Any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line, its exit and last output on the branch, beside `main` at this packet's commit (`d9f4802` plus three files) under pyenv 3.12.7:

| line | main | branch |
|---|---|---|
| `make check >/dev/null 2>&1; echo $?` | 0 | 0 |
| `shasum -a 256 scripts/hygiene scripts/doclint \| cut -c1-8 \| tr '\n' ' '` | `5c7408dd ca28e426` | `d9e99149 4318bc91` |
| `grep -oE '^(HYGIENE\|DOCLINT)_SHA = [0-9a-f]{8}' Makefile \| tr '\n' ' '` | `HYGIENE_SHA = 5c7408dd DOCLINT_SHA = ca28e426` | `HYGIENE_SHA = d9e99149 DOCLINT_SHA = 4318bc91` |
| `make hygiene >/dev/null 2>&1; echo $?` | 0 | 0 |
| `sed -n 37p .hygiene-allow` | `history/sittings/*.md: sibling,private` | `history/sittings/*.md: private` |
| `python3 scripts/doclint; echo $?` | 0 | 0 |
| `for s in init off on report respeak; do awk '/^description: >/{f=1;next} f&&/^  /{sub(/^ +/,"");d=(d==""?$0:d" "$0);next} {f=0} END{print length(d)}' plugin/skills/$s/SKILL.md; done \| tr '\n' ' '` | `297 333 206 316 274 ` | five numbers, each at most 200 |
| `for s in init off on report respeak; do awk '/^description: >/{f=1;next} f&&/^  /{sub(/^ +/,"");d=(d==""?$0:d" "$0);next} {f=0} END{print d}' plugin/skills/$s/SKILL.md; done \| grep -cE 'User-invoked only\|explain that to my manager'` | 5 | 5 |
| `make test 2>&1 \| grep -E '^Ran [0-9]+ tests' \| cut -d' ' -f1-3` | `Ran 218 tests` | `Ran 218 tests` |
| `awk '/^## Unreleased/{f=1;next} /^## /{f=0} f&&/^- /{n++} END{print n}' CHANGELOG.md` | 1 | 2 |
| `git diff --name-only main..HEAD \| grep -vc '^history/'` | 0 | 10 |
| `git status --short \| wc -l \| tr -d ' '` after the last commit | 0 | 0 |

Bullets: act 1's commit, one line; act 2's commit and the five counts; the choices made inside the design beyond §2, with their reason; what was left undone and for whom; at most ONE open fork for the owner. Last line: the branch and its head sha.
