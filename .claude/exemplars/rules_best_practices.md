# Best Practices for Writing `.claude/rules/` Files

Reference guide for creating effective Claude Code rules. Based on Anthropic documentation, community patterns, and production experience.

**Sources:** Anthropic docs ([memory](https://code.claude.com/docs/en/memory), [skills](https://code.claude.com/docs/en/skills), [best-practices](https://code.claude.com/docs/en/best-practices), [hooks-guide](https://code.claude.com/docs/en/hooks-guide)), community guides (humanlayer.dev, marioottmann.com, builder.io, sabrina.dev, rockcybermusings.com).

---

## 1. What Rules Are (and Are Not)

Rules are **context injected into every session** to guide Claude's reasoning. They are not enforced configuration — they guide, they don't enforce. This distinction matters:

| Mechanism | Purpose | Enforcement |
|-----------|---------|-------------|
| **Rules** | Standing constraints, domain knowledge, conventions | Guidance (Claude weighs against other context) |
| **Skills** | Repeatable workflows invoked with `/skill-name` | Procedural (runs on invocation) |
| **Agents** | Isolated autonomous tasks in separate context | Isolation (shielded from main conversation) |
| **Hooks** | Shell commands triggered by tool-call events | Hard enforcement (blocks/modifies actions) |
| **CLAUDE.md** | Project overview, routing, universal context | Always loaded, brief |
| **Linters/formatters** | Code style (indentation, semicolons) | Tooling (don't duplicate in rules) |

**Key principle:** If a linter/formatter already enforces it, don't write a rule for it. Rules are for the strategic, domain-specific guidance that tools can't capture.

---

## 2. Rule File Anatomy

### Frontmatter

```yaml
---
description: Short keyword-rich description Claude uses to assess relevance
paths:
  - "src/api/**/*.ts"
  - "**/*.sql"
---
```

- **`description`**: Be specific. "Supabase database patterns for authenticated APIs using RLS policies" >> "Development best practices". Keywords matter — Claude matches them to current work.
- **`paths`**: Glob patterns for conditional loading. Rule only loads when Claude works with matching files. Omit for rules that apply everywhere.

### Glob Pattern Reference

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All `.ts` files recursively |
| `src/**/*` | Everything under `src/` |
| `src/*.tsx` | Only files directly in `src/`, not subdirs |
| `**/*.{ts,tsx}` | Both `.ts` and `.tsx` files |
| `migrations/**/*` | Everything under `migrations/` |

### Body Structure

Use one of these proven patterns:

**Pattern A: Quick Reference + Sections** (best for conventions)
```markdown
# Rule Title

## Quick Reference
[3-5 line summary of the most important points]

---

## 1. Topic Area
[Actionable rules with examples]

## 2. Another Topic
[...]
```

**Pattern B: Do / Don't / Why / Refs** (best for security, correctness)
```markdown
# Rule Title

## Topic

**Do**: Use parameterized queries.
```code
const result = await db.query('SELECT * FROM users WHERE id = $1', [id]);
```

**Don't**: Concatenate user input.
```code
const result = await db.query(`SELECT * FROM users WHERE id = '${id}'`);
```

**Why**: SQL injection allows arbitrary data access.

**Refs**: OWASP A03:2021
```

**Pattern C: Table-Driven** (best for banned/preferred patterns)
```markdown
# Rule Title

| Banned | Replacement |
|--------|-------------|
| utilize | use |
| leverage (verb) | use, employ |
```

---

## 3. What Makes a Good Rule

### Do

- **Be specific and actionable.** "Use `booktabs` package: `\toprule`, `\midrule`, `\bottomrule`" >> "Use good table formatting"
- **Include concrete examples.** Show the right pattern, not just describe it.
- **Use path scoping** for rules that only apply to certain file types.
- **Keep each file focused on one coherent topic.** Database rules separate from testing rules.
- **Stay under 200 lines.** Beyond this, adherence to all instructions degrades uniformly.
- **Put the most important rules first.** Front-load what matters most.
- **Use tables for lookup-style rules** (banned words, naming conventions, status codes).

### Don't

- **Don't duplicate what tools enforce.** If Prettier handles indentation, skip it.
- **Don't write procedures.** Step-by-step workflows belong in skills, not rules.
- **Don't write for future scenarios.** Rules for "when we switch to microservices" create noise now.
- **Don't be vague.** "Code Quality" as a rule name is useless.
- **Don't stack unrelated topics.** A design system rule should not also cover testing.
- **Don't exceed 50 instructions total** across all rules + CLAUDE.md. The system prompt already has ~50; each addition reduces reliability across the board.
- **Don't include obvious guidance.** Skip "here's how to import a React component" for senior engineers.

---

## 4. Organization Patterns

### Recommended Directory Structure

```
.claude/
├── rules/
│   ├── design-system.md        # Always loaded (no path filter)
│   ├── security.md             # Always loaded
│   ├── academic-writing.md     # Path-filtered: **/*.tex, **/*.bib
│   ├── database-patterns.md    # Path-filtered: **/*.sql, src/db/**
│   └── testing.md              # Always loaded
├── skills/
│   └── ...                     # Invocable workflows
├── agents/
│   └── ...                     # Isolated autonomous tasks
└── exemplars/
    └── ...                     # Reference material
```

### Organize by Domain, Not File Type

Think in terms of concerns: "database patterns", "security requirements", "writing style" — not "TypeScript rules", "SQL rules".

### Progressive Disclosure

Only load rules when they're relevant:
- **Always loaded**: Security, project conventions, testing philosophy
- **Path-scoped**: Database patterns (only for `*.sql`), LaTeX conventions (only for `*.tex`), API standards (only for `src/api/**`)

This conserves context tokens — database guidance doesn't load when editing React components.

---

## 5. CLAUDE.md vs Rules: What Goes Where

### CLAUDE.md (small, stable, always loaded)

- Project purpose and scope (2-3 sentences)
- Tech stack summary
- Quick commands (`npm run dev`, `psql service=wrds`)
- Index of available rules, skills, agents
- Pointers to detailed guidance

**Target: 50-100 lines for the "routing" section.** CLAUDE.md can be longer if it contains essential universal context (like data output conventions), but the routing/overview part should be concise.

### Rules (focused, conditional, detailed)

- Domain-specific conventions with examples
- Banned/preferred patterns with alternatives
- Architecture constraints for specific code areas
- Security requirements with Do/Don't/Why
- Reference material Claude consults during work

**Target: Under 200 lines per file.**

### Neither (belongs elsewhere)

| Content | Where It Belongs |
|---------|-----------------|
| Step-by-step procedures | Skills (`/skill-name`) |
| One-time setup instructions | Onboarding skill or README |
| Project-specific terminology | Project-level `CLAUDE.md` |
| Exploratory notes | `_misc/` or project `guidance/` |

---

## 6. Common Mistakes

### The Bloated File
**Problem:** Rule starts focused, grows to 500+ lines covering everything.
**Fix:** Split into multiple focused files. Ruthlessly prune.

### Procedures in Rules
**Problem:** "Step 1: Create migration. Step 2: Run migration. Step 3: ..."
**Fix:** Move to a skill. Rules state constraints ("every table must have `created_at`"), skills describe procedures.

### No Path Scoping
**Problem:** Database patterns load when editing frontend code.
**Fix:** Add `paths: ["**/*.sql", "src/db/**/*"]` to frontmatter.

### Duplicated Guidance
**Problem:** Same instruction in CLAUDE.md and a rule file.
**Fix:** Put it in one place. CLAUDE.md for overview/routing, rules for details.

### Too Generic
**Problem:** Rule titled "Development Standards" with description "Best practices for development."
**Fix:** "React Component Patterns for Authenticated Dashboards Using Supabase" — specific enough that Claude knows when to apply it.

### Linter Duplication
**Problem:** Rule says "use 2-space indentation and semicolons."
**Fix:** Delete the rule. Let Prettier/ESLint handle it. Use hooks to auto-run formatters.

---

## 7. Templates

### Template: Code Convention Rule

```yaml
---
description: [Language/framework] coding patterns for [specific domain]
paths:
  - "src/[domain]/**/*.[ext]"
---

# [Domain] Coding Standards

## Quick Reference
- [Most important convention]
- [Second most important]
- [Third]

---

## Naming
[Table or list of naming conventions]

## Patterns
[Code examples of preferred patterns]

## Anti-Patterns
[Code examples of what to avoid, with explanation]

## Examples
See `src/[domain]/[example_file]` for reference implementation.
```

### Template: Security Rule

```yaml
---
description: Security requirements for [specific area]
---

# Security Standards

## [Vulnerability Category]

**Do**: [Secure pattern with code example]

**Don't**: [Vulnerable pattern with code example]

**Why**: [Attack vector explanation]

**Refs**: [Standard reference]

## [Next Category]
...
```

### Template: Writing/Style Rule

```yaml
---
description: [Writing domain] style rules for [document type]
paths:
  - "**/*.[ext]"
---

# [Domain] Writing Rules

## Quick Reference
[3-5 line summary]

---

## 1. Banned Patterns
| Banned | Replacement |
|--------|-------------|
| ... | ... |

## 2. Required Patterns
[Positive examples of what to do]

## 3. Examples
### Bad
> [Example of what not to write]

### Good
> [Example of what to write instead]

## 4. Checklist
- [ ] [Verification item]
- [ ] [Verification item]
```

### Template: Data/Schema Rule

```yaml
---
description: [Database] schema conventions and query patterns
paths:
  - "**/*.sql"
  - "src/db/**/*"
  - "migrations/**/*"
---

# Database Standards

## Schema Conventions
[Table naming, column naming, required columns]

## Constraints
[Primary keys, foreign keys, indexes]

## Query Patterns
[Preferred query structures with examples]

## Performance
[Indexing, query optimization guidelines]

## Common Gotchas
[Things that silently break or produce wrong results]
```

---

## 8. Granularity: Many Small Files > Few Large Files

**Many focused files win** because:
1. **Path scoping**: Small files can target specific file types, loading only when relevant.
2. **Maintainability**: Updating database conventions means editing one file, not hunting through a monolith.
3. **Discoverability**: Descriptive filenames communicate what rules exist at a glance.
4. **Context efficiency**: Only relevant guidance consumes tokens in any given session.

**Splitting threshold:** If a rule file exceeds 200 lines, split it. A project with 15-20 focused rule files is better than 2-3 monoliths.

**Exception:** A rule with deep internal cross-references (like `academic-writing.md` where banned words, principles, and checklist are tightly coupled) can be longer if splitting would break coherence.

---

## 9. Advanced Patterns

### Hooks as Enforcement Complement
Rules guide; hooks enforce. Use together:
- **Rule**: "All tables must use `booktabs` package"
- **Hook**: PostToolUse hook that runs a linter checking for `\hline` usage

### Pointers Instead of Copies
Keep rules small by pointing to real code:
```markdown
## API Response Format
See `src/api/endpoints/users.ts` for the canonical response pattern.
```
Claude reads the file when needed. Avoids maintaining duplicate examples that drift from reality.

### Progressive Context Loading
```
CLAUDE.md          → Always loaded (overview, routing)
  └── rules/       → Conditionally loaded (path-scoped domain guidance)
      └── skills/  → On-demand (invoked explicitly for workflows)
```

Each layer adds context only when needed.

---

## 10. Checklist: Before Committing a New Rule

- [ ] **Focused**: Covers one coherent topic
- [ ] **Under 200 lines**: Split if longer
- [ ] **Has frontmatter**: `description` is specific and keyword-rich
- [ ] **Path-scoped** (if not universally applicable)
- [ ] **Actionable**: Contains concrete examples, not just abstract principles
- [ ] **Not duplicated**: Doesn't repeat CLAUDE.md or another rule
- [ ] **Not a procedure**: Workflows belong in skills
- [ ] **Not tool-enforceable**: Linter/formatter rules don't need to be here
- [ ] **Front-loaded**: Most important content comes first
- [ ] **Has examples**: Shows the right pattern, not just describes it
