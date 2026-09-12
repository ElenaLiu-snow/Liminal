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
- Acceptance state: implementation candidate; requires a new model-generated Pass 2 human
  review before it becomes the accepted output baseline.
