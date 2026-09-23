---
name: report
description: >
  File a bug report, feature request, documentation note, or question on
  GitHub. Privacy by default: your text plus an environment footer; project
  content only if you opt in. User-invoked only.
disable-model-invocation: true
argument-hint: "[bug|enhancement|documentation|question] [\"title\"] [--include-content]"
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/report-env.sh *) Bash(gh auth status*) Bash(gh issue create *)
---

# respeak — report an issue upstream

Issue target and environment (detected by the plugin, never from your
project):

!`"${CLAUDE_PLUGIN_ROOT}/scripts/report-env.sh"`

Arguments: `$ARGUMENTS` may carry a kind (the first word, when it is one of
`bug`, `enhancement`, `documentation`, `question`), a quoted title, and the
flag `--include-content` anywhere. Anything supplied is not asked again.

Steps:

1. **Resolve the target.** Use `owner_repo` from the JSON above as the
   `--repo` argument for `gh`. If it is `null`, stop with:
   "The plugin manifest has no parseable `repository` field, so there is no
   issue tracker to target."
2. **Check the GitHub CLI.** Run `gh auth status`. Three branches:
   - Installed and authenticated: continue.
   - Installed, not authenticated: say so, show `gh auth login`, and keep
     gathering; at step 7 print the body for pasting instead of posting.
   - Not installed: show `brew install gh && gh auth login` (macOS) or the
     platform equivalent; same paste fallback at step 7.
3. **Open with one line:** "Report a bug, request a feature, or ask a
   question. Anything about respeak goes."
4. **Gather three fields**, one at a time, skipping any already supplied:
   the kind (`bug | enhancement | documentation | question`), a one-line
   title, and the body. For a bug ask what happened, what was expected, and
   how to reproduce it; for the other kinds, what is wanted and why. Take
   the user's words as written. Do not restyle them.
5. **Build the footer** with
   `"${CLAUDE_PLUGIN_ROOT}/scripts/report-env.sh" --footer` and append it
   to the body. A fact the script could not detect reads `unknown`; never
   block on it.
6. **Privacy guard, opt-in only.** Only when `--include-content` was given,
   or the user says mid-flow to attach a named file or block:
   1. Attach one named path or block at a time. Never offer an
      "everything" toggle, and never scan for candidates.
   2. Read only that path. Show the full text that would be appended.
   3. Ask: "This will be posted publicly to <owner_repo>. Anyone on the
      internet can read it. Confirm? [y/N]"
   4. On yes, append it inside `<details><summary>Attached content</summary>`
      so it is searchable without dominating the issue. On no, drop it.
7. **Privacy pass, every time.** Before showing the body, read it once for
   details that identify a person, an organization, or a machine, or that
   are privileged: personal names, email addresses, usernames, hostnames,
   IP addresses, internal URLs, file paths under a home directory, company,
   client or customer names, ticket or account identifiers, and anything
   that looks like a token, key, or password. Replace each with a neutral
   placeholder such as `<name>`, `<host>`, `<path>`, `<org>`, and prefer
   `~/...` over an absolute home path. Never redact the substance of the
   report, only what identifies. Then tell the user what changed, or that
   nothing needed to, in one line, and ask: "Confirm the body contains
   nothing privileged or sensitive and is ready to be public? [y/N]" A
   yes is required to continue; a no returns to the previous step.
8. **Show the final body** (kind and title as the heading, then the body,
   footer, and any attachment) and ask "Post? [y/N]". On no, ask what to
   change: title, body, attachments, or cancel. If `gh` is missing or not
   authenticated, print instead: "gh is not configured. Paste this into
   <owner_repo>'s issue tracker:" followed by the full body, and stop. No
   draft is written on that path.
9. **Post.** Feed the body on stdin so quoting never mangles it:

   ```sh
   gh issue create --repo <owner_repo> --title "<title>" --label <kind> --body-file - <<'RESPEAK_EOF'
   <body, footer, attachment>
   RESPEAK_EOF
   ```

   If `gh` rejects the label (a fork without the default labels), retry
   once without `--label`. On success report
   "Filed #<number> against <owner_repo>: <title>" and the URL.
   On any other failure (network, expired auth, rate limit) write the body
   to `.claude/respeak/drafts/report-<YYYY-MM-DDTHHMMSS>.md` in the current
   project, creating the directory if needed, and show the error, the draft
   path, and the retry:
   `gh issue create --repo <owner_repo> --title "<title>" --label <kind> --body-file <path>`

Guardrails:

- **Nothing from the project is included by default.** Not the document
  being gated or translated, not a measure or gate report (it quotes the
  user's prose), not `.claude/respeak/` or `~/.claude/respeak/` config, not
  the lexicon or proposals, not the transcript. The default body is the
  user's text plus the footer.
- **Read no file** outside the plugin directory except a path the user
  named and confirmed in step 6.
- **Write nothing** except a draft after a failed post. A cancelled report
  is dropped, not saved.
- **Identifying detail is replaced, not posted.** The privacy pass in step
  7 runs on every report, attachment or not, and its confirmation is not
  optional. Keep the wording neutral: no employer, client, or colleague
  names, even when the user typed them.
- **Never fire from conversation.** This skill runs only when invoked as
  `/respeak:report`. When a user complains about respeak in chat, name the
  command once and continue; do not start the flow.
