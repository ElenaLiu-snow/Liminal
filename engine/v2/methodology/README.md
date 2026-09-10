# Analysis method layer

`analysis_method.json` expresses the reasoning policy outside the model prompts. It defines:

- an epistemic ladder from observation to bounded hypothesis
- the same eight symbolic transformations enforced by runtime contracts
- minimum evidence and common false positives for each transformation
- a session-pattern gate emphasizing sequence, adaptive value, possible cost, alternatives, and disconfirming evidence
- Pass 2 inheritance and reality-evidence rules
- explicit prohibitions against trait, developmental-origin, trauma-source, and diagnostic claims from one reading
- a separation between historical interpretive theory, empirical risk evidence, qualitative-method guidance, and product engineering choices
- exploratory versus confirmatory human-evaluation rules
- non-clinical positioning and minimum safety requirements

The research layer is split into auditable files:

- `source_registry.json`: verified bibliographic records, review level, supported uses, and explicit non-supported uses
- `method_evidence_map.json`: claim-to-source mapping, evidence status, resulting product rule, and what the claim does not establish
- `research_notes.md`: Chinese synthesis, controversy log, and implications for the next human study

Its current status is `shadow_only_not_prompt_input`. This is intentional. The method can be reviewed and tested now, but it cannot influence generated answers until an explicit integration change updates both the runtime and the locked prompt baseline.

This separation supports independent iteration:

- knowledge changes describe the card
- method changes describe valid reasoning
- prompt changes control model instructions and wording
- human tests determine whether an activated combination is useful

No participant transcript, question, card-specific answer, or desired conclusion is encoded in the method specification.

The registry intentionally retains disagreements. In particular, the critical review of projective techniques and a published counterargument are both represented. The conservative Liminal boundary does not depend on pretending this field is unanimous.
