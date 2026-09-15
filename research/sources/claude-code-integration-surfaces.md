# Claude Code extension surfaces: what respeak builds on

*Research notes, 2026-08-31, verified against code.claude.com; rewritten as an educational primer 2026-09-15.*

Claude Code's documentation now lives at code.claude.com; old docs.claude.com links redirect there. Claude Code exposes eight distinct extension points. respeak, a two-lane communication plugin, uses them for one reason: the swarm's shorthand stays in the model's context, and the human reader still gets prose.

## Subagents

A custom subagent is a Markdown file with YAML frontmatter; its body is the system prompt. It gets that prompt plus basic environment details, not the full Claude Code system prompt. It still loads project memory files; only the built-in Explore and Plan agents skip that. `name` and `description` are the only required fields. `tools`, `model`, `permissionMode`, and `skills` are optional; `skills` preloads full skill content at startup. A subagent runs by automatic delegation, by direct mention, or as the whole session's agent, replacing its system prompt entirely.

respeak runs its translator as a plugin subagent. That isolates long swarm transcripts from the main window, narrows the tool list, and allows a cheaper model than the main session's. One limit: plugin subagents cannot carry `hooks`, `mcpServers`, or `permissionMode` in frontmatter. Those guarantees live in the prompt itself, or in hooks at the plugin level.

## Skills

Skills are the current, unified mechanism behind slash commands. A skill lives at `SKILL.md`; most of its frontmatter is optional. A plugin's skill is invoked as `/plugin-name:skill-name`, and the bare `/name` form works too, unless another command already claims it. Frontmatter sets whether a skill answers to a typed command, model judgment, or both. Its `description` stays in context for the model to judge; the full body loads only on invocation and persists across turns. A skill body can embed a shell command that runs at invocation and inlines its output into the prompt.

respeak needs one skill for two things: a typed translate command, and a natural-language trigger such as "explain this to my manager." One skill handles both, since either path can invoke it. The shell-execution feature lets it read the live configuration file, or the current lexicon version, at the moment it runs.

## Hooks

Hooks run code at defined points: session start, before or after a tool call, when a subagent stops, and when text is about to display. Over a dozen other events exist too. A handler can be a shell command, an HTTP call, an MCP tool call, or a prompt a model evaluates. Input for the `Stop` event includes the assistant's final message text directly, so a hook need not parse the transcript file. Hooks can inject additional context into the session as a system reminder, or block a turn from ending until a condition is met.

A `Stop` hook is how respeak nudges a narrative at a milestone. It reads the final response and, when the layered configuration turns the feature on, asks Claude to append one rendered paragraph before the turn ends. One event matters most for this plugin: `MessageDisplay` can replace the text shown on screen, while the transcript and model context keep the original. The swarm keeps its shorthand; the person watching sees prose instead.

## Plugins and marketplaces

A plugin bundles some combination of skills, subagents, hooks, an MCP server, and other components under one manifest, `.claude-plugin/plugin.json`. Only `name` is required; optional fields include `displayName`, `version`, `author`, `repository`, `license`, and `userConfig`, which declares settings a user fills in at enable time. Plugins install from marketplaces: git repositories, URLs, or local paths listing installable plugins. `claude plugin marketplace add <source>` registers one; `claude plugin install name@marketplace` installs from it. `claude plugin inspect` reports a plugin's component inventory, plus the token cost it projects for every session.

respeak ships as one plugin, so its skill, subagent, and hooks install and update together. The `userConfig` block is where a person sets defaults, such as the rendering mode or the audience's tech level, without hand-editing a YAML file. Running `claude plugin inspect` keeps its passive token footprint measured, not assumed.

## Statusline

A statusline is a script Claude Code runs after most assistant messages, and on a debounce timer, set with the `statusLine` settings key. It reads a JSON payload on standard input describing the session: model, `cost.total_cost_usd`, `context_window.used_percentage`, `output_style.name`, and more. It prints plain or ANSI-colored lines to standard output. None of this costs model tokens, since it runs locally.

A statusline script can show respeak's active mode, its lexicon version, and a count of pending shorthand proposals. It reads those from the plugin's own configuration and proposal files. A plugin cannot install a `statusLine` setting on its own; that step has to be an explicit action a skill offers to perform.

## Memory and CLAUDE.md

`CLAUDE.md` files load at the start of every session, broad to specific: a machine-wide policy file first, then a personal file, then project-level files. This content loads as context, not enforced configuration. One file can import another with the documented `@path/to/file` syntax, expanded when the session starts. Claude Code also writes its own short auto-memory file per project. Separate rule files follow the same load order, but can be scoped to load only when a matching file path is touched.

The import syntax is the cleanest way to keep a ratified shorthand lexicon in every session's context. A project's `CLAUDE.md` can carry one import line pointing at a short lexicon digest. Any session working there, swarm workers included, then loads the current terms without duplicating them. A plugin cannot ship `CLAUDE.md` content directly, so this needs the project owner's consent, through a skill that offers to write that line.

## Headless print mode

Running Claude Code non-interactively with `-p` produces scripted output in text or JSON. Flags cover a custom system prompt, continuing a prior session, and exit codes suited to automation. A stricter `--bare` flag skips all automatic discovery: hooks, skills, plugins, `CLAUDE.md`, and MCP. It reads no stored login session, so it needs an API key. The documentation calls bare mode "the recommended mode for scripted and SDK calls." It says bare mode will become the default for `-p` in a future release. It still accepts an explicit plugin directory, agent definitions, a settings file, and an MCP configuration on the command line.

A hook can shell out to a bare, headless call running only respeak's translator subagent, deterministic and isolated from whatever the calling session has configured. The cost is a separate billed call, and added latency, against an in-session subagent that shares the main call.

## MCP

The Model Context Protocol lets Claude Code connect to external servers that expose tools and resources over one standard interface. A plugin can bundle its own server configuration through an `.mcp.json` file or an `mcpServers` manifest key. Any tool an MCP server exposes adds its schema to the model's context for the whole session, whether or not that tool is ever called.

An MCP server could expose translate and lexicon-lookup tools to any MCP-compatible client, not only Claude Code sessions. A subagent already gives respeak's translator an isolated context and a free choice of model. MCP earns its added cost mainly if respeak needs to serve callers outside Claude Code entirely.

## Sources

- https://code.claude.com/docs/llms.txt
- https://code.claude.com/docs/en/overview.md
- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/skills.md
- https://code.claude.com/docs/en/commands.md
- https://code.claude.com/docs/en/hooks.md
- https://code.claude.com/docs/en/hooks-guide.md
- https://code.claude.com/docs/en/plugins.md
- https://code.claude.com/docs/en/plugins-reference.md
- https://code.claude.com/docs/en/plugin-marketplaces.md
- https://code.claude.com/docs/en/output-styles.md
- https://code.claude.com/docs/en/settings.md
- https://code.claude.com/docs/en/settings-reference.md
- https://code.claude.com/docs/en/statusline.md
- https://code.claude.com/docs/en/memory.md
- https://code.claude.com/docs/en/headless.md
- https://code.claude.com/docs/en/agent-sdk/overview.md
- https://code.claude.com/docs/en/mcp.md
- https://code.claude.com/docs/en/features-overview.md
- https://code.claude.com/docs/en/claude-directory.md
