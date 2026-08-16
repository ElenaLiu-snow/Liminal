# Liminal v2 testable vertical slice

Status: **ready for the next question-blind Pass 1 human test**.

This directory adds v2 contracts without modifying the frozen v1.1 schema or prompts.

## Implemented through the Phase 3 test gate

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

No model SDK is coupled to the engine yet. This is intentional: the prompt can be tested with a chosen model while the input, output, and freeze contracts stay provider-independent.

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

## Human-test gate

The next participant test should use a different card and question from the exploratory sample that shaped the contract. The participant keeps the question private until Pass 1 has been validated, frozen, and shown.

Score at least:

- evidence support
- psychological-pattern recognizability
- overreach / forced fit
- whether Pass 1 stands on its own without the question

Do not commit participant audio, raw transcript, revealed question, or identifiable feedback to a public repository. Store only consented, anonymized research artifacts outside the code repository.
