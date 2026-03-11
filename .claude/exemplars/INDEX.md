# Exemplars & Reference Material

Reference material for academic writing and Claude Code configuration. Skills load these automatically when needed.

## Writing Reference

- **`cochrane_writing_tips.md`** — John Cochrane's "Writing Tips for Ph.D. Students" (2005). The foundational reference for all academic writing rules. Covers organization (triangular style, punchline first), abstracts, introductions, literature reviews, conclusions, writing mechanics (active voice, concision, "clothe the naked this"), tables, figures, and seminar presentations.

## Claude Code Configuration Reference

- **`rules_best_practices.md`** — Best practices for writing `.claude/rules/` files. Covers rule anatomy (frontmatter, body patterns), Do/Don't/Why structure, path scoping, organization patterns, CLAUDE.md vs rules separation, common mistakes, templates for code conventions / security / writing / data rules, and granularity guidelines. Based on Anthropic docs + community patterns.

- **`agents_best_practices.md`** — Best practices for writing `.claude/agents/` files. Covers subagent architecture, frontmatter fields (13 fields), description routing (the sole routing mechanism), tool/permission control, skills loading, worktree isolation, hooks, agent teams (experimental), and a deployment checklist. Based on Anthropic docs.

## How to Use

1. Read `cochrane_writing_tips.md` before writing any paper section
2. The rules in `.claude/rules/academic-writing.md` distill Cochrane + other sources into actionable checks
3. Project-specific exemplars (from your own prior papers or published work you admire) can be added to `projects/<name>/literature/` and referenced in the project's `CLAUDE.md`

## Adding Exemplars

To add new exemplars to this shared directory:
- Source must be from published papers or widely-assigned teaching materials
- Include style notes explaining what works well and why
- Organize by section type (abstract, introduction, results, conclusion, referee reply)
