# Liminal v2 testable vertical slice

Status: **model-connected contract-driven alpha; Pass 2 causal-synthesis revision awaiting human acceptance**.

This directory adds v2 contracts without modifying the frozen v1.1 schema or prompts.

## Implemented through the Phase 4 alpha test gate

- Phase 1 alpha contract:
  - observable symbolic material
  - eight symbolic-transformation types
  - session-level psychological process with sequence, emotional function, adaptive value, and current cost
  - evidence links, alternatives, disconfirming evidence, confidence, and explicit epistemic limits
- Phase 2 testable traditional layer:
  - canonical input is limited to card and orientation
  - situated input is limited to canonical reading and the revealed question
  - situated output supplies only card structure, orientation mechanism, open tension axes,
    and a scope boundary; it cannot pre-answer the question or recommend an intervention
  - all 78 current records are available, but remain marked `provisional_v1_dataset` until Waite-source and human review are complete
- Phase 3 Pass 1 workflow:
  - question-blind request preparation
  - conservative multilingual feature hints
  - provider-neutral prompt rendering
  - structured-output validation
  - deterministic SHA-256 freeze and tamper detection
- Phase 4 question reveal and Pass 2 workflow:
  - explicit question-shift state
  - immutable Pass 1 lineage through its SHA-256 digest
  - isolated situated traditional reading
  - explicit `integrated` / `held` / `not_relevant` mapping for every Pass 1 pattern
  - `integrated` requires at least two evidenced steps in their frozen order; it no longer
    forces every step to match, while theme-only or under-evidenced connections remain `held`
  - an explicit question structure preserves core experience, lived stakes, the user's
    current explanatory frame, contemplated decision, and decisive unknowns
  - one causal process synthesis carries the inherited process's contextual value and cost
    without rendering backend step mappings as prose
  - verbatim reality evidence, including emotional salience and optional action already taken
  - a card-specific perspective shift relocates attention and revises the decision criterion
  - at least two live alternative explanations prevent premature causal closure
  - bounded direction with an uncertainty boundary; only integrated patterns may drive it
  - optional action/reflection used only to learn about a named decisive unknown
  - a takeaway question linked to that unknown without presupposing a solution
  - a writing stage that renders one self-contained reading from a curated narrative brief;
    it receives neither full Pass 1 prose, raw evidence checklists, nor process-step mappings
- Parallel production foundations (not yet active model inputs):
  - a deterministic 78-card RWS knowledge index with per-card Waite text candidates, source links, and review states
  - a prompt-neutral analysis-method specification with a verified source registry, claim-to-source map, controversy boundaries, evaluation design, evidence gates, and false-positive checks
  - a SHA-256 lock for all seven human-approved baseline or revision-candidate prompts
  - automated isolation checks preventing either shadow layer from silently altering current output
- Live model execution:
  - a standard-library DeepSeek adapter using the official OpenAI-compatible endpoint
  - secure ignored `.env.local` configuration with no key in logs or receipts
  - JSON mode, retry handling, requested-versus-served model receipts, and token usage
  - a versioned runtime JSON contract envelope because remote API models cannot open local schema files
  - four-stage Pass 1 and three-stage Pass 2 orchestration with per-stage validation,
    contract-scoped repair, and progress
  - successful synthetic end-to-end smoke run against `deepseek-v4-pro`

No third-party model SDK is required; the adapter uses Python's standard HTTP library.
A first live participant API run accepted Pass 1 but exposed formal rather than semantic
inheritance in Pass 2. A first correction then overconstrained exact step matching and produced
fragmented prose. The current candidate separates backend evidence audit from causal synthesis
and must be rerun against the frozen participant Pass 1 before acceptance.

The automated knowledge-ingestion and method-research passes are complete for this gate. Human field review of card text/images and explicit method activation remain later work. Both layers remain `shadow_read_only` / `shadow_only_not_prompt_input`, so the live model still uses the accepted provisional traditional payload and locked analytical prompts.

## DeepSeek local configuration and live workflow

Copy the variable names from `.env.example` into the ignored `.env.local`; never commit or print the real key. Local participant runs should be written under the ignored `local_runs/` directory. Both the environment file and run files can contain sensitive data.

The selected model is configured through `DEEPSEEK_MODEL=deepseek-v4-pro`. DeepSeek's official documentation states that requests using this name will be routed to V4.1 Flash after 2026-09-14 12:00 Beijing time until a future V4.1 Pro is available. Every call receipt therefore records both `requested_model` and `served_model`.

The structured workflow defaults to `DEEPSEEK_THINKING=disabled`. A live test showed that high reasoning could exhaust the response budget with empty final JSON, while non-thinking mode completed the same four Pass 1 stages in about 30 seconds. The model can still be changed through local environment values without editing code.

Minimal paid connectivity check:

```bash
python -m engine.v2.cli deepseek-smoke
```

Run a real question-blind Pass 1 and write the sensitive result with mode `600`:

```bash
python -m engine.v2.cli run-pass1-model \
  --session-id participant-001 \
  --card "The Hermit" \
  --orientation upright \
  --transcript-file /path/to/private-transcript.txt \
  --output local_runs/participant-001-pass1.json
```

Only after Pass 1 has been shown and frozen, collect the question and run Pass 2:

```bash
python -m engine.v2.cli run-pass2-model \
  --pass1-run local_runs/participant-001-pass1.json \
  --question "The newly revealed question" \
  --question-shift clarified \
  --question-shift-note "Optional note" \
  --output local_runs/participant-001-pass2.json
```

Receipts include hashes, token usage, attempts, finish reason, and requested/served model names. They exclude the API key and hidden model reasoning.

## Prepare a Pass 1 request

```bash
python -m engine.v2.cli prepare-pass1 \
  --session-id test-001 \
  --card "The Moon" \
  --orientation upright \
  --transcript-file /path/to/verbatim-transcript.txt
```

Render Stage 1 with `render-observations` using the same arguments. Then render the remaining stages in order:

```bash
python -m engine.v2.cli render-patterns \
  --request /path/to/request.json \
  --evidence /path/to/evidence-stage.json

python -m engine.v2.cli render-compensation \
  --request /path/to/request.json \
  --evidence /path/to/evidence-stage.json \
  --patterns /path/to/pattern-stage.json

python -m engine.v2.cli render-writing \
  --request /path/to/request.json \
  --evidence /path/to/evidence-stage.json \
  --patterns /path/to/pattern-stage.json \
  --compensation /path/to/compensation-stage.json
```

Use `assemble-pass1` to combine the four stage outputs. This separation prevents canonical card meaning from leaking into evidence extraction and prevents the writing layer from inventing analysis.

After the model returns JSON matching `schemas/pass1_output.schema.json`:

```bash
python -m engine.v2.cli freeze-pass1 \
  --request /path/to/request.json \
  --output /path/to/pass1-output.json
```

## Prepare and run Pass 2

Only after the frozen Pass 1 has been shown, collect the revealed question and its shift status:

```bash
python -m engine.v2.cli prepare-pass2 \
  --frozen-pass1 /path/to/frozen-pass1.json \
  --question "The user's question as revealed" \
  --question-shift clarified \
  --question-shift-note "Optional description of what changed"
```

Render and run the situated traditional prompt first, then the integration and writing prompts:

```bash
python -m engine.v2.cli render-situated --request /path/to/pass2-request.json

python -m engine.v2.cli render-pass2-integration \
  --request /path/to/pass2-request.json \
  --situated /path/to/situated-output.json

python -m engine.v2.cli render-pass2-writing \
  --request /path/to/pass2-request.json \
  --situated /path/to/situated-output.json \
  --integration /path/to/integration-output.json

python -m engine.v2.cli assemble-pass2 \
  --request /path/to/pass2-request.json \
  --situated /path/to/situated-output.json \
  --integration /path/to/integration-output.json \
  --writing /path/to/pass2-writing-output.json
```

## Next human-test gate

Rerun the revised Pass 2 against the already frozen participant Pass 1 and revealed question.
Acceptance requires a coherent causal process rather than element-by-element matching, explicit
coverage of material lived stakes, a genuinely card-specific shift in perspective, multiple live
explanations, and a takeaway question that does not preselect its solution. After this regression
check, use a different card and question for a complete two-pass confirmation run.

Score at least:

- evidence support
- psychological-pattern recognizability
- overreach / forced fit
- whether Pass 1 stands on its own without the question
- Pass 1 → Pass 2 inheritance continuity
- Pass 2 incremental value and answer completeness
- whether practical translation follows from evidence rather than generic advice
- whether emotionally important stakes remain present without being overinterpreted
- whether the perspective shift changes the decision criterion rather than merely adding advice
- whether the takeaway question remains neutral about the method and outcome

Do not commit participant audio, raw transcript, revealed question, or identifiable feedback to a public repository. Store only consented, anonymized research artifacts outside the code repository.
