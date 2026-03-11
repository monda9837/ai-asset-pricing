# Anthropic Agent Subagents & Teams: Complete Reference

> Condensed from Anthropic's official documentation: Subagents Overview and Agent Teams Guide.

---

## Table of Contents

1. [What Are Subagents?](#1-what-are-subagents)
2. [How Subagents Work](#2-how-subagents-work)
3. [Built-in Subagents](#3-built-in-subagents)
4. [Subagent File Structure](#4-subagent-file-structure)
5. [Scope and Priority](#5-scope-and-priority)
6. [Tool and Permission Control](#6-tool-and-permission-control)
7. [Writing Effective Descriptions](#7-writing-effective-descriptions)
8. [Working With Subagents](#8-working-with-subagents)
9. [Hooks for Subagents](#9-hooks-for-subagents)
10. [Agent Teams (Experimental)](#10-agent-teams-experimental)
11. [Checklist: Before Deploying a Subagent](#11-checklist-before-deploying-a-subagent)

---

## 1. What Are Subagents?

Subagents are specialized AI assistants that run in their **own context window** with a custom system prompt, specific tool access, and independent permissions. When Claude encounters a task matching a subagent's description, it delegates to that subagent, which works independently and returns results.

**Key benefits:**
- **Preserve context** — exploration and implementation stay out of main conversation
- **Enforce constraints** — limit which tools a subagent can use
- **Reuse configurations** — share subagents across projects (user-level) or teams (project-level)
- **Specialize behavior** — focused system prompts for specific domains
- **Control costs** — route tasks to faster, cheaper models like Haiku

**Subagents vs other configuration types:**

| Type | Purpose | Loaded | Scope |
|------|---------|--------|-------|
| **Subagent** | Delegated task execution in isolated context | At session start (metadata only) | Own context window |
| **Skill** | Domain-specific instructions injected into current context | On-demand when triggered | Current conversation |
| **Rule** | Auto-triggered constraints on file edits | When matching file is edited | Current conversation |
| **Hook** | Shell commands on lifecycle events | On specific events | External process |

**Key distinction:** Skills add knowledge to the current context. Subagents run in a **separate** context window — they don't see the parent's conversation history.

---

## 2. How Subagents Work

### Delegation Flow

1. **Session start:** Claude loads all subagent metadata (name + description) — ~100 tokens each
2. **User request:** Claude compares request against all subagent descriptions
3. **Match:** Claude invokes the Agent tool, which spawns the subagent in a new context window
4. **Execution:** Subagent receives ONLY its system prompt (body of .md file) + basic environment info
5. **Return:** Results are summarized back to the main conversation

### Context Isolation

- Subagent receives its system prompt (the body of the `.md` file) and basic environment details (working directory, platform)
- Does **NOT** receive the full Claude Code system prompt
- Does **NOT** inherit parent conversation history
- Skills are **NOT** inherited — must be explicitly configured via the `skills` field
- CLAUDE.md and project context **ARE** available (subagent can read files)

### Nesting Prevention

- Subagents **cannot** spawn other subagents
- The Agent tool is unavailable inside subagents
- Only main-thread agents (`claude --agent`) can spawn subagents with restricted `Agent(worker, researcher)` syntax

---

## 3. Built-in Subagents

Claude Code includes built-in subagents that auto-delegate based on context:

| Name | Model | Tools | Purpose |
|------|-------|-------|---------|
| **Explore** | Haiku | Read-only (Glob, Grep, Read, Bash) | Fast codebase search and file discovery. Three thoroughness levels: quick, medium, very thorough |
| **Plan** | Inherits | Read-only | Research during plan mode. Cannot modify files |
| **General-purpose** | Inherits | All tools | Complex multi-step tasks requiring both exploration and modification |
| **Bash** | Inherits | Terminal only | Running terminal commands in separate context |
| **statusline-setup** | Sonnet | Read, Edit | Configures the status line |
| **Claude Code Guide** | Haiku | Glob, Grep, Read, WebFetch, WebSearch | Answers questions about Claude Code features |

---

## 4. Subagent File Structure

### File Format

Markdown file with YAML frontmatter. Frontmatter = metadata and configuration. Body = the system prompt injected when the subagent is spawned.

### Minimal Example

```markdown
---
name: code-reviewer
description: "Reviews code for quality, security, and best practices. Use after code changes or when explicitly requested."
---

You are a senior code reviewer. Analyze code for:
- Security vulnerabilities
- Performance issues
- Readability and maintainability
```

### All Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | string | Unique identifier. Lowercase letters and hyphens only |
| `description` | Yes | string | When Claude should delegate. **This is the routing mechanism** |
| `tools` | No | CSV | Allowlist of tools. Inherits all if omitted |
| `disallowedTools` | No | CSV | Denylist — removed from inherited/specified tools |
| `model` | No | string | `sonnet`, `opus`, `haiku`, or `inherit` (default) |
| `permissionMode` | No | string | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | No | integer | Maximum agentic turns before stopping |
| `skills` | No | CSV | Skills injected at startup. **Not inherited from parent** |
| `mcpServers` | No | list | MCP servers — name references or inline definitions |
| `hooks` | No | object | Lifecycle hooks scoped to this subagent |
| `memory` | No | string | Persistent memory scope: `user`, `project`, or `local` |
| `background` | No | boolean | `true` to always run as background task |
| `isolation` | No | string | `worktree` for temporary git worktree (auto-cleaned if no changes) |
| `color` | No | string | Background color for UI identification |

### Complete Annotated Example

```markdown
---
name: wrds-data-expert
description: "Use for WRDS database queries covering CRSP, Compustat, and OptionMetrics.

<example>
user: \"Pull monthly returns for S&P 500 stocks.\"
assistant: Uses wrds-data-expert to query CRSP monthly stock file.
<commentary>Filters for common stocks on major exchanges. Uses permno as identifier.</commentary>
</example>

<example>
user: \"Get quarterly earnings data for Apple.\"
assistant: Uses wrds-data-expert to query Compustat fundamentals.
<commentary>Uses gvkey identifier. Applies required Compustat filters: indfmt, datafmt, popsrc, consol.</commentary>
</example>"
tools: Bash, Glob, Grep, Read, Edit, Write
model: inherit
---

You are an expert agent for WRDS database queries via PostgreSQL.

**Before running any psql query, invoke the `wrds-psql` skill.**

## Overview
[Domain-specific knowledge here...]

## Tables
[Schema and table documentation...]

## Example Queries
[Tested query patterns...]

## Gotchas
[Data quality issues, common mistakes...]
```

---

## 5. Scope and Priority

Subagents can be stored in four locations. Higher-priority locations override lower ones when names conflict:

| Priority | Location | Scope | Use Case |
|----------|----------|-------|----------|
| 1 (highest) | `--agents` CLI flag (JSON) | Current session only | Quick testing, CI automation |
| 2 | `.claude/agents/` | Current project | Team-shared, check into version control |
| 3 | `~/.claude/agents/` | All user's projects | Personal cross-project agents |
| 4 (lowest) | Plugin `agents/` directory | Where plugin is enabled | Plugin-provided agents |

**Management:**
- `/agents` command: interactive view, create, edit, delete
- `claude agents`: list all subagents from command line (shows override hierarchy)
- CLI flag format:
```bash
claude --agents '{
  "quick-reviewer": {
    "description": "Fast code review",
    "prompt": "You are a code reviewer...",
    "tools": ["Read", "Grep", "Glob"],
    "model": "haiku"
  }
}'
```

**Loading timing:** Subagents load at session start. Manually created `.md` files need session restart or `/agents` reload.

---

## 6. Tool and Permission Control

### Tool Specification

```yaml
tools: Read, Grep, Glob, Bash           # Allowlist — only these tools available
disallowedTools: Write, Edit             # Denylist — removed from available tools
```

- If `tools` omitted: subagent inherits **all** tools from main conversation
- Both `tools` and `disallowedTools` can be combined
- `Agent(worker, researcher)` syntax restricts which subagent types can be spawned (main-thread agents only)

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Standard permission checking — user prompted for each action |
| `acceptEdits` | Auto-accept file edits, prompt for other actions |
| `dontAsk` | Auto-deny permission prompts (explicitly allowed tools still work) |
| `bypassPermissions` | Skip all permission checks (**use with extreme caution**) |
| `plan` | Read-only exploration mode |

**Inheritance:** Subagents inherit parent's permission context. If parent uses `bypassPermissions`, it takes precedence and **cannot** be overridden by the subagent.

### Skills Loading

```yaml
skills: wrds-psql, factor-construction    # Injected at startup
```

- Skills are **NOT** inherited from parent — must be explicitly listed
- Full skill content is injected when the subagent starts
- Only inject skills the subagent actually needs (context cost)

### MCP Servers

```yaml
mcpServers:
  - perplexity                            # Reference by name (pre-configured)
  - name: custom-server                   # Inline definition
    url: http://localhost:3000
```

---

## 7. Writing Effective Descriptions

### Why Description Matters

The `description` field is the **sole routing mechanism**. Claude reads it at session start to decide when to delegate. A bad description means the agent never gets invoked — even if the body contains perfect domain knowledge.

**Real failure case:** An agent documented JKP (Jensen, Kelly, Pedersen) factor data thoroughly in its body, but the `description` only said "CRSP stock data." Claude never routed JKP queries to it because the description didn't mention JKP, characteristics, or `contrib.global_factor`.

### Best Practices

1. **Include 3-4 `<example>` blocks** with realistic user queries, assistant responses, and `<commentary>` explaining the routing logic
2. **Include ALL key routing keywords** from the body: database names, table names (`contrib.global_factor`), schema names, paper/author names, acronyms
3. **State WHAT + WHEN** — capability and trigger conditions
4. **Add negative routing** if needed: "Do NOT use for X" to prevent false matches
5. **Use "use proactively"** to encourage automatic delegation without explicit user request

### Good vs Bad Descriptions

| Quality | Description | Why |
|---------|-------------|-----|
| **Good** | "Use for JKP (Jensen, Kelly, Pedersen 2023) Global Factor Data on WRDS: 443 pre-computed stock characteristics. Covers contrib.global_factor..." | Names the paper, acronym, table, key features |
| **Good** | "Expert code reviewer. Use proactively after code changes." | Clear trigger with proactive delegation |
| **Bad** | "Handles stock data queries" | Too vague — which database? which tables? |
| **Bad** | "CRSP expert" | Missing table names, key features, example queries |

### The Cross-Referencing Rule

**Every important routing keyword in the body must also appear in the description.**

If the body documents:
- A table name (`contrib.global_factor`) → description must mention it
- An acronym (`JKP`, `CCM`) → description must include it
- A paper/author name (`Jensen, Kelly, Pedersen`) → description must reference it
- Key capabilities (`443 characteristics`, `pre-linked permno`) → description should surface them

This is the single most important rule for preventing routing failures.

---

## 8. Working With Subagents

### Automatic Delegation

Claude delegates automatically based on three factors:
1. Task content matches subagent's `description`
2. Subagent description includes "use proactively" (encourages unsolicited delegation)
3. Current conversation context suggests the subagent is appropriate

### Explicit Invocation

Users can request a specific subagent: "Use the code-reviewer agent to check this file."

### Foreground vs Background

- **Foreground** (default): blocks main conversation until subagent completes. Use when you need results before proceeding
- **Background** (`background: true`): non-blocking. Main conversation continues; results appear when complete. Use for independent tasks

### Worktree Isolation

```yaml
isolation: worktree
```

- Creates a temporary git worktree — subagent gets an isolated copy of the repository
- Auto-cleaned if the subagent makes no changes
- If changes are made, the worktree path and branch are returned in the result
- Useful for exploratory or risky modifications that shouldn't affect the main working tree

### Common Patterns

| Pattern | Description | Tools |
|---------|-------------|-------|
| **Research agent** | Explore codebase, gather information | Read, Grep, Glob (read-only) |
| **Implementation agent** | Modify files, run tests | All tools |
| **Domain expert** | Deep knowledge of a specific database/API | Bash, Read, Write + domain skills |
| **Reviewer** | Analyze code quality, security | Read, Grep, Glob (read-only) |
| **Orchestrator** | Coordinate other agents | Agent, Read, Bash |

---

## 9. Hooks for Subagents

### Subagent-Scoped Hooks

Defined in the subagent's `hooks` field. Run within the subagent's execution context:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo 'Bash command about to run'"
```

### Project-Level Hooks

Defined in `settings.json`. Two lifecycle events with optional matchers:

| Event | Matcher Input | When It Fires |
|-------|---------------|---------------|
| `SubagentStart` | Agent type name | When a subagent begins execution |
| `SubagentStop` | Agent type name | When a subagent completes |

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [
          { "type": "command", "command": "./scripts/setup-db.sh" }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/cleanup.sh" }
        ]
      }
    ]
  }
}
```

Matchers target specific agent types by name. Omit `matcher` to fire for all subagents.

---

## 10. Agent Teams (Experimental)

> Agent teams are experimental and disabled by default. Enable via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` in settings.json or environment.

### Overview

Agent teams coordinate **multiple Claude Code sessions** working in parallel. Unlike subagents (which only report results back to the parent), teammates can communicate directly with each other, share findings, and self-coordinate.

### Architecture

| Component | Role |
|-----------|------|
| **Team lead** | Main session. Creates team, spawns teammates, coordinates work |
| **Teammates** | Separate Claude instances, each working on assigned tasks |
| **Task list** | Shared work items: pending → in_progress → completed. Stored in `~/.claude/tasks/{team-name}/` |
| **Mailbox** | Inter-agent messaging with automatic delivery |

### Subagents vs Agent Teams

| Dimension | Subagents | Agent Teams |
|-----------|-----------|-------------|
| **Context** | Own context; results return to parent | Own context; fully independent sessions |
| **Communication** | Report-back only | Direct teammate-to-teammate messaging |
| **Coordination** | Parent manages all delegation | Shared task list with self-coordination |
| **Best for** | Focused, result-oriented tasks | Complex collaborative work |
| **Token cost** | Lower (results summarized) | Higher (each teammate = full session) |

### Display Modes

- **In-process**: all teammates run in main terminal. Shift+Down to cycle. Works in any terminal
- **Split panes**: each teammate gets dedicated pane. Requires tmux or iTerm2
- Default `"auto"`: split panes if already in tmux, else in-process
- Override via `"teammateMode"` in settings.json or `--teammate-mode` CLI flag

### Task Management

- Three states: **pending** → **in_progress** → **completed**
- Tasks can have dependencies (`block`/`blockedBy`). Completed tasks auto-unblock dependents
- File locking prevents race conditions on simultaneous claims
- Lead assigns explicitly OR teammates self-claim next unblocked task

### Quality Gates

Two hooks for enforcement:
- **`TeammateIdle`**: exit code 2 sends feedback, keeps teammate working
- **`TaskCompleted`**: exit code 2 prevents marking task complete, sends feedback

### Best Practices

- **Team size**: start with 3-5 teammates (balances parallelism with coordination overhead)
- **Task density**: 5-6 tasks per teammate. Too small = overhead; too large = risk of wasted effort
- **Context**: give teammates enough context in spawn prompt (conversation history does NOT carry over)
- **File conflicts**: break work so each teammate owns different files
- **Monitor**: check progress, redirect failing approaches, synthesize findings
- **Start simple**: begin with research/review tasks before parallel implementation

### Known Limitations

1. No session resumption with in-process teammates (`/resume` doesn't restore them)
2. Task status can lag (teammates may not mark tasks complete — check manually)
3. Shutdown can be slow (teammates finish current request/tool call first)
4. One team per session (must clean up before starting a new one)
5. No nested teams (only lead manages teammates)
6. Lead is fixed (cannot transfer leadership)
7. Per-teammate permissions: set at spawn; can change individually after
8. Split panes require tmux or iTerm2 (not VS Code terminal, Windows Terminal, or Ghostty)

---

## 11. Checklist: Before Deploying a Subagent

### Frontmatter

- [ ] `name` is lowercase + hyphens, unique across all agent locations
- [ ] `description` is specific, includes key routing keywords from body
- [ ] `description` includes 3+ `<example>` blocks with realistic user queries
- [ ] `description` states both WHAT the agent does and WHEN to use it
- [ ] `tools` field matches agent's role (read-only agents should deny Write/Edit)
- [ ] `model` explicitly set or `inherit`

### Description Quality

- [ ] Every key domain term from body also appears in description
- [ ] Negative triggers added if needed ("Do NOT use for...")
- [ ] Debug test: ask Claude "when would you use [agent]?" — clear answer from description alone
- [ ] No scope overlap with other agents' descriptions

### Body

- [ ] Opening paragraph matches description scope (same databases, same domain)
- [ ] Structured sections (Overview, Tables/Schema, Connection, Examples, Gotchas)
- [ ] Skill invocation line present when applicable ("Before running any psql query, invoke the `wrds-psql` skill")
- [ ] 2+ example queries/code blocks present and syntactically valid
- [ ] Under 900 lines (prefer under 600)
- [ ] No Windows paths, no verbose fundamentals, no magic numbers

### Ecosystem

- [ ] Listed in project's CLAUDE.md specialist agent section (if applicable)
- [ ] Listed in orchestrator dispatch table (if coordinated with other agents)
- [ ] No overlapping scope with other agents (same tables/schemas not duplicated)
