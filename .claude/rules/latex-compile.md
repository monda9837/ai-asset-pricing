---
description: Always compile LaTeX after editing .tex files
paths:
  - "**/*.tex"
---

# LaTeX Compilation Rule

**After every edit to a .tex file, compile the document immediately.** Do not wait for the user to ask. This is mandatory.

## How to Compile

### Paper main file
```bash
cd {latex_dir} && pdflatex -interaction=nonstopmode {file} && bibtex {stem} && pdflatex -interaction=nonstopmode {file} && pdflatex -interaction=nonstopmode {file}
```

### Standalone files
Use the standalone wrapper if one exists (it contains the preamble and bibliography). Compile from the directory containing the file:
```bash
cd {dir} && pdflatex -interaction=nonstopmode {file}.tex && bibtex {stem} && pdflatex -interaction=nonstopmode {file}.tex && pdflatex -interaction=nonstopmode {file}.tex
```

### Beamer presentations
```bash
cd {dir} && pdflatex -interaction=nonstopmode {file}.tex && pdflatex -interaction=nonstopmode {file}.tex
```

## Important
- Use the pdflatex/bibtex paths from canonical local state reported by `tools/bootstrap.py audit` (or a repo-root `CLAUDE.local.md` compatibility shim if present)
- Check for compilation errors in the output. Report any errors to the user.
- If compilation fails, diagnose and fix before proceeding.
- A successful compile does NOT require zero warnings, only zero errors and "Output written" in the log.
