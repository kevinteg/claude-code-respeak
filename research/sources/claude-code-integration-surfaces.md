# Claude Code Extension Surfaces for the respeak Translator
Research date: 2026-08-31. All claims verified against docs.claude.com pages fetched during this session (URLs in Sources).

## 0. Docs location has moved (important)

`docs.claude.com/en/docs/claude-code/*` now 301-redirects to **`https://code.claude.com/docs/en/*`** (verified: overview → `https://code.claude.com/docs/en/overview`, HTTP 200). The complete page index is at `https://code.claude.com/docs/llms.txt`, and every page renders as Markdown with a `.md` suffix. The old `docs.claude.com/llms.txt` covers the platform API docs (platform.claude.com), not Claude Code. Cite code.claude.com URLs going forward.

## 1. Custom subagents (`.claude/agents/*.md`, plugin `agents/`)

Source: https://code.claude.com/docs/en/sub-agents.md

**Status: current, actively developed.** Markdown files with YAML frontmatter; body = the subagent's system prompt. Subagents get *only* that system prompt + basic environment details (cwd), not the full Claude Code system prompt; custom subagents DO load CLAUDE.md (only built-in Explore/Plan skip it).

**Scope/priority order** (same `name` → higher wins): 1 managed settings, 2 `--agents` CLI flag (JSON), 3 project `.claude/agents/`, 4 user `~/.claude/agents/`, 5 **plugin `agents/` dir (lowest)**. So a project-level `respeak` agent would shadow the plugin's.

**Frontmatter fields** (only `name` + `description` required):
- `name` — lowercase+hyphens; no `:` (reserved for plugin-scoped IDs like `my-plugin:reviewer`); hooks receive it as `agent_type`.
- `description` — the delegation trigger. Claude auto-delegates by matching task against this; docs: "include phrases like 'use proactively'" to encourage delegation. Combined descriptions of all custom subagents warn at >15,000 tokens — keep description short, put detail in the body.
- `tools` (allowlist; inherits all subagent-available tools if omitted), `disallowedTools` (denylist).
- `model` — `sonnet|opus|haiku|fable`, full ID, or `inherit`. Resolution order: per-invocation param → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → main model.
- `permissionMode` — `default|acceptEdits|auto|dontAsk|bypassPermissions|plan|manual`. **Ignored for plugin subagents.**
- `maxTurns`, `skills` (preloads FULL skill content into subagent context at startup), `mcpServers` (**ignored for plugin subagents**), `hooks` (per-subagent lifecycle hooks; **ignored for plugin subagents**), `memory` (`user|project|local` — persistent cross-session memory), `background: true`, `effort` (`low..max`), `isolation: worktree`, `color`, `initialPrompt` (auto-submitted first turn when agent runs as MAIN session agent via `--agent`), `experimental.cacheTtl`.

**Invocation paths relevant to respeak:**
- Automatic delegation from `description` match.
- Natural language ("use the respeak subagent…").
- `@`-mention: `@agent-respeak` or plugin-scoped `@agent-respeak:respeak` — guarantees that subagent runs for one task.
- Whole session as agent: `claude --agent respeak` or `"agent": "respeak"` in settings — subagent's prompt REPLACES the Claude Code system prompt (CLAUDE.md still loads). Plugin agents work: `claude --agent my-plugin:name`.
- Subagents can be resumed / sent follow-up messages; `maxTurns` overruns return partial output.

**Notes:** `/agents` interactive wizard removed as of v2.1.198 (prints reminder to edit files directly). Agent dirs are file-watched (changes picked up in seconds; first file in a new dir needs restart). Background subagents keep a reduced built-in tool set (Read/Grep/Glob/Bash/Edit/Write/WebFetch/WebSearch/Skill/… survive). Validate with `claude plugin validate .claude/agents`.

**respeak fit:** the translator as a plugin `agents/respeak.md` subagent is correct: isolated context (long swarm transcripts don't pollute the main window), read-mostly tool list, cheaper/faster model via `model: haiku` or `sonnet`, and `skills:` preload of the rendering skill. Caveats: plugin subagents can't carry `hooks`/`permissionMode`/`mcpServers` frontmatter — put behavioral guarantees in the prompt or hooks at plugin level.

## 2. Skills (SKILL.md) — now the unified command/skill system

Sources: https://code.claude.com/docs/en/skills.md, https://code.claude.com/docs/en/commands.md

**Status: current; skills have absorbed slash commands.** The commands doc says "To add your own commands, see skills." `.claude/commands/*.md` files still work, but when a skill and command share a name, the skill wins. A plugin's `commands/` dir is documented as "Skills as flat Markdown files. **Use `skills/` for new plugins**" (plugins-reference). Bundled Claude commands like `/code-review` are themselves skills now.

**Locations & namespacing:** `~/.claude/skills/<name>/SKILL.md` (personal), `.claude/skills/<name>/SKILL.md` (project), plugin `skills/<name>/SKILL.md` → invoked as `/plugin-name:skill-name` (e.g. `/respeak:respeak`); the bare `/name` also works "unless another command already uses that name". Plugin-root `SKILL.md` also allowed. Enterprise > personal > project on name conflicts; plugin skills can't conflict (namespaced).

**Frontmatter (all optional; `description` recommended):** `name` (display; for plugin skills sets command's last segment), `description` (+`when_to_use`, combined cap 1,536 chars in listing), `argument-hint`, `arguments` (named positional args for `$name` substitution), `disable-model-invocation` (user-only; description NOT in context, so zero passive cost), `user-invocable: false` (model-only; description always in context), `allowed-tools` (per-turn permission pre-grant), `disallowed-tools`, `model` (per-turn override — e.g. force Sonnet for translation quality), `effort`, `context: fork` (+ `agent`, `background`) to run the skill in a subagent, `hooks` (registered on invocation, persist rest of session; `once` option), `paths` (glob-gated auto-loading), `shell`, `metadata`, `license`, `compatibility`.

**Invocation matrix:** default = both user (`/name`) and model can invoke; description always sits in context (~cheap), full content loads on invocation and PERSISTS across turns (re-attached after compaction, first 5,000 tokens, shared 25k budget).

**String substitutions in body:** `$ARGUMENTS`, `$0`/`$1`/`$ARGUMENTS[N]`, `$name`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}` (plugin skills only), `${CLAUDE_PLUGIN_DATA}` (persistent data dir surviving plugin updates — good home for the ratified lexicon cache). **Dynamic context injection**: `` !`command` `` blocks execute shell at invocation time and inline the output — a respeak skill can inject the current lexicon version, config mode, or latest transcript slice at invocation.

**`context: fork`:** skill content becomes the prompt of a fresh subagent (`agent:` picks the type); no conversation history. Runs background by default (narrower toolset); `background: false` to block and keep full tools. In `-p`/SDK mode, forked skills always block.

**respeak fit:** a single plugin skill `/respeak:translate` (user-invocable, args `[mode] [source]`) can REPLACE both the current `commands/respeak.md` and the model-trigger skill; use dynamic `!`cat config/respeak.config.yaml`` injection; keep a second model-only skill (`user-invocable: false`) whose description carries the natural-language triggers ("explain to my manager", "make this readable").

## 3. Hooks

Sources: https://code.claude.com/docs/en/hooks.md (reference), https://code.claude.com/docs/en/hooks-guide.md

**Status: current; the event list is far larger than the classic eight.** Full list (verified): `SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `PreModelSwitch`, `PostModelSwitch`, `Elicitation`, `ElicitationResult`, `SessionEnd`.

**Five handler types** (not just shell commands): `command`, `http` (POST JSON to URL), `mcp_tool`, `prompt` (single-turn LLM evaluation, `$ARGUMENTS` = hook input JSON, defaults to a fast model), and `agent` (experimental: spawns a subagent with Read/Grep/Glob to verify conditions). Common fields: `if` (permission-rule filter, tool events only), `timeout`, `statusMessage` (custom spinner text), `once` (skill-frontmatter hooks only), `async`/`asyncRewake` (command hooks in background; exit 2 wakes Claude with a system reminder).

**Hook locations:** `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed policy, **plugin `hooks/hooks.json`**, **skill frontmatter** (registered at invocation, persist rest of session, `once` supported), **subagent frontmatter** (active only while that subagent runs; a `Stop` hook there is converted to `SubagentStop`). Hook entries merge across levels. Settings/plugin hooks also fire inside subagents, with `agent_id`/`agent_type` in the input.

**Answers to the two respeak questions:**
- *Can a Stop hook auto-translate a turn's final output?* Yes, three ways. (a) Stop input includes **`last_assistant_message`** — the full text of Claude's final response (docs explicitly recommend it over parsing `transcript_path`) plus `stop_hook_active`, `background_tasks`, `session_crons`; a command hook can pipe it to `claude -p --agent respeak` or an SDK service and write/display a rendered narrative. (b) Stop supports `decision: "block"` + `reason` (forces Claude to continue — usable to demand "now render a BLUF summary"; capped at 8 consecutive blocks) and `hookSpecificOutput.additionalContext` (non-error feedback the model acts on). (c) **`MessageDisplay`** hook can return `displayContent` that **replaces the displayed text on screen while the transcript and model context keep the original** — this is the purest "translate for the human without fighting the optimization" surface: swarm shorthand stays in context, the human sees the translation. (10s default timeout, so display-rewrites must be fast/local.)
- *Can hooks inject context into the session?* Yes: `hookSpecificOutput.additionalContext` is supported on SessionStart, SubagentStart, UserPromptSubmit, UserPromptExpansion, PreToolUse, PostToolUse(+Failure/Batch), Stop, SubagentStop, PostModelSwitch. Injected as a system-reminder at the event's position; values >10,000 chars are written to a file and passed as a path+preview. SessionStart additionally accepts `initialUserMessage`, `watchPaths`, `sessionTitle`, `reloadSkills`. Docs advise phrasing injected text as factual statements ("The lexicon version is v12"), not imperative commands, to avoid prompt-injection defenses.

**Other respeak-relevant events:** `SubagentStop` (fire translation when a swarm worker finishes — input mirrors Stop for subagents), `PreCompact`/`PostCompact` (snapshot/re-inject lexicon around compaction), `TaskCompleted` (milestone trigger for auto-narratives), `UserPromptSubmit` (inject lexicon delta each turn), `FileChanged` with a `matcher` on `corpus/lexicon.yaml` (react to ratifications live), `ConfigChange`. Plugin hooks get `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` placeholders and, in exec form, `${user_config.*}` substitution.

## 4. Plugins

Sources: https://code.claude.com/docs/en/plugins.md, https://code.claude.com/docs/en/plugins-reference.md, https://code.claude.com/docs/en/plugin-marketplaces.md. Also inspected a real installed plugin at `~/.claude/plugins/cache/claude-api-agents/claude-api-agents/1.0.0/`.

**Structure:** manifest at `.claude-plugin/plugin.json` (manifest is OPTIONAL — components auto-discovered; name derives from dir name). Component dirs at plugin ROOT (never inside `.claude-plugin/`): `skills/` (preferred), `commands/` ("skills as flat .md files — use skills/ for new plugins"), `agents/`, `hooks/hooks.json`, `.mcp.json`/`mcpServers`, `output-styles/`, LSP servers, experimental `themes/` + `monitors/`. Real-world confirmation: claude-api-agents ships `commands/*.md` with frontmatter `allowed-tools`, `description`, `disable-model-invocation` and a `skills/<name>/SKILL.md` — matching the docs.

**Manifest schema:** only `name` required (kebab-case; used as the namespace prefix `plugin:component`). Optional: `displayName`, `version`, `description`, `author{name,email,url}`, `homepage`, `repository`, `license`, `keywords`, `metadata` (free-form), `defaultEnabled` (default true), component-path overrides (`skills`, `commands`, `agents`, `hooks`, `mcpServers`, `outputStyles`, `lspServers`), `dependencies` (other plugins), **`userConfig`** and `channels`. Unrecognized top-level fields are ignored (warn only in `claude plugin validate`; `--strict` for CI).

**`userConfig` (big for respeak):** declares typed options (`string|number|boolean|directory|file`, `title`, `description`, `default`, `sensitive`, `required`, `multiple`, `min/max`) that Claude Code PROMPTS the user for at enable time — e.g. `default_mode`, `tech_level`, `tone`. Values substitute as `${user_config.KEY}` in MCP/LSP configs and exec-form hook commands, in skill/agent content (non-sensitive), and export to hooks as `CLAUDE_PLUGIN_OPTION_<KEY>`. Stored under `pluginConfigs` in user settings.json only (project settings ignored for security).

**Paths/state:** `${CLAUDE_PLUGIN_ROOT}` (install dir; changes each update), `${CLAUDE_PLUGIN_DATA}` → `~/.claude/plugins/data/<id>/` persistent across updates (right home for the mutable ratified lexicon + proposal queue), `${CLAUDE_PROJECT_DIR}`. Install cache observed at `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`.

**Install flow:** marketplaces are git repos/URLs/paths with `.claude-plugin/marketplace.json`; `claude plugin marketplace add <src>` then `claude plugin install name@marketplace` (user scope default, `--project` for team) or interactive `/plugin`. `claude plugin init` scaffolds; `claude plugin validate` lints; `claude plugin inspect` shows the component inventory AND **projected token cost per session** — use it to keep respeak's passive footprint measured. `/reload-plugins` after mid-session updates.

**Plugin-specific restrictions to remember:** plugin agents don't support `hooks`, `mcpServers`, `permissionMode` frontmatter (security); plugin skills get `/plugin:skill` names; plugin agent with bad/missing frontmatter still loads under its filename.

## 5. Output styles

Source: https://code.claude.com/docs/en/output-styles.md

**Status: feature alive; the `/output-style` COMMAND is dead** (deprecated v2.1.73, removed v2.1.91). Configure via `/config` menu → saved to `.claude/settings.local.json`, or set `"outputStyle": "<Name>"` in any settings file. Built-ins now: Default, Proactive, Concise, Explanatory, Learning. Custom styles are Markdown files with frontmatter (`name`, `description`, `keep-coding-instructions: true|false`) at `~/.claude/output-styles/`, `.claude/output-styles/`, managed dir — and **plugins can ship an `output-styles/` directory**. They modify the SYSTEM PROMPT (read once at session start; changes need `/clear`/restart, and bust the prompt cache).

**respeak fit:** an optional shipped output style ("respeak-shorthand", `keep-coding-instructions: true`) is the strongest lever for making the MAIN session write in ratified shorthand, since it edits the system prompt itself. Downside: user opt-in, session-start-only, one style at a time (conflicts with a user's own style). Treat as an optional add-on, not the core mechanism.

## 6. CLAUDE.md, `.claude/rules/`, and settings.json as lexicon-injection points

Sources: https://code.claude.com/docs/en/memory.md, https://code.claude.com/docs/en/settings.md, https://code.claude.com/docs/en/claude-directory.md

- CLAUDE.md scopes (load order broad→specific): managed policy (`/etc/claude-code/CLAUDE.md` on Linux) → `~/.claude/CLAUDE.md` → `./CLAUDE.md` or `./.claude/CLAUDE.md` → `./CLAUDE.local.md` (gitignored). Loaded at EVERY session start; "context, not enforced configuration". Guidance: <200 lines per file, concrete verifiable rules.
- **`@path/to/import` syntax**: CLAUDE.md can import other files (expanded at launch, 4-hop depth, backticks suppress import). This is the cleanest lexicon injection: project CLAUDE.md carries one line `@corpus/lexicon.yaml` (or a generated `@corpus/lexicon-active.md` digest) so every session — swarm workers included — loads the ratified lexicon. Translator ratification loop = rewrite that digest file; new sessions pick it up (mid-session edits DON'T apply until restart, per prompt-caching doc).
- **`.claude/rules/*.md`**: modular rule files, same priority as `.claude/CLAUDE.md`; support `paths:` frontmatter so a rule loads ONLY when Claude touches matching files. A `rules/shorthand.md` (always-on writing conventions) plus path-scoped rules (e.g. shorthand allowed in `notes/**`, banned in `docs/**`) is a finer-grained lexicon-injection point than one monolithic CLAUDE.md.
- Auto memory: Claude-written, per-repo, first 200 lines/25KB loaded each session — the swarm may organically record shorthand here; the translator can audit it.
- settings.json (user/project/local + managed): carries `hooks`, `statusLine`, `subagentStatusLine`, `outputStyle`, `agent` (default session agent), `enabledPlugins`, `pluginConfigs`, permissions. Note plugins cannot ship CLAUDE.md content directly — lexicon injection from a plugin must go through hooks (`additionalContext`), a SessionStart hook, skills, or by writing to project CLAUDE.md/rules with user consent.

## 7. Statusline customization

Source: https://code.claude.com/docs/en/statusline.md

Settings key `statusLine`: `{"type":"command","command":"<script>","padding":N,"refreshInterval":N,"hideVimModeIndicator":bool}`. Script gets a rich JSON payload on stdin (model, cwd, `workspace.*`, `cost.total_cost_usd`, `context_window.used_percentage`, `effort.level`, `output_style.name`, `session_id`, `session_name`, `transcript_path`, rate limits, prompt-cache stats, version) and prints lines to stdout; ANSI colors + OSC-8 links supported; runs locally, **zero API tokens**; re-runs on each assistant message / compact / permission-mode change, debounced 300ms; `refreshInterval` for idle updates. `/statusline` command (uses a Sonnet `statusline-setup` subagent) configures it conversationally. There is also **`subagentStatusLine`** to custom-render each subagent's row in the agent panel.

**respeak fit:** a statusline script can show `mode:bluf · lexicon:v12 (3 proposals)` by reading `config/respeak.config.yaml` + counting `corpus/proposals/*` — pure local cost. A plugin cannot install a statusline automatically (statusLine is a settings key), so ship the script in the plugin + a skill (`/respeak:statusline`) that offers to write the settings entry.

## 8. Headless mode, Agent SDK, MCP as translator homes

Sources: https://code.claude.com/docs/en/headless.md, https://code.claude.com/docs/en/agent-sdk/overview.md, https://code.claude.com/docs/en/mcp.md

- **`claude -p`**: non-interactive; `--output-format json|stream-json`; `--append-system-prompt` / `--system-prompt`; `--continue`; exit codes for scripting. **`--bare`** skips ALL auto-discovery (hooks, skills, plugins, CLAUDE.md, MCP), reads no OAuth (needs `ANTHROPIC_API_KEY`), and is "the recommended mode for scripted and SDK calls, and will become the default for `-p` in a future release." Bare mode can still load `--plugin-dir <path>`, `--agents <json>`, `--settings`, `--mcp-config`. A Stop-hook translator pipeline = `claude --bare -p --agents '<respeak json>' ...` fed `last_assistant_message` — isolated, deterministic, but a separate billed call per turn and seconds of latency.
- **Agent SDK** (TypeScript/Python, `@anthropic-ai/claude-agent-sdk`): full programmatic loop — subagents, hooks, MCP, structured outputs, session storage. Right home only if respeak grows a standalone service (e.g. an HTTP hook endpoint doing translation); overkill for the plugin itself.
- **MCP server**: a plugin can bundle one (`.mcp.json`/`mcpServers` manifest key). It could expose `translate(text, mode)` and `lexicon_lookup(term)` tools plus MCP resources for the corpus. Cost: tool schemas sit in context; translation quality then depends on the MAIN model doing the rendering unless the server calls out to its own model. Given subagents already give isolation + model choice for free, MCP is only warranted if respeak must serve non-Claude-Code clients too. Hooks can also call MCP tools directly (`type: "mcp_tool"`).

## 9. Audit of the current respeak scaffold vs. docs

Files read: `agents/respeak.md`, `commands/respeak.md`, `skills/respeak/SKILL.md`, `.claude-plugin/plugin.json`.

**`.claude-plugin/plugin.json` — valid.** `name`, `description`, `version`, `author.name` are all recognized fields; `name: respeak` is legal kebab-case. Improvements: add `displayName`, `keywords`, `repository`; add **`userConfig`** for `default_mode` (string, default "bluf"), `tech_level` (number, min/max), `auto_narrative` (boolean) so users configure respeak at enable time instead of hand-editing YAML; values reach hooks as `CLAUDE_PLUGIN_OPTION_*`.

**`agents/respeak.md` — frontmatter valid, three fixes advised.**
1. `tools: Read, Grep, Glob, Write` — all valid names; plugin agents support `tools`. OK.
2. Add `model:` (e.g. `sonnet`) — otherwise it follows the subagent model order and may run on an expensive main-session model for every translation. Optionally `color`, `maxTurns`.
3. **Path bug in body:** the prompt reads `config/respeak.config.yaml` and writes `corpus/proposals/` as cwd-relative paths. That only works when the plugin repo *is* the working project. For an installed plugin, shipped read-only assets must be referenced as `${CLAUDE_PLUGIN_ROOT}/...` (substituted in plugin agent/skill content), and mutable state (proposals, ratified lexicon) must go to `${CLAUDE_PLUGIN_DATA}` (survives updates) or an explicit project-level `.claude/respeak/` — never the plugin root, which changes on every update.
4. Long `description` is legal but counts toward the 15,000-token combined-descriptions warning; current length is fine, keep trigger phrases, trim prose.

**`commands/respeak.md` + `skills/respeak/SKILL.md` — the split is obsolete and self-colliding.**
- Plugin `commands/` is documented as "Skills as flat Markdown files. **Use `skills/` for new plugins**."
- Both files resolve to the same invocation name: `commands/respeak.md` → `/respeak:respeak` and `skills/respeak/SKILL.md` (name: respeak) → `/respeak:respeak`. Two components claiming one name in one plugin.
- The design premise ("/respeak = deterministic path, skill = natural-language fallback") is unnecessary: a single skill is BOTH user-invocable (`/respeak:respeak`) and model-invocable by default. Merge into one `skills/respeak/SKILL.md` carrying the command's `argument-hint`/steps plus the NL trigger phrases in `description`/`when_to_use`.
- Frontmatter fields used (`description`, `argument-hint`, `name`) are all valid skill fields. Consider adding `arguments: [mode, source]` for `$mode`/`$source` substitution, and a `` !`cat ${CLAUDE_PLUGIN_ROOT}/config/respeak.config.yaml` `` dynamic-context block.
- The skill says "delegate to the respeak agent (see agents/respeak.md)" — reference it by its runtime name `respeak:respeak` (plugin-scoped), not by file path.

## 10. Integration-options table

| Surface | Mechanism | When it fires | Context cost (main session) |
|---|---|---|---|
| Plugin subagent `agents/respeak.md` | Auto-delegation by description; `@agent-respeak:respeak`; explicit ask | On delegation | description only (~100–200 tokens passive); transcript stays in subagent window |
| Plugin skill `/respeak:respeak` | User `/…` or model invocation; args + dynamic `!`cmd`` injection | On invocation | description in context always (≤1,536 chars); full body only when invoked, persists (5k/25k compaction budget) |
| Model-only skill (`user-invocable: false`) | NL triggers ("explain to my manager…") in description | Model decides | description always in context |
| User-only skill (`disable-model-invocation: true`) | `/…` only | User types it | ZERO passive cost (description not loaded) |
| Hook: `Stop` (plugin hooks/hooks.json) | command/prompt/agent handler; input has `last_assistant_message` | End of every main-agent turn | none unless it returns `additionalContext`; external `claude -p` call costs $ + latency |
| Hook: `MessageDisplay` → `displayContent` | rewrite displayed text only; transcript/model keep original | While assistant text displays (10s timeout) | zero model-context cost — display-only |
| Hook: `SubagentStop` / `TaskCompleted` | milestone auto-narrative trigger | Worker finishes / task completes | none passive |
| Hook: `SessionStart` / `UserPromptSubmit` `additionalContext` | inject lexicon version/delta as system-reminder | Session start / each prompt | size of injected string (>10k chars auto-spills to file) |
| Hook: `PreCompact`/`PostCompact`, `FileChanged(lexicon.yaml)` | re-inject or react to lexicon state | compaction / file edits | small |
| CLAUDE.md `@import` + `.claude/rules/*.md` | project-level lexicon digest, path-scoped rules | Every session start | full text every session — keep digest <200 lines |
| Output style (plugin `output-styles/`) | system-prompt modification, `keep-coding-instructions: true` | Session start after user opts in via `/config` | in system prompt; cache-busting on change |
| `statusLine` / `subagentStatusLine` settings | shell script over stdin JSON | Each assistant message etc., 300ms debounce | zero tokens (local) |
| `claude -p [--bare]` / Agent SDK | out-of-band translator process | Whenever scripts call it | zero main-session tokens; separate API cost |
| MCP server (plugin-bundled) | `translate`/`lexicon` tools + resources | On tool call | tool schemas always in context |

## 11. Recommended combination

1. **On-demand translation:** one plugin skill `skills/respeak/SKILL.md` (`/respeak:respeak [mode] [source]`, `arguments: [mode, source]`, both user- and model-invocable, NL triggers in `when_to_use`) that delegates to the plugin subagent `respeak:respeak` (`model: sonnet`, tools Read/Grep/Glob/Write). Delete `commands/respeak.md`.
2. **Auto-narrative at milestones:** plugin `hooks/hooks.json` with (a) `Stop` command hook — reads `last_assistant_message`, and when the turn crosses a milestone heuristic (or shorthand density threshold) returns `hookSpecificOutput.additionalContext` asking Claude to append a one-paragraph narrative in the configured mode, gated by `stop_hook_active` to avoid loops; (b) optional `SubagentStop`/`TaskCompleted` variants for swarm workers. For zero-context-cost display translation of shorthand-dense replies, an experimental `MessageDisplay` hook with a fast local `displayContent` rewrite (banned-phrase/lexicon expansion via script, not a model).
3. **Lexicon injection (translator proposes, lexicon disposes):** ratified lexicon rendered to a compact digest `corpus/lexicon-active.md`; injected via project CLAUDE.md `@corpus/lexicon-active.md` import or `.claude/rules/respeak-shorthand.md` (setup performed by a `/respeak:init` user-only skill with user consent, since plugins can't ship CLAUDE.md). Supplement with a `SessionStart` hook injecting `additionalContext`: "The ratified shorthand lexicon is vN; the digest is loaded" — factual phrasing per docs. Proposals live in `${CLAUDE_PLUGIN_DATA}` or project `.claude/respeak/proposals/`.
4. **UX:** statusline script shipped in the plugin (`mode · lexicon vN · proposals pending`), installed by `/respeak:init` writing the `statusLine` settings key; `userConfig` in plugin.json for mode/tech-level defaults; optional shipped output style `respeak-shorthand` (`keep-coding-instructions: true`) for users who want the main swarm lane to write shorthand natively.

## Sources (all fetched this session)

- https://code.claude.com/docs/llms.txt (page index)
- https://code.claude.com/docs/en/overview.md (via redirect from https://docs.claude.com/en/docs/claude-code/overview)
- https://docs.claude.com/llms.txt (confirmed: platform docs only, no Claude Code pages)
- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/skills.md
- https://code.claude.com/docs/en/commands.md
- https://code.claude.com/docs/en/hooks.md
- https://code.claude.com/docs/en/hooks-guide.md (downloaded)
- https://code.claude.com/docs/en/plugins.md (downloaded)
- https://code.claude.com/docs/en/plugins-reference.md
- https://code.claude.com/docs/en/plugin-marketplaces.md (downloaded)
- https://code.claude.com/docs/en/output-styles.md
- https://code.claude.com/docs/en/settings.md (downloaded)
- https://code.claude.com/docs/en/settings-reference.md (downloaded)
- https://code.claude.com/docs/en/statusline.md
- https://code.claude.com/docs/en/memory.md
- https://code.claude.com/docs/en/headless.md
- https://code.claude.com/docs/en/agent-sdk/overview.md
- https://code.claude.com/docs/en/mcp.md (downloaded)
- https://code.claude.com/docs/en/features-overview.md (downloaded)
- https://code.claude.com/docs/en/claude-directory.md (downloaded)
- Local inspection: `~/.claude/plugins/cache/claude-api-agents/claude-api-agents/1.0.0/` (plugin.json, commands/, skills/)
