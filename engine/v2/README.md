# Liminal v2 testable vertical slice

Status: **ready for a full Pass 1 → question reveal → Pass 2 human test**.

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
  - verbatim reality evidence, including optional evidence of action already taken
  - bounded direction with an uncertainty boundary
  - optional action/reflection translation and one takeaway question
  - a writing stage that renders one complete reading without adding analysis

No model SDK is coupled to the engine yet. This is intentional: the prompts can be tested with a chosen model while the input, output, and freeze contracts stay provider-independent.

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

## Human-test gate

The next participant test should run the complete two-pass flow with a different card and question from the exploratory samples. The participant keeps the question private until Pass 1 has been validated, frozen, and shown.

Score at least:

- evidence support
- psychological-pattern recognizability
- overreach / forced fit
- whether Pass 1 stands on its own without the question
- Pass 1 → Pass 2 inheritance continuity
- Pass 2 incremental value and answer completeness
- whether practical translation follows from evidence rather than generic advice

Do not commit participant audio, raw transcript, revealed question, or identifiable feedback to a public repository. Store only consented, anonymized research artifacts outside the code repository.
