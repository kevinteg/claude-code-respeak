---
status: current
updated: 2026-09-28
owner: kevin
audience: kevin, agent
---
# claude-code-respeak: what is left open, none of it blocking

Nothing here blocks a review or a merge. An item leaves when it lands, or when a decision retires it.

- SessionStart hook with no off key: the hook runs in every repo that has a `.claude/respeak/` directory, and no config key turns it off (`plugin/scripts/lexicon-status.sh:31`), while the cross-repo ledger wants every hook off unless a repo turns it on. Since 2026-09-28 six repos carry a config, so the hook fires in all six until a key gates it; drop the hook, or gate it behind a key that is off by default.
