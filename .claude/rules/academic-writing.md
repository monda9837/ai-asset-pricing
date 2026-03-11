---
description: Academic writing style rules for empirical finance and economics papers
paths:
  - "**/*.tex"
  - "**/*.bib"
---

# Academic Writing Rules — Empirical Finance

## Quick Reference

**First sentence**: Concrete finding, no throat-clearing
**Voice**: Active, present tense for results
**Banned words**: See Section 1
**One-sentence test**: Can you state the paper's contribution in one concrete sentence? If not, restructure. (Cochrane)
**Exemplars**: See `.claude/exemplars/INDEX.md`

> **Project-specific terminology and section constraints belong in each project's `CLAUDE.md`.** This file covers universal writing rules that apply to all empirical finance papers.

---

## 1. Banned Words and Phrases

### Hard Bans (never use)

| Banned | Replacement |
|--------|-------------|
| delve / delve into | examine, investigate, study, analyze |
| crucial | important, central |
| comprehensive | thorough, complete, detailed |
| multifaceted | complex, varied |
| utilize | use |
| leverage (verb for "use") | use, employ |
| facilitate | enable, allow, help |
| endeavor | effort, attempt, work |
| paramount | important, essential |
| myriad | many, numerous, various |
| plethora | many, abundance |
| noteworthy | notable (or just state the fact) |
| it is important to note that | [delete — just state the thing] |
| it should be noted that | [delete] |
| in this regard | [delete or restructure] |
| the fact that | that (or restructure) |
| in order to | to |
| due to the fact that | because |
| a number of | several, many, some |
| the vast majority of | most |
| at the present time | now, currently |
| in the context of | in, for, when |
| with respect to | for, about, regarding |
| in terms of | [restructure sentence] |
| as such | [delete or use "therefore" sparingly] |
| --- (em-dash) in LaTeX | Rewrite: use comma, semicolon, colon, period, or parentheses. Never use `---` in prose. |
| underscores / underscoring | shows, emphasizes, demonstrates (Kobak r=13.8) |
| showcasing / showcase | showing, demonstrating (Kobak r=10.7) |
| pivotal | central, important (Liang top-4 AI marker) |
| intricate | complex, detailed (Kobak +117%) |
| meticulous / meticulously | careful, thorough (Kobak +137%) |
| illuminates / illuminate | reveals, shows, clarifies |
| unveil / unveils / unveiling | show, reveal, document |
| bolster / bolsters | support, strengthen |
| realm | field, area, domain (Liang top-4 AI marker) |
| landscape (metaphorical) | field, literature, area |
| foster | encourage, promote |
| encompass / encompassing | span, cover, include |
| enhancing | improving |
| exhibited | showed, displayed |
| aligns with | is consistent with, matches (IsGPT 16x) |
| Additionally, (sentence opener) | delete, or "also", "X is also Y" |
| in other words | [delete; say it right the first time] (Cochrane: "sign of trouble") |
| of course | [delete] (Nikolov: if obvious, the reader knows) |
| obviously | [delete] (Nikolov) |
| whether or not | whether (Nikolov) |
| aforementioned | [delete; use "this" + noun] (McCloskey Rule 26) |
| it is easy to show that | [delete; just show it] (Cochrane) |
| as we will show / we will show | [delete or give forward ref: Section~X formalizes this] (Cochrane: no previewing) |
| Recall from / Recall that | [restructure; restate the fact briefly] (Cochrane: poor organization signal) |
| -- (en-dash) as parenthetical aside | NEVER use `--` for parenthetical insertions or asides in prose. Use comma, colon, semicolon, period, or parentheses instead. `--` is only for number ranges (e.g., 2002--2024) and compound modifiers (e.g., long--short). |
| shed light on | reveal, show, clarify (Kobak AI-corpus marker) |
| profound | deep, large, substantial (Kobak 2025) |
| grappling | addressing, confronting (Kobak + Liang AI marker) |
| commendable | [delete or be specific] (Gray +83%) |
| innovative | new (if truly novel) (Gray +30%, Liang) |
| versatile | flexible, adaptable (Liang AI marker) |
| not only ... but also | [two separate sentences] (AI overuse pattern) |
| in a manner that / in a way that | [state action directly] (verbose padding) |
| it is worth noting that | [delete; state the thing] (throat-clearing variant) |
| it is clear that / it is evident that | [delete; assert directly] (if clear, reader sees it) |
| one can see that | [delete] (passive hedge) |
| provide a foundation for | enable, support (nominalization + AI filler) |
| serves as (connector verb) | "is" (e.g., "is a proxy for") (AI connector) |
| plays a role in | [name the mechanism] (avoids naming cause) |
| stands in contrast to | differs from, contradicts (AI filler) |
| in line with | consistent with, matches (Kobak AI corpus) |
| in turn | [delete; show link directly] (often meaningless) |
| going forward | in future work, or [delete] (business-speak) |
| that said | [delete; use "however" or "but"] (AI filler transition) |
| taken together | [delete; state conclusion directly] (variant of banned "Together...") |
| to be sure | [state qualification directly] (condescending hedge) |
| broadly speaking | [delete or quantify] (hedge + softener) |
| long-standing (intro opener) | [state the question directly] (cliche) |
| open the door to/for | [state what is now possible] (cliche metaphor) |
| reiterating | [delete] (gerund restatement tag) |
| as discussed in section X | [make the point here or use Section~\ref{}] (variant of "Recall from") |
| speaks to | is relevant to, bears on (vague connector) |
| a battery of | [name the specific checks] (cliche, finance-specific) |
| canonical (for data/methodology) | standardized, standard (overly formal register) |

### Soft Bans (max 1-2 per paper)
- significant/significantly (prefer "substantial", "material", "economically meaningful", or give the number)
- novel (prefer "new" or describe what's new)
- robust (fine in "robustness checks" but don't overuse)
- key (often filler)
- critical/critically (prefer "important" or be specific)
- highlights (prefer "shows", "reveals"; max 2 per paper)
- insights (prefer stating what was learned directly; max 1 per paper)
- compelling (prefer "strong" or just present the evidence)
- ultimately (often filler; delete or restructure)
- somewhat (delete or give the magnitude: "somewhat larger" -> "12bp larger") (Nikolov/Sword)
- quite (delete or quantify) (Nikolov)
- very (as intensifier; delete: "very few" -> "few") (Nikolov: "very often very unnecessary")
- rather (as hedge, not in "rather than") (Nikolov)
- arguably (delete; present evidence instead) (Nikolov)
- perhaps (delete or present evidence) (Nikolov)
- especially (replace with number: "especially large" -> "140 basis points") (Nikolov)
- particularly (same as above; replace with number)
- a variety of (name the types)
- the extent to which (restructure to state the result)
- in general (delete or quantify the exception)
- Indeed, (as sentence opener; AI amplifier; delete)
- as noted above (restructure; variant of "Recall from")

### Structural AI Tells to Avoid
- "Together, these results..." as a paragraph opener (max 1 per paper; vary with "Collectively," or restructure)
- "This finding" as sentence opener (max 1 per paper; vary: "The result", "The evidence", name the specific finding)
- "In this section, we..." throat-clearing (just start with the content)
- Naked "this" without a noun ("This implies..." -> "This result implies...")
- "Importantly," / "Notably," / "Specifically," as sentence-opening adverbs (delete or fold into the sentence)
- "Overall," as a paragraph opener (restructure)
- Uniform paragraph length (vary: some 2-sentence, some 6-sentence)
- Consecutive same-structure paragraph openers: No two consecutive paragraphs begin with the same grammatical construction (e.g., two adverb-comma openers, two "The..." openers). Vary: subject-verb, prepositional phrase, dependent clause. (GPTZero burstiness metric)
- Content-free meta-announcements: Delete any sentence that announces the next topic without providing content. "We now turn to X" -> just start with the finding. Exception: one orienting sentence at section start if it names the specific question. (Cochrane)
- "First...Second" enumeration overuse: Limit parallel enumeration to genuinely parallel, discrete items. For causal chains, use prose. Max one "First...Second" structure per subsection.
- Closing-summary paragraphs within sections: Do not end a section with a paragraph that merely restates. Each paragraph must advance the argument. Summary belongs in Conclusion only.
- Symmetric hedges when data exist: Replace "can be positive or negative, depending on..." with the empirical answer when you have data.
- Gerund-phrase opener density: Max one gerund-phrase opener ("Using a large dataset, we...") per paragraph. High density is a syntactic AI tell. (Burstiness research)
- Padding appositives: Define a concept once. After definition, use the name without appositives restating the definition.
- Sentence length variation: Mix short declarative sentences (8-12 words) with longer compounds (25-40 words). Five consecutive sentences of similar length is an AI tell. (GPTZero/Turnitin burstiness; Kobak 2025)
- Intensive reflexive pronouns as emphasis ("itself", "themselves"): When the pronoun adds emphasis but no semantic distinction, delete it. Max 2 uses of "itself/themselves" per paper, each earning its place.

### Never Stack Superlatives
Bad: "These results provide crucial new insights into this important phenomenon."
Good: "These results show that X."

---

## 2. Writing Principles (Cochrane)

### Punchline First
State the central contribution in paragraph 1. The reader should know your main finding by end of page 1.

### Bad Openings (never use)
- "The literature has long..."
- "Financial economists have wondered..."
- "An important question in finance is..."
- "Asset pricing research stands at a critical juncture..."
- "Recent years have witnessed growing attention to..."
- "A growing body of literature has examined..."

### Good Openings (direct, concrete)
- "Value strategies earn 0.8% per month in gross returns but only 0.3% after transaction costs."
- "Nearly 70% of corporate bonds trade on ten or fewer days per year."
- "The CAPM beta premium is zero in the post-1963 sample."

### Voice and Tense
- **Active voice**: "We show that" not "it is shown that"
- **Present tense for results**: "Table 3 shows..." not "Table 3 will show..."
- "We" is preferred over passive constructions

### Concision
- Every sentence must earn its place
- No repetition -- say it once, say it right
- "In other words" signals you should say it better the first time

### No Previewing or Recalling (Cochrane)
- "As we show below" / "we will show" / "Recall from Section 2" signals poor organization
- Either put the information where it belongs, or give a forward reference: "Section~\ref{sec:model} formalizes this"
- Exception: a single forward reference in the introduction to a later section is fine

### Adjectives
- Do not praise your own work: "striking results", "important contribution"
- Let results speak. If they're striking, readers will notice.

### Sentence Structure
- Subject-verb-object: clear, direct sentences
- Clothe the naked "this": always follow "this" with a noun ("This regression..." not "This shows...")
- Simple short words over fancy ones: "use" not "utilize", "several" not "diverse"

### Kill Hedge Words (Nikolov, Sword)
- Delete: somewhat, rather, quite, very, arguably, perhaps
- If uncertain, give the magnitude: "somewhat larger" -> "12 basis points larger"
- If truly uncertain, say so directly: "we cannot rule out X" rather than hedging with adverbs

### Prefer Verbs over Nominalizations (Williams, Sword)
- "conduct an analysis of" -> "analyze"
- "implementation of the procedure" -> "implementing the procedure"
- "provide evidence that" -> "show that" or "document that"
- Nominalizations (-tion, -ment, -ness) bury the action; strong verbs expose it

### Old Information First, New Last (Pinker, Williams, McCloskey Rule 17)
- Start each sentence with what the reader already knows
- End with the new or complex information
- Chain sentences: the end of sentence A introduces what begins sentence B (AB-BC-CD cohesion)

---

## 3. Handling Uncertainty

- **Factual claims**: Make your best attempt. Flag with `[HUMAN EDIT REQUIRED: verify claim about X]`
- **Technical details**: Be precise. If unsure: `[HUMAN EDIT REQUIRED: verify equation/definition]`
- **Stylistic choices**: Default to this document. When ambiguous: `[HUMAN EDIT REQUIRED: style choice]`

---

## 4. Pre-Finalization Checklist

- [ ] No banned words (Section 1)
- [ ] No em-dashes (`---`) in prose
- [ ] No en-dashes (`--`) used as parenthetical asides (only for ranges and compound modifiers)
- [ ] No AI-marker words (Kobak/Liang list in Section 1)
- [ ] No structural AI tells (Section 1: consecutive openers, meta-announcements, closing summaries, sentence length uniformity, gerund density, intensive reflexives)
- [ ] No hedge words (kill: somewhat, rather, quite, very, arguably, perhaps, especially, particularly)
- [ ] Soft-ban counts within limits (significant max 2, highlights max 2, insights max 1)
- [ ] First sentence is concrete, not throat-clearing
- [ ] Active voice throughout
- [ ] No stacked superlatives
- [ ] Specific numbers for quantitative claims
- [ ] Project-specific terminology consistent (check project's `CLAUDE.md`)
- [ ] Prefer verbs over nominalizations: "conduct an analysis" -> "analyze", "provide evidence" -> "show"
- [ ] Citations verified against `.bib` file (see `.claude/rules/latex-citations.md`)
- [ ] Every table and figure referenced in text
- [ ] Flagged uncertain claims with `[HUMAN EDIT REQUIRED: ...]`
- [ ] No editorial artifacts in prose: `[HUMAN EDIT REQUIRED]`, `TODO`, `FIXME`, `(change to...)`, `[TBD]`, `[PLACEHOLDER]`, `[??]`

---

## 5. Referee Reply Guidelines

These rules apply when writing response letters to referee reports (see also `.claude/skills/respond-to-referee/SKILL.md`).

### Tone
- **Grateful but not obsequious**: "We thank the referee for this suggestion" -- never "We are deeply grateful for this invaluable insight"
- **Accept blame for misunderstandings**: If the referee misread, it is our exposition failure: "We realize our original text was ambiguous and have revised it as follows..."
- **Never dismissive**: No bare "we respectfully disagree." Every disagreement requires evidence, data, or a reference.
- **Direct answers first**: Open each response with what you did, then explain why.

### Structure
- Respond to **every** point. Ignoring any comment signals carelessness.
- **Quote revised text** in the letter (using `\begin{quote}\small ... \end{quote}`) so the referee can verify changes without hunting through the manuscript.
- Reference changes by **section name**, not page numbers (which shift).
- Group related points when they address the same underlying issue.

### Substance
- **Do what the referee asks**, even if you disagree. Run the analysis, report results in the letter, then explain why the manuscript differs.
- **Don't over-revise**: Restrict changes to what is requested. Unrequested dramatic changes create new attack surface.
- **Address general criticisms globally**: If the referee cites two examples of a problem, fix the problem paper-wide.

### Phrases to Use / Avoid

| Use | Avoid |
|-----|-------|
| "Thank you for raising this point" | "We are deeply grateful for this invaluable comment" |
| "The referee is correct that..." | "The referee failed to notice..." |
| "We realize our original text was ambiguous" | "The referee misunderstood" |
| "We have added clarifying language to Section X" | "See page 17" |
| "We maintain X because [evidence]" | "We respectfully disagree" (bare) |

---

## 6. Example Transformations

### Throat-clearing opener to concrete opening

**Bad:**
> "A growing body of literature has studied momentum strategies. Typically, researchers evaluate proposed strategies using historical data, assuming that the representative investor can trade instantaneously, without delay."

**Good:**
> "Momentum profits fall by half after accounting for realistic trading delays and transaction costs."

---

### Vague quantitative claim to precise

**Bad:**
> "The impact of transaction costs is greatest for the most profitable strategies."

**Good:**
> "Momentum strategies face transaction costs of 0.22% per month, more than half of their 0.43% gross alpha, because signals based on past returns decay while investors rebalance."

---

### Self-praising to concrete numbers

**Bad:**
> "Our comprehensive analysis reveals striking results about the importance of accounting for execution costs."

**Good:**
> "Nine ML models generate average CAPM alpha of 0.82% per month before costs. After trading costs, alpha falls to 0.33% for institutional-size trades."

---

## 7. Sources

These rules draw on:

- **Cochrane, J.** (2005). "Writing Tips for Ph.D. Students." Widely assigned in finance PhD programs. See `.claude/exemplars/cochrane_writing_tips.md`.
- **McCloskey, D.** (2019). *Economical Writing*, 3rd ed. The classic on economics prose style.
- **Nikolov, B.** Style rules referenced throughout. Hedge words, concision.
- **Sword, H.** *Stylish Academic Writing*. Nominalization avoidance, sentence variation.
- **Williams, J.** *Style: Lessons in Clarity and Grace*. Old-before-new, verb-driven prose.
- **Pinker, S.** *The Sense of Style*. Information flow, cohesion.
- **Kobak, D. et al.** (2025). "Excess use of certain words in scientific papers published after ChatGPT." *Science Advances*. Statistical validation of AI-marker words (454 excess words in 2024; 10-13.5% of biomedical abstracts LLM-processed).
- **Gray, A.** (2024). "ChatGPT contamination: estimating the prevalence of LLMs in the scholarly literature." arXiv:2403.16887. Frequency spikes: "intricate" +117%, "meticulously" +137%, "delve" ~12x.
- **Liang, W. et al.** (2024). *Nature Human Behaviour*. 22.5% of CS papers show AI modification. "Meticulous" 35x increase in peer reviews. Top markers: showcasing, pivotal, grappling, innovative, versatile.
