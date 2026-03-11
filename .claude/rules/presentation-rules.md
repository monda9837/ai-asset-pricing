---
description: Rules for creating academic seminar and conference presentations
paths:
  - "**/*.tex"
---

# Presentation Rules

Rules for creating academic seminar and conference presentations. Based on the Rhetoric of Decks framework, tailored for empirical finance.

---

## The Three Laws

### Law 1: Beauty Is Function
- Every element earns its presence
- Nothing distracts from the point
- The eye knows where to go
- The most beautiful slide may be three words on a blank background

### Law 2: Cognitive Load Is the Enemy
- One idea per slide. ONE. Not a guideline -- the law.
- Too many points = zero points retained
- Dense text = nothing read
- Complex charts = confusion, not insight

### Law 3: The Slide Serves the Spoken Word
- The slide is the visual anchor, not the content itself
- If slides can be understood without you speaking, you wrote a document
- If you must read slides aloud, you failed twice

---

## Titles Are Assertions, Not Labels

| Weak | Strong |
|------|--------|
| "Results" | "Transaction costs eliminate half of momentum alpha" |
| "Literature Review" | "Prior work assumes costless, instantaneous execution" |
| "Data" | "CRSP covers 26,000 stocks over 60 years" |
| "Methodology" | "Double sorts on size and book-to-market isolate the value premium" |
| "Robustness" | "Results survive alternative breakpoints, weighting, and sample periods" |

**Test**: If someone reads only slide titles in sequence, they should understand your argument.

---

## The MB/MC Equivalence

Optimal rhetoric equalizes marginal benefit to marginal cost across all slides:

MB_1/MC_1 = MB_2/MC_2 = ... = MB_n/MC_n

- **Overloaded slides** (MB/MC too low): Text in footer, competing ideas, audience gives up
- **Underloaded slides** (MB/MC too high): Wasted attention, captured but unused

Walk through the deck asking: "If I added one more element, would the benefit justify the cognitive cost?"

---

## The Aristotelian Balance for Finance Seminars

| Mode | Weight | How It Appears |
|------|--------|----------------|
| **Logos** (logic) | 45% | Data, econometrics, formal results, tables |
| **Pathos** (stakes) | 35% | Why the question matters, impact on investors, real-world costs |
| **Ethos** (credibility) | 20% | Reproducibility, acknowledging limitations, data quality |

---

## Visual Style

### Professional Academic Palette

```latex
% Muted, authoritative house palette
\definecolor{navy}{HTML}{1A365D}        % Primary text, headers
\definecolor{darkgray}{HTML}{2D3748}    % Secondary text
\definecolor{crimson}{HTML}{9B2335}     % Emphasis, key results
\definecolor{forest}{HTML}{276749}      % Positive/adjusted values
\definecolor{steel}{HTML}{4A5568}       % Tertiary, captions
\definecolor{warmgray}{HTML}{E2D8CC}    % Background tint (sparingly)
\definecolor{lightgray}{HTML}{F7FAFC}   % Slide background
```

### Beamer Setup

```latex
\documentclass[aspectratio=169,11pt]{beamer}
\usetheme{default}
\usecolortheme{default}

% Strip navigation chrome
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}[frame number]

% Professional frame styling
\setbeamercolor{frametitle}{fg=navy,bg=white}
\setbeamercolor{title}{fg=navy}
\setbeamercolor{normal text}{fg=darkgray}
\setbeamercolor{itemize item}{fg=steel}
\setbeamercolor{alerted text}{fg=crimson}

% Clean typography
\setbeamerfont{frametitle}{series=\bfseries,size=\large}
\setbeamerfont{title}{series=\bfseries,size=\Large}
```

### Custom Commands

```latex
% Highlight a number (crimson, bold)
\newcommand{\emphnum}[1]{{\color{crimson}\textbf{#1}}}

% Positive result (forest green)
\newcommand{\goodnum}[1]{{\color{forest}\textbf{#1}}}

% Full-slide transition
\newcommand{\transitionslide}[1]{
  \begin{frame}[plain]
  \vfill\centering
  {\Large\color{navy}\textbf{#1}}
  \vfill
  \end{frame}
}

% Takeaway box
\newcommand{\takeaway}[1]{
  \begin{center}
  \colorbox{lightgray}{\parbox{0.85\textwidth}{
    \centering\color{navy}\textbf{#1}
  }}
  \end{center}
}
```

### Typography Rules
- Minimum 24pt body (18pt absolute floor)
- Sans-serif only for projection
- Never justify text (ragged right)
- Maximum two fonts (heading + body)

### Data Visualization
- One message per chart
- Remove chartjunk (no 3D, no excessive gridlines)
- Label directly on the chart (no legends requiring eye movement)
- Use `crimson` to highlight the key comparison
- Use `forest` for net/adjusted values vs `crimson` for gross/unadjusted

### Tables in Slides
- Never show a full regression table -- extract the 2-3 rows that matter
- Bold or color the key coefficient
- State the finding in the title, show the evidence in the table
- Use `\alert{}` for the number you want them to see

---

## Narrative Arc

> **Project-specific narrative arcs belong in each project's `CLAUDE.md`.** Below is a generic template for empirical finance talks.

### Act I: The Problem (slides 1-8)
- Title slide
- The hook: one concrete, surprising fact
- What is the question?
- Why should we care? (stakes for investors, researchers, or policymakers)
- Preview of key results

### Act II: The Evidence (slides 9-25)
- Data: scope, source, sample period
- Methodology: the key identification strategy
- Main results: before/after or treatment/control, with assertion titles
- Mechanism: what drives the result?
- Robustness: one summary slide, not ten

### Act III: The Resolution (slides 26-30)
- The main takeaway, stated cleanly
- Implications for practice or future research
- Devil's advocate: strongest objection + response
- The one thing the audience should remember

### Approximate Slide Budget: 30 slides for 45-minute talk

---

## Common Failures in Finance Seminars

1. **Showing full regression tables**: Extract the key rows. Nobody reads a 15-row table in 60 seconds.
2. **"Outline" slides with 8 items**: Three sections maximum, or cut the outline entirely.
3. **Leading with literature**: Lead with the puzzle, not who wrote what.
4. **"Results" as a title**: Say what the result IS.
5. **Cramming robustness**: One summary slide with "Results survive X, Y, Z" beats 10 robustness slides.
6. **Ending with "Questions?"**: End with the one thing they should remember.

---

## The Devil's Advocate Slide

Before your conclusion, present the strongest objection:

**Title**: "The strongest objection: [state it clearly]"

Content:
- The critique, stated fairly and forcefully
- Your response, with evidence
- What residual uncertainty remains (honesty builds ethos)

---

## Working vs. External Decks

| Dimension | External (seminar/conference) | Working (coauthors) |
|-----------|-------------------------------|---------------------|
| Density | Sparse, one idea per slide | Can be more detailed |
| Titles | Assertions only | Can include descriptive titles |
| Tables | Key rows only | Can show full tables |
| Tone | Performative, polished | Documentary, preserves uncertainty |
| Content | 30 slides / 45 min | No limit |
