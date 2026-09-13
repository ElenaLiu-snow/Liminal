# Human-evaluation regressions

This log records anonymized model behaviors that exposed a general contract or workflow
defect. It excludes participant transcripts, revealed questions, identifiable context, and
complete model answers. A regression entry may justify a general implementation change only
when the defect can be stated independently of the case content and protected by tests.

## HE-REG-001 — Formal lineage without process-level inheritance

- Date: 2026-09-12
- Stimulus class: one reversed card; relationship-choice question
- Human scores: Pass 1 → Pass 2 continuity 2–3/5; question completeness 4/5;
  incremental value 4/5; forced fit 0/5; practical help 4/5
- Observed defects:
  - the final rendering copied multiple Pass 1 paragraphs verbatim
  - the integration treated thematic overlap as evidence that the frozen psychological
    process had recurred
  - reality-evidence extraction appeared as a detached restatement of the question
  - the compensation and practical translation defaulted to broadly applicable advice
- General root causes:
  - the writing stage received the full Pass 1 prose and had no repetition gate
  - inheritance validation checked ids and statuses but not frozen sequence steps
  - the compensation layer lacked an explicit bridge from process limit to card
    counterweight to revised decision criterion
- Approved revision:
  - require every evidence-linked frozen process step for `integrated`
  - represent theme-only and insufficient-process matches as `held`
  - prevent held or irrelevant patterns from driving direction or practice
  - replace free compensation prose with a three-part compensation bridge
  - remove full Pass 1 prose from the final writing input and reject copied paragraphs
- Acceptance state: superseded by HE-REG-002 after the first correction exposed a second-order
  fragmentation defect.

## HE-REG-002 — Complete step mapping produced fragmented meaning

- Date: 2026-09-14
- Stimulus class: one reversed card; relationship-compatibility question
- Observed defects:
  - final prose paired separate question fragments with separate card elements instead of
    expressing one causal or meaning-making process
  - an explicitly important emotional stake disappeared because it did not fit a mapping slot
  - emotional intensity was upgraded into an unreported relationship role and stronger affect
  - the card's compensation became generic counselling rather than a distinct shift of viewpoint
  - the takeaway question assumed one intervention was the answer before the decisive unknown
    had been established
- General root causes:
  - complete mapping coverage was used as a proxy for semantic continuity
  - contextual value and cost were stored per pattern rather than synthesized at the whole-process level
  - the writing stage received backend audit mappings as its narrative plan
  - the situated tarot stage generated a direction and reflection question before causal integration,
    seeding a preferred intervention upstream
  - the question had no explicit structure for lived stakes, current frames, contemplated choices,
    or decision-critical unknowns
  - practice and takeaway generation were linked to a recommended method rather than an evidence gap
- Approved revision:
  - preserve ordered step mappings only as hidden audit material; require two supported steps for
    recurrence without forcing every step to match
  - add a reality-question structure and one causal-process synthesis
  - represent emotional salience as a lived stake without assigning a role or pathology
  - replace generic compensation with a card-specific perspective shift and revised decision criterion
  - restrict the situated tarot stage to card structure, orientation mechanism, open tensions,
    and a scope boundary; it must not answer the question or recommend an intervention
  - keep at least two live alternative explanations and state their missing evidence
  - link optional practice and the neutral takeaway question to a named decisive unknown
  - give the writing stage only a curated narrative brief without mappings, evidence ids, or raw quotes
- Acceptance state: implementation candidate; requires model-generated regression review before
  becoming the accepted Pass 2 baseline.
