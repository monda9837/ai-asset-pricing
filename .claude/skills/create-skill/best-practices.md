# Skill Authoring: Constraints & Validation Checklist

> Condensed from Anthropic's official documentation. This is the canonical reference for Phase 5 validation in `/create-skill`.

## Table of Contents

1. [Frontmatter Constraints](#frontmatter-constraints)
2. [Body Constraints](#body-constraints)
3. [Naming Guide](#naming-guide)
4. [Description Writing](#description-writing)
5. [Conciseness Rules](#conciseness-rules)
6. [Progressive Disclosure](#progressive-disclosure)
7. [Degrees of Freedom](#degrees-of-freedom)
8. [Anti-Patterns](#anti-patterns)
9. [Troubleshooting](#troubleshooting)
10. [Complete Validation Checklist](#complete-validation-checklist)

---

## Frontmatter Constraints

### Required fields

**`name`** (skills only — rules do NOT have this field):
- Max 64 characters
- Lowercase letters, numbers, and hyphens only: `^[a-z][a-z0-9-]{0,63}$`
- Cannot contain "anthropic" or "claude" (reserved)
- Cannot contain XML tags

**`description`** (all types):
- Non-empty, max 1024 characters
- Cannot contain XML angle brackets (`< >`)
- Must state WHAT the skill does AND WHEN to use it
- Always written in third person (injected into system prompt)

### Optional fields (skills)

- `argument-hint`: Shows expected argument format in slash-command UI
- `license`: License identifier (e.g., `MIT`)
- `allowed-tools`: Restrict tool access (e.g., `"Bash(python:*), WebFetch"`)
- `metadata`: Custom fields — `author`, `version`, `category`, `tags`

### Rule-specific fields

- `paths`: List of glob patterns that trigger the rule (e.g., `"**/*.tex"`)
- Rules have `description` + `paths`, but NO `name` field

## Body Constraints

- **Max 500 lines** for SKILL.md body. Split excess to separate reference files.
- **Progressive disclosure**: 3 levels (metadata → body → linked files)
- Reference files must be **ONE level deep** from SKILL.md — never chain references
- Reference files longer than 100 lines should include a **table of contents**
- Body should be under ~5,000 tokens when loaded

## Naming Guide

### Preferred patterns

Gerund form (verb + -ing):
- `processing-pdfs`, `analyzing-spreadsheets`, `managing-databases`, `building-reports`

Verb-noun also acceptable (matches this project's convention):
- `build-paper`, `write-section`, `create-skill`, `new-project`

### Names to avoid

Generic names that don't convey purpose:
- `helper`, `utils`, `tools`, `misc`, `data`, `documents`, `general`, `common`

## Description Writing

### Format rules

- **Third person**: "Analyzes code for..." not "Analyze code for..."
- **WHAT + WHEN**: State capability AND trigger conditions
- **Under 1024 characters**
- **No XML tags** (`< >`)

### Auto-apply skills

Description must include an "Auto-apply when..." clause:
```yaml
description: "Look-ahead bias prevention and portfolio formation rules. Auto-apply when constructing factors, sorting stocks into portfolios, or computing long-short returns."
```

### Good examples

```yaml
description: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."
```

```yaml
description: "Pre-submission checklist for JF, RFS, JFE, or other target journals"
```

### Bad examples

```yaml
description: "Helps with documents"        # Too vague, no WHEN
description: "Processes data"               # Generic, no trigger phrases
description: "Does stuff with files"        # Useless
```

### Negative triggers

If the skill triggers too often, add exclusions:
```yaml
description: "Advanced statistical analysis for CSV data. Use for regression, clustering, modeling. Do NOT use for simple data exploration (use data-viz skill instead)."
```

### Debug test

Ask Claude: "When would you use the [skill-name] skill?" If the description alone gives a clear answer, it's good. If Claude is confused, revise.

## Conciseness Rules

The context window is a shared resource. Challenge every piece of information:

- "Does Claude really need this explanation?"
- "Can I assume Claude knows this?"
- "Does this paragraph justify its token cost?"

**Good** (~50 tokens — concise with a code example):
```markdown
## Extract PDF text
Use pdfplumber:
\`\`\`python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
\`\`\`
```

**Bad** (~150 tokens — explains what a PDF is):
```markdown
PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available...
```

**Rules of thumb:**
- Assume Claude knows programming, standard libraries, common patterns
- Only add what Claude genuinely lacks: domain rules, project conventions, gotchas
- One concrete example beats three paragraphs of explanation

## Progressive Disclosure

### Three levels

| Level | When loaded | Token cost | Content |
|-------|------------|------------|---------|
| **Metadata** | Always (startup) | ~100 tokens | `name` + `description` from YAML |
| **Instructions** | When triggered | Under 5k tokens | SKILL.md body |
| **Resources** | As needed | Unlimited | Auxiliary files, scripts |

### Patterns

**Pattern 1: High-level guide with references**
```markdown
## Quick start
[Concise example]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md)
**API reference**: See [REFERENCE.md](REFERENCE.md)
```

**Pattern 2: Domain-specific organization**
```
skill-dir/
  SKILL.md (overview + navigation)
  reference/
    topic1.md
    topic2.md
```

**Pattern 3: Conditional routing**
```markdown
**Creating new?** → Follow "Creation workflow" below
**Editing existing?** → Follow "Editing workflow" below
```

### Critical rule

Keep references **one level deep** from SKILL.md. Deeply nested references (file A references file B references file C) cause Claude to partially read files and miss context.

## Degrees of Freedom

Match specificity to the task's fragility:

| Freedom | Style | When to use | Example |
|---------|-------|------------|---------|
| **Low** | Exact scripts, templates | Fragile tasks, errors costly | `wrds-psql` pipeline |
| **Medium** | Checklists, decision tables | Stable structure, variable content | `submission-prep` checks |
| **High** | Principles, examples | Creative/judgment-heavy tasks | `write-section`, `respond-to-referee` |

**Analogy**: Narrow bridge with cliffs → exact instructions. Open field → general direction.

## Anti-Patterns

| Anti-pattern | Why it's bad | Fix |
|-------------|-------------|-----|
| Windows paths (`C:\Users\...`) | Breaks on other platforms | Use forward slashes, `$HOME` |
| Assuming tools installed | Fails silently on different machines | Check availability or reference `CLAUDE.local.md` |
| Deeply nested references | Claude loses context in chains | Keep ONE level deep from SKILL.md |
| Menus without defaults | Claude picks randomly | Provide one default with escape hatch |
| Magic numbers in scripts | No one knows why the value is 30 | Document every constant with justification |
| Verbose fundamentals | Wastes tokens explaining what Claude knows | Cut ruthlessly; one example > three paragraphs |
| Time-sensitive information | Goes stale silently | Use "old patterns" section or avoid entirely |
| Generic naming | Claude can't match skills to requests | Use specific, descriptive names |

## Troubleshooting

### Skill won't upload
- File must be named exactly `SKILL.md` (case-sensitive)
- YAML must have `---` delimiters on their own lines
- Check for unclosed quotes in frontmatter

### Skill doesn't trigger
- Description too generic — add specific trigger phrases
- Missing file type mentions if applicable
- Debug: ask Claude "when would you use [skill]?"

### Skill triggers too often
- Add negative triggers: "Do NOT use for..."
- Narrow scope: "PDF legal documents" not "documents"
- Clarify: "Use specifically for X, not for general Y"

### Instructions not followed
- Too verbose — use bullet points, move details to separate files
- Critical info buried — put key instructions at top, use `## Critical` headers
- Ambiguous — replace "validate properly" with explicit checklists
- For critical validations, use bundled scripts (code is deterministic)

### Context bloat / slow responses
- SKILL.md too large — move reference data to auxiliary files
- Too many skills enabled (20-50+) — Claude struggles to select
- All content inline instead of progressive disclosure

---

## Complete Validation Checklist

Use this checklist for Phase 5 validation. Every item must pass.

### Frontmatter

- [ ] `name` matches `^[a-z][a-z0-9-]{0,63}$` (skills only; rules have no name)
- [ ] No "anthropic" or "claude" in name
- [ ] `description` is non-empty and under 1024 characters
- [ ] `description` contains no XML angle brackets
- [ ] `description` is in third person
- [ ] `description` states both WHAT the skill does and WHEN to use it
- [ ] Auto-apply skills: description includes "Auto-apply when..." clause
- [ ] Rules: `paths` field present with valid glob patterns; no `name` field
- [ ] `argument-hint` present only if skill accepts arguments

### Body

- [ ] Total line count under 500
- [ ] No Windows-style paths (all forward slashes)
- [ ] No assumptions about tools being installed
- [ ] No menus of options without a clear default
- [ ] Every paragraph earns its token cost
- [ ] H1 heading matches the skill purpose
- [ ] `## Examples` section present (user-invocable skills)
- [ ] `## Output` section present (if skill produces reports)

### Anti-patterns

- [ ] No deeply nested references (max 1 level from SKILL.md)
- [ ] No generic naming (helper, utils, misc, etc.)
- [ ] No verbose explanations of fundamentals Claude already knows
- [ ] No time-sensitive information without deprecation markers
- [ ] No magic numbers in code blocks
- [ ] Description passes debug test: clear answer to "when would you use [skill]?"
